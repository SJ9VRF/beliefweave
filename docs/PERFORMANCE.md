# Local Runtime Profile

`scripts/profile_runtime.py` records a small local profile in `results/runtime_profile.json` using the packaged local models and SQLite backend.

Reported fields include ingest and recall median/p95 latency, RSS delta, `tracemalloc` peak, and database size. These values are environment-dependent engineering observations, **not** production latency or capacity claims.

Re-run with:

```bash
PWM_PROFILE_N=400 python scripts/profile_runtime.py
```
