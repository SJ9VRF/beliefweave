# Quality Gates

A public research release is valid only when all of the following hold.

## Correctness and regression
- full regression/API/invariant suite passes
- line coverage for `pwm` + `demo` is at least 90%
- 360 hard scenarios pass
- retrieval evaluation reports zero stale-memory leaks
- adversarial attribution/role-play checks pass
- hard forget purges memory and referenced source events
- user-isolation invariants pass

## Paper-grade authority evidence
- BeliefShiftBench-v2 contains a frozen held-out test manifest separate from development cases
- exact `USE / ASK / ABSTAIN` results are generated from `results/paper_grade_eval.json`
- bootstrap confidence intervals and paired McNemar comparisons are present
- threshold/cost sensitivity and risk–coverage outputs are present
- component ablations are present
- controlled counterfactual response-intervention results are present
- fault-injection/error-propagation results are present
- 10k-turn local memory-core scaling results are present
- calibration weakness is reported rather than hidden

## Scientific integrity
- synthetic/controlled results are labeled as such
- OOD router weakness is reported separately from template-distribution results
- external benchmark adapters must not be presented as executed scores unless official runs actually exist
- human-evaluation scaffolding must not be presented as participant evidence unless real annotations exist
- environment-dependent latency/throughput is labeled local and non-production
- no SOTA or broad real-user utility claim is inferred from controlled mechanism tests

## Reproducibility and distribution
- `results/test_summary.json` reports all tests passing
- installed wheel exposes `pwm = pwm.cli:main`
- isolated wheel smoke passes
- SQLite schema version matches `CURRENT_SCHEMA_VERSION` and future versions fail closed
- OpenAPI, data contract, SBOM, dependency snapshot, static-security result and runtime profile are present
- publication/site generators and release audit pass
- public surface remains date-free

## Data lifecycle and process resilience
- per-user export inventories persisted control metadata as well as events/memories/state
- full-user erasure removes all user-scoped rows when replay guards are not retained
- guarded erasure retains only hashed/scrubbed replay tombstones and is not labeled complete erasure
- telemetry user correlation is HMAC-keyed rather than an unkeyed identifier digest
- independent-process SQLite writer check passes with no lost events
- forced interpreter exit with an uncommitted event+memory transaction recovers with zero partial rows

Current checked release: **129 tests passed, 95.69% line coverage, package 0.17.0**.
