# Database Integrity Audit

`pwm.integrity.audit_database()` is a non-mutating relational/lifecycle audit used by `pwm doctor`.

It checks:
- supported schema version and migration tables,
- required SQLite tables,
- source-event provenance references and same-user ownership,
- `supersedes` references,
- symmetric `conflicts_with` references,
- idempotency receipts, including tombstone/event consistency and request-hash shape,
- invalid serialized relation fields,
- active memories whose validity window has already ended.

Hard-forget is transactionally provenance-aware: it removes source events, repairs surviving provenance, removes references to purged memories, clears `supersedes` pointers to purged memories, and tombstones idempotency receipts so a stale retry cannot resurrect forgotten content.

Errors fail the integrity check. Lazy-expiry findings are warnings because `list_active()` performs expiry transitions. Corruption classes are covered by regression tests and the idempotency/privacy/migration evaluation.
