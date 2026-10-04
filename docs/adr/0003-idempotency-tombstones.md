# ADR 0003 — Preserve idempotency tombstones after hard forget

## Decision
Hard forget deletes user content but keeps a minimal tombstoned idempotency receipt for requests that had an idempotency key.

## Why
Deleting the receipt entirely would let a stale network retry recreate data the user explicitly removed. Keeping the original content would violate the purpose of hard deletion. A content-free tombstone prevents resurrection without retaining the deleted event payload.

## Consequences
- Old retries fail closed instead of recreating deleted data.
- Reusing a tombstoned key is distinguishable from a normal replay.
- Tombstones contain only the minimum metadata required to block resurrection.
