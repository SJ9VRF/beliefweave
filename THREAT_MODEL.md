# Threat Model — BeliefWeave

## Protected assets
Current user state, raw interaction events, memory provenance, deleted memories, contextual preferences, and confidence metadata.

## Primary failure / abuse modes
1. **Memory poisoning** — third-party, quoted, hypothetical, or role-play text is mistaken for a user belief.
2. **Stale-memory harm** — an obsolete preference remains active after a change.
3. **Context collapse** — work/friends/travel preferences are merged into a global belief.
4. **Unsupported inference** — the system converts weak evidence into a sensitive or personal claim.
5. **Deletion leakage** — deleted memory remains retrievable or reconstructable from retained source events.
6. **Overwriting additive state** — multiple valid goals/preferences are collapsed into one value.
7. **Classifier overreach** — a learned conflict model overwrites unrelated memories.

## Implemented mitigations
- explicit provenance per memory
- rule-first attribution and role-play guards
- structural gates around learned conflict resolution
- temporal validity and expiry
- additive-by-default multi-valued state
- context-aware coexistence
- user edit/delete/correct controls
- optional hard deletion of source events
- retrieval only from ACTIVE memories
- regression tests for poisoning, deletion, context, and unrelated-memory overwrite

## Deliberately out of scope for this prototype
Encryption-at-rest, authentication/authorization, multi-tenant isolation, production PII detection, legal retention policy, red-team coverage for all languages, and formal privacy guarantees. A production deployment must add these before handling real personal data.

## Demo API exposure
The reference API now fails closed for non-loopback `/api/*` requests unless `BELIEFWEAVE_DEMO_TOKEN` is configured. Docker Compose requires that token. This is an accidental-exposure guard, not production authentication or user-level authorization.

## Replay-after-erasure and telemetry-linkability tradeoff

A stale retry after deletion is a distinct threat from retention of deletion-control metadata. Full user erasure prioritizes removing all BeliefWeave rows, including replay tombstones; guarded erasure instead retains only scrubbed hashed tombstones so stale idempotent requests fail closed. The caller must choose which property is required.

Telemetry user correlation uses keyed HMAC tokens rather than an unkeyed identifier hash. A caller that configures one stable key gains cross-process correlation and correspondingly increases linkability; the default process-local random key intentionally limits that scope.
