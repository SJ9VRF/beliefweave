from __future__ import annotations
from pathlib import Path
import hmac
from typing import Optional
from importlib.metadata import PackageNotFoundError, version as package_version
import os, tempfile
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from pwm.engine import (
    IdempotencyConflictError,
    IdempotencyTombstonedError,
    MemoryStateConflictError,
    PersonalMemoryEngine,
)
from pwm.temporal import TemporalValueError

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get('PWM_DEMO_DB', str(Path(tempfile.gettempdir()) / f'pwm-demo-{os.getpid()}.db')))
engine = PersonalMemoryEngine(
    DB,
    enable_ml=os.environ.get('BELIEFWEAVE_DEMO_ENABLE_ML', '').lower() in {'1', 'true', 'yes'},
)
try:
    APP_VERSION = package_version('beliefweave')
except PackageNotFoundError:
    APP_VERSION = 'source'
app = FastAPI(title='BeliefWeave Demo', version=APP_VERSION)


def _custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description=(
            "Reference BeliefWeave demo API. Remote /api/* access requires "
            "BELIEFWEAVE_DEMO_TOKEN via Bearer auth or X-API-Key; localhost-only "
            "development is allowed without a token."
        ),
    )
    components = schema.setdefault("components", {}).setdefault("securitySchemes", {})
    components["BearerAuth"] = {"type": "http", "scheme": "bearer"}
    components["DemoApiKey"] = {"type": "apiKey", "in": "header", "name": "X-API-Key"}
    for path, operations in schema.get("paths", {}).items():
        if not path.startswith("/api/"):
            continue
        for operation in operations.values():
            if isinstance(operation, dict):
                operation["security"] = [{"BearerAuth": []}, {"DemoApiKey": []}]
                operation["x-beliefweave-localhost-bypass"] = True
    app.openapi_schema = schema
    return schema


app.openapi = _custom_openapi


def _demo_access_allowed(request: Request) -> bool:
    """Fail closed for remote API access unless an explicit token is configured."""
    token = os.environ.get("BELIEFWEAVE_DEMO_TOKEN")
    if token:
        auth = request.headers.get("Authorization", "")
        api_key = request.headers.get("X-API-Key", "")
        expected_bearer = f"Bearer {token}"
        return hmac.compare_digest(auth, expected_bearer) or hmac.compare_digest(
            api_key, token
        )
    host = request.client.host if request.client else ""
    return host in {"127.0.0.1", "::1", "localhost", "testclient"}


@app.middleware("http")
async def protect_demo_api(request: Request, call_next):
    if request.url.path.startswith("/api/") and not _demo_access_allowed(request):
        return JSONResponse(
            status_code=401,
            content={
                "detail": (
                    "BeliefWeave demo API is localhost-only unless "
                    "BELIEFWEAVE_DEMO_TOKEN is configured"
                )
            },
        )
    return await call_next(request)


@app.exception_handler(TemporalValueError)
async def temporal_value_error_handler(_request: Request, exc: TemporalValueError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

class IngestRequest(BaseModel):
    user_id: str = Field(default='demo-user', min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=12000)
    context: Optional[str] = Field(default=None, max_length=256)
    timestamp: Optional[str] = None
    idempotency_key: Optional[str] = Field(default=None, min_length=1, max_length=256)

class RecallRequest(BaseModel):
    user_id: str = Field(default='demo-user', min_length=1, max_length=128)
    query: str = Field(min_length=1, max_length=4000)
    context: Optional[str] = Field(default=None, max_length=256)
    limit: int = Field(default=5, ge=1, le=50)
    now: Optional[str] = None

class CorrectionRequest(BaseModel):
    value: str = Field(min_length=1, max_length=4000)

@app.get('/')
def home():
    return FileResponse(ROOT / 'demo' / 'web.html')

@app.get('/project')
def project_home():
    return FileResponse(ROOT / 'site' / 'index.html')

@app.get('/dashboard')
def dashboard():
    return FileResponse(ROOT / 'dashboard' / 'index.html')

@app.get('/health')
def health():
    return {
        'ok': True,
        'service': 'beliefweave',
        'version': app.version,
        **engine.runtime_capabilities(),
    }

@app.post('/api/ingest')
def ingest(req: IngestRequest, idempotency_key_header: Optional[str] = Header(default=None, alias='Idempotency-Key')):
    if req.idempotency_key and idempotency_key_header and req.idempotency_key != idempotency_key_header:
        raise HTTPException(status_code=409, detail='Idempotency-Key header disagrees with request body')
    idem = idempotency_key_header or req.idempotency_key
    try:
        out = engine.ingest(req.user_id, req.text, context=req.context, timestamp=req.timestamp, idempotency_key=idem)
    except IdempotencyTombstonedError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        'event': out['event'].to_dict(),
        'actions': [
            {
                'observation': a['observation'].__dict__ if hasattr(a['observation'], '__dict__') else {k: getattr(a['observation'], k) for k in a['observation'].__slots__},
                'decision': a['policy'].decision.value,
                'score': a['policy'].score,
                'memory': a['memory'].to_dict() if a['memory'] else None,
                'conflicts': a['conflicts'],
            }
            for a in out['actions']
        ],
        'state': _state(out['state']),
        'idempotent_replay': out.get('idempotent_replay', False),
    }

@app.post('/api/recall')
def recall(req: RecallRequest):
    return [
        {'memory': r.memory.to_dict(), 'score': r.score, 'reasons': r.reasons}
        for r in engine.recall(req.user_id, req.query, req.limit, req.context, req.now)
    ]

@app.post('/api/governed-recall')
def governed_recall(req: RecallRequest):
    return [
        {
            'memory': x['retrieval'].memory.to_dict(),
            'retrieval_score': x['retrieval'].score,
            'retrieval_reasons': x['retrieval'].reasons,
            'personalization_action': x['gate'].action.value,
            'authority_score': x['gate'].score,
            'authority_reason': x['gate'].reason,
            'gate_version': engine.belief_gate_version,
        }
        for x in engine.governed_recall(req.user_id, req.query, req.limit, req.context, req.now)
    ]

@app.get('/api/state/{user_id}')
def state(user_id: str, now: Optional[str] = None):
    return _state(engine.current_state(user_id, now=now))

@app.get('/api/memories/{user_id}')
def memories(user_id: str):
    return [m.to_dict() for m in engine.memories.list_all(user_id)]

@app.get('/api/export/{user_id}')
def export_user(user_id: str):
    """Portable, inspectable export of all stored data for one user."""
    out=engine.export_user_data(user_id)
    out['state']=_state(out['state'])
    return out

@app.delete('/api/user/{user_id}')
def purge_user(user_id: str, retain_replay_guard: bool = Query(default=False)):
    """Purge all persisted BeliefWeave data for a user.

    Keeping replay guards retains only hashed/scrubbed idempotency tombstones;
    full erasure removes those markers too.
    """
    return engine.purge_user_data(
        user_id, retain_replay_guard=retain_replay_guard
    )

@app.delete('/api/memory/{memory_id}')
def delete(memory_id: str, hard: bool = Query(default=False)):
    if not engine.memories.get(memory_id):
        raise HTTPException(404, 'memory not found')
    ok = engine.forget_memory(memory_id, delete_source_events=hard)
    return {'ok': ok, 'hard': hard}

@app.patch('/api/memory/{memory_id}')
def correct(memory_id: str, req: CorrectionRequest):
    try:
        corrected = engine.correct_memory(memory_id, req.value)
    except MemoryStateConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if corrected is None:
        raise HTTPException(404, 'memory not found')
    return corrected.to_dict()


def _state(s):
    return {k: [{field: getattr(b, field) for field in b.__slots__} for b in vals] for k, vals in s.items()}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('demo.app:app', host='127.0.0.1', port=8000, reload=False)
