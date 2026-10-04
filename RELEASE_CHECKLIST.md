# Release Checklist

A public release is ready only when every item below is satisfied.

## Correctness
- [x] all regression/API/invariant tests pass
- [x] line coverage is at least 90%
- [x] deterministic generator reproduces identical logical output for the canonical seed
- [x] different seeds produce different synthetic trajectories
- [x] multi-user interleaving does not violate user isolation
- [x] hard forget purges memory and source events
- [x] superseded/expired/deleted memories do not leak into active retrieval

## Research integrity
- [x] synthetic results are labeled as synthetic/controlled
- [x] OOD weakness is reported rather than hidden
- [x] calibration is recomputed from raw predictions
- [x] publication tables/summary are generated from result JSON
- [x] environment-dependent throughput is not presented as a fixed claim
- [x] limitations distinguish engineering validation from real-user evidence

## Reproducibility
- [x] `./scripts/reproduce_all.sh` regenerates tests, coverage, benchmarks, figures, dashboard and publication summary
- [x] serialized learned components have retraining scripts
- [x] release audit fails on missing or inconsistent core artifacts
- [x] checksums are generated after release cleanup

## Public repository hygiene
- [x] benchmark card
- [x] dataset card
- [x] model card
- [x] threat model / security notes
- [x] contributing guide
- [x] developer guide
- [x] issue and pull-request templates
- [x] reviewer guide and demo script

## Paper-grade research evidence
- [x] frozen held-out BeliefShiftBench-v2 test manifest separated from development cases
- [x] strong policy baselines beyond retrieval-only
- [x] bootstrap confidence intervals and paired significance tests
- [x] calibration, risk–coverage, threshold and cost-sensitivity analyses
- [x] component ablations by failure family
- [x] counterfactual response-intervention evaluation
- [x] controlled fault-injection/error-propagation analysis
- [x] 10k-turn memory-core scaling evaluation
- [x] external LongMemEval and PersonaMem-style adapters included without fabricated scores
- [x] human A/B protocol/UI/analysis kit included without fabricated participant results

## User data / process resilience
- [x] export includes persisted idempotency control metadata
- [x] full user purge leaves no BeliefWeave rows for the user
- [x] guarded purge retains only scrubbed hashed replay markers
- [x] telemetry identifiers are HMAC-keyed and exclude raw user/content fields
- [x] independent-process writer check passes
- [x] interpreter-crash rollback leaves no partial event/memory rows
