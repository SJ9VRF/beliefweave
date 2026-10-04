# Architecture decisions

The project keeps a small set of explicit architecture decisions so the code review path shows not only *what* was implemented, but *why* the boundaries exist.

- [ADR 0001 — Separate retrieval relevance from behavioral authority](adr/0001-behavioral-authority.md)
- [ADR 0002 — Keep historical authority policies frozen](adr/0002-frozen-evaluation-policies.md)
- [ADR 0003 — Preserve idempotency tombstones after hard forget](adr/0003-idempotency-tombstones.md)
- [ADR 0004 — Use SQLite as the reference store, not a scale claim](adr/0004-reference-storage-scope.md)
- [ADR 0005 — Keep the core runtime optional-ML and telemetry-backend neutral](adr/0005-core-runtime-and-observability.md)

These are design records, not claims that the current choices are universally optimal. They document the tradeoffs that the checked-in implementation is built around.

- [ADR 0006 — Deterministic runtime selection and canonical time](adr/0006-deterministic-runtime-and-temporal-contract.md)
- [ADR 0007 — User data inventory and process-level resilience](adr/0007-user-data-inventory-and-process-resilience.md)
