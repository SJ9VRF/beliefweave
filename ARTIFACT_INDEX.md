# Project map

The shortest path through BeliefWeave is:

- `site/index.html` — project page
- `site/demo.html` — interactive belief-gate demo
- `paper/BELIEFWEAVE.pdf` — paper
- `REVIEWER_GUIDE.md` — five-minute review path
- `FAILURE_LOG.md` — the implementation failures that changed the design

## Research

- `paper/TECHNICAL_REPORT.md` — extended engineering write-up
- `BENCHMARK_CARD.md` — benchmark scope and limitations
- `NOVELTY_AUDIT.md` — comparison with nearby memory/personalization work
- `EVAL_PROTOCOL.md` — evaluation methodology
- `paper/RESULTS_TABLES.md` — generated result tables

## Code

- `pwm/` — memory engine and belief-governance logic
- `demo/app.py` — FastAPI service
- `benchmark/` — longitudinal, retrieval, robustness, and authority evaluations
- `tests/` — regression and invariant tests
- `scripts/reproduce_all.sh` — end-to-end reproduction
- `dist/` — installable Python wheel

## Safety and data

- `THREAT_MODEL.md`
- `SECURITY.md`
- `MODEL_CARD.md`
- `DATASET_CARD.md`

## Public-facing artifacts

- `site/benchmark.html` — benchmark overview
- `site/technical.html` — implementation deep dive
- `site/blog.html` — accessible explanation of the research question
- `site/beliefweave-demo.mp4` — short demo video
- `site/downloads/beliefweave-github-ready.zip` — repository bundle ready to publish

## Production-assurance artifacts

- `results/authority_modelcheck.json` — finite exhaustive 9,600-state verification per authority-gate version; V3 has zero declared-property violations.
- `results/privacy_erasure.json` — 50-user provenance-aware hard-forget and export-leakage regression.
- `results/concurrency_integrity.json` — 480-ingest, 12-thread local SQLite integrity stress.
- `benchmark/authority_modelcheck.py` — executable authority-policy state-space checker.
- `benchmark/privacy_erasure_eval.py` — executable privacy/provenance erasure regression.
- `benchmark/concurrency_integrity_eval.py` — executable concurrent ingest/recall stress.
- `benchmark/external/locomo_adapter.py` — provider-neutral LoCoMo evidence-retrieval adapter.
- `scripts/fetch_external_benchmarks.py` — opt-in third-party benchmark fetcher with checksum verification where pinned; raw external bytes are not vendored.

## Transactional/reproducibility assurance

- `results/atomicity_fault_injection.json` — injected-crash verification that an ingest never leaves a partial event/memory/conflict update.
- `results/experiment_lineage.json` — machine-readable hashes connecting key result files to the exact code and input manifests that produced them.
- `results/repro_environment.json` — comparison between the current validation environment and the checked reference constraints.
- `constraints/reproducible.txt` — exact package versions used for this release validation; intentionally documented as reference constraints rather than a universal platform lock.
- `benchmark/atomicity_fault_injection_eval.py` — executable atomicity failure-injection suite.

- `COMPETITIVE_LANDSCAPE.md` — closest-work matrix, explicit overlap, falsification tests, and novelty boundary.
## Runtime packaging and operations

- `results/core_install.json` — clean-venv, no-dependency wheel validation for the deterministic core runtime.
- `docs/adr/0005-core-runtime-and-observability.md` — rationale for optional ML and telemetry-backend-neutral observability.
- `scripts/validate_core_install.py` — executable release check for the dependency-free install path.


## Deterministic runtime, temporal and correction contracts

- `docs/adr/0006-deterministic-runtime-and-temporal-contract.md` — why the default runtime is deterministic core, why ML is explicit opt-in, and how temporal/API failure semantics are defined.
- `results/idempotency_privacy_migration.json` — schema-v4 migration, hashed idempotency receipts, scrubbed hard-forget tombstones, replay blocking, relation repair, and correction-provenance checks.
- `pwm/temporal.py` — canonical UTC validation/normalization boundary for external timestamps.
- `PersonalMemoryEngine.correct_memory(...)` — append-and-supersede correction path used by the public API/CLI.

## Data inventory and process resilience

- `results/privacy_inventory.json` — export completeness, full-user erasure, guarded replay tombstones, and keyed telemetry checks.
- `results/database_resilience.json` — independent-process writer integrity and interpreter-crash rollback evidence for the SQLite reference runtime.
- `benchmark/privacy_inventory_eval.py` — executable user-data inventory/privacy assurance.
- `benchmark/database_resilience.py` — executable process-level resilience assurance.
- `docs/adr/0007-user-data-inventory-and-process-resilience.md` — design rationale and erasure/replay tradeoff.
