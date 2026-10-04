from __future__ import annotations
import json, sys
from pathlib import Path
from uuid import uuid4
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
from demo.app import app, engine, DB
client = TestClient(app)
uid = f"smoke-{uuid4().hex}"
checks = {}

for route in ['/health', '/', '/project', '/dashboard']:
    r = client.get(route)
    checks[f'GET {route}'] = r.status_code == 200

r = client.post('/api/ingest', json={'user_id': uid, 'text': 'I love sushi.', 'context': 'food'})
checks['ingest'] = r.status_code == 200
payload = r.json()
memories = [a['memory'] for a in payload.get('actions', []) if a.get('memory')]
checks['memory_created'] = bool(memories)
if memories:
    mid = memories[0]['id']
    eid = memories[0]['source_event_ids'][0]
    rec = client.post('/api/recall', json={'user_id': uid, 'query': 'dinner food', 'context': 'food'})
    checks['recall'] = rec.status_code == 200 and any(x['memory']['value'] == 'sushi' for x in rec.json())
    exp = client.get(f'/api/export/{uid}')
    checks['export'] = exp.status_code == 200 and any(m['id'] == mid for m in exp.json()['memories'])
    dele = client.delete(f'/api/memory/{mid}?hard=true')
    checks['hard_forget_http'] = dele.status_code == 200 and dele.json().get('ok') is True
    checks['hard_forget_memory_purge'] = engine.memories.get(mid) is None
    checks['hard_forget_event_purge'] = engine.events.get(eid) is None

checks['demo_db_outside_repo'] = ROOT not in DB.resolve().parents
result = {
    'passed': all(checks.values()),
    'checks': checks,
    'demo_db': str(DB),
}
(ROOT / 'results' / 'release_smoke.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
if not result['passed']:
    raise SystemExit(1)
