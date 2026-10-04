# BeliefWeave release notes

This release hardens the boundary between research evidence and the production runtime.

## Research / evaluation
- BeliefShiftBench-v2 remains the frozen primary authority benchmark: 640 controlled cases with a 320-case held-out split.
- The sealed-specification audit, unseen-composition challenge, metamorphic invariants, mutation adequacy, stochastic stability, sensitivity analysis, counterfactual intervention, error propagation, and horizon scaling remain checked in and reproducible.
- External benchmark adapters are present, but no LongMemEval/PersonaMem/LoCoMo score is claimed without an executed official run.

## Runtime / integrity hardening
- Production authority policy remains V3; V1/V2 remain selectable for frozen-paper reproduction.
- `ingest()` is now atomic across event insertion, memory creation, conflict links, and supersession using one `BEGIN IMMEDIATE` SQLite transaction.
- Two explicit fault-injection cases prove rollback after a memory insert and during conflict resolution.
- Provenance-aware hard forget, privacy erasure, concurrency stress, and the 9,600-state authority-policy model check remain release gates.

## Reproducibility
- Added `results/experiment_lineage.json`, binding principal results to SHA256 hashes of generating code and checked inputs.
- Added exact reference validation constraints plus a machine-readable environment comparison report.
- CI is defined across Python 3.10–3.13 with `pip check`, bytecode compilation, coverage, package smoke, atomicity failure injection, model checking, and release audit.

## Validated package
- package: **beliefweave 0.17.0**
- **129/129 tests passed**
- **95.69% line coverage**
- isolated wheel build/install smoke: PASS
- release audit: PASS
## Runtime-quality hardening

- The public core install now has no third-party runtime dependencies; local ML components live behind the `ml` extra.
- A clean virtual-environment check installs the wheel with `--no-deps` and verifies ingest/state behavior without scikit-learn or joblib.
- `PersonalMemoryEngine.runtime_capabilities()` exposes the active extractor/retriever/conflict path explicitly.
- An optional privacy-safe observer hook emits operation metadata and counts without raw interaction text, memory values, context, or raw user identifiers. Observer failures cannot change memory semantics.
- The memory store and lexical retriever were rewritten for readable, reviewable control flow; the critical-path style gate now covers persistence and retrieval as well as governance/engine/schema/public API.
- Site architecture-decision downloads now include their linked ADR files rather than a dangling markdown index.


## Deterministic runtime and user-control semantics

- `PersonalMemoryEngine()` now starts in the deterministic core profile; optional local ML is enabled only with `enable_ml=True`. Installing extra packages no longer changes application behavior implicitly.
- External timestamps are validated and normalized to UTC before persistence and before idempotency hashing; malformed temporal input fails fast rather than silently degrading memory semantics.
- API error handling uses domain exceptions rather than parsing exception strings. Idempotency conflicts, hard-forgotten retries, and invalid time map to stable 409/410/422 semantics.
- User correction is append-and-supersede: it creates a correction event and a new user-verified memory, preserving the prior version and provenance instead of mutating history in place.
- Schema v4 hashes persisted idempotency keys. Hard-forget scrubs request hashes and deleted event identifiers while retaining only a minimal hashed replay tombstone, preventing stale retries from resurrecting forgotten content.
- The demo service is local-only when no token is configured; remote `/api/*` access requires the coarse demo transport token. This is explicitly not presented as production authentication or authorization.

## Data inventory, erasure, and process resilience

- User exports now include persisted idempotency receipts/tombstones under explicit `control_metadata`; raw idempotency keys remain absent because only digests are stored.
- Added atomic whole-user purge with two explicit semantics: full erasure or guarded erasure that retains only scrubbed replay tombstones.
- Observer user correlation now uses HMAC-SHA256 with caller-provided or process-local secret material instead of an unkeyed identifier digest.
- Added process-level SQLite assurance: 4 independent writers complete 80/80 ingests with integrity PASS, and a forced interpreter exit during an uncommitted transaction recovers with zero partial rows.
