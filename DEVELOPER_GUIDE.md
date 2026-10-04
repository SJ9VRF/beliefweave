# Developer Guide

## Fast paths
- Core engine: `pwm/engine.py`
- Event persistence: `pwm/events/store.py`
- Observation extraction: `pwm/observations/`
- Memory lifecycle: `pwm/memory/`
- Conflict/state logic: `pwm/world_model/`
- Longitudinal simulator: `pwm/simulation/`
- Evaluations: `benchmark/`
- API/demo: `demo/`

## Invariants
The implementation is expected to preserve the following invariants:

1. **User isolation** — no state or retrieval crosses user IDs.
2. **Temporal validity** — expired memory is not active at a later evaluation time.
3. **Additive-by-default semantics** — unrelated preferences/goals do not destructively overwrite one another.
4. **Evidence-backed supersession** — destructive updates require a compatible conflict family.
5. **Provenance retention** — active memory retains source event IDs unless the user explicitly hard-forgets it.
6. **Hard forget semantics** — hard forget purges both memory row and source event(s).
7. **No stale retrieval** — superseded/expired/deleted records cannot leak into active recall.
8. **Determinism where promised** — benchmark generators with the same seed produce byte-equivalent logical records.

## Adding a learned component
A learned component must have:
- a deterministic training script or recorded model artifact
- an out-of-distribution evaluation
- calibration or abstention analysis if its output controls persistent memory writes
- a structural safety gate if a wrong prediction could destructively overwrite state

## Debugging philosophy
Prefer explicit typed state and inspectable decisions over opaque end-to-end behavior. When a learned component is uncertain, abstention or a non-destructive action is preferable to irreversible personalization.

## Data lifecycle controls

`export_user_data(user_id)` includes conversational records, current state, and persisted idempotency control metadata. `purge_user_data(user_id)` performs full erasure by default; `retain_replay_guard=True` intentionally keeps only scrubbed hashed tombstones to reject stale retries. Do not describe guarded erasure as complete deletion.

If an observer callback is configured, user correlation uses HMAC. Supply `observer_hmac_key` only when stable cross-process correlation is required; omitting it creates a process-local random secret and limits linkability by default.
