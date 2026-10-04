# ADR 0004 — Use SQLite as the reference store, not a scale claim

## Decision
The reproducible reference implementation uses SQLite with explicit transactions and integrity audits.

## Why
The research question is about temporal belief revision and behavioral authority, not distributed storage. SQLite keeps the artifact inspectable, deterministic, and easy to reproduce while still allowing real transaction, migration, concurrency, and deletion tests.

## Consequences
- Local latency and concurrency results describe this reference implementation only.
- Production-scale claims require a different storage backend and independent load testing.
- Storage boundaries remain narrow enough that another backend can replace SQLite without changing the authority policy.
