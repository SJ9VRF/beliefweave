# Demo API

Run:

```bash
PYTHONPATH=. uvicorn demo.app:app --host 127.0.0.1 --port 8000
```

## Endpoints

- `GET /health` — service health/version
- `POST /api/ingest` — ingest an interaction and return memory actions + current state
- `POST /api/recall` — retrieve active memories relevant to a query
- `GET /api/state/{user_id}` — materialized current state
- `GET /api/memories/{user_id}` — full memory ledger, including inactive/superseded entries
- `GET /api/export/{user_id}` — portable user memory/state export
- `PATCH /api/memory/{memory_id}` — user correction
- `DELETE /api/memory/{memory_id}` — soft deletion
- `DELETE /api/memory/{memory_id}?hard=true` — delete memory and associated source events
- `GET /dashboard` — evaluation dashboard
- `GET /project` — project overview page

The API is a local research demo. It does not include authentication, multi-tenant authorization, encryption-at-rest, rate limiting, or production privacy controls.
