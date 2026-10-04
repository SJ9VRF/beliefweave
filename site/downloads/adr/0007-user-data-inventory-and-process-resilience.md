# ADR 0007 — Make user data inventory explicit and test process-level SQLite resilience

## Context

BeliefWeave already exposed per-user event/memory export and memory-level hard forget. Two review findings remained:

1. The export called itself complete while omitting user-scoped idempotency receipts/tombstones that are actually persisted.
2. Reliability evidence covered transactions and threads, but not independent writer processes or an interpreter dying with an open transaction.

Observability also used an unkeyed digest of `user_id`, which is not a strong pseudonymization boundary for low-entropy identifiers.

## Decision

- `export_user_data()` inventories persisted control metadata as well as conversational events/memories. Raw idempotency keys are never available because only digests are stored.
- `purge_user_data()` has two explicit modes:
  - **full erasure** removes events, memories, and idempotency receipts;
  - **guarded erasure** retains only scrubbed hashed replay tombstones to block stale retries.
- Telemetry correlation identifiers are HMAC-SHA256 tokens. By default the HMAC key is process-local random material; callers may provide a secret when stable cross-process correlation is intentionally required.
- A process-level resilience check uses independent engine processes against one SQLite file and separately kills an interpreter with an uncommitted event+memory transaction to verify rollback on recovery.

## Tradeoffs

Full erasure deliberately removes replay markers, so an old client request cannot be recognized after deletion. Guarded erasure prevents that replay resurrection but retains minimal user-scoped control metadata. The API returns which mode was used rather than hiding this tradeoff.

The process-resilience check validates the checked SQLite reference runtime only. It is not a distributed-storage durability claim and does not replace production database testing.
