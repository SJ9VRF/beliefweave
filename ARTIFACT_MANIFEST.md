# Artifact Manifest

## Core research system
- `pwm/engine.py` — orchestration
- `pwm/memory/` — schema, persistence, policies, lexical/semantic retrieval, consolidation
- `pwm/observations/` — deterministic and hybrid learned routing/extraction
- `pwm/world_model/` — temporal state, conflict resolution, learned/hybrid conflict models
- `pwm/events/` — raw event provenance store

## Evaluation
- `benchmark/data/memworldbench_1000x100.jsonl` — 100k generated longitudinal interactions
- `benchmark/data/hard_scenarios_360.jsonl` — 360 hard scenarios
- `benchmark/run_benchmark.py` — executable longitudinal slice
- `benchmark/evaluate_hard_scenarios.py` — regression suite
- `benchmark/evaluate_ood.py` — linguistic distribution shift and adversarial cases
- `benchmark/evaluate_retrieval.py` — controlled relevance/context/staleness retrieval benchmark
- `benchmark/stress_test.py` — stress/invariant validation
- `experiments/run_ablations.py` — controlled ablations
- `results/*.json` — measured outputs

## Learned components
- `scripts/train_write_policy.py`
- `scripts/train_semantic_router.py`
- `scripts/train_conflict_model.py`
- serialized local models under `results/`

## Product/demo surface
- `demo/app.py` — FastAPI service
- `demo/web.html` — interactive browser demo
- `dashboard/index.html` — measured evaluation dashboard

## Research communication
- `paper/TECHNICAL_REPORT.md`
- `paper/MANUSCRIPT.md` — publication-style manuscript
- `paper/REPRODUCIBLE_SUMMARY.md` — result summary generated directly from JSON
- `paper/RESULTS_TABLES.md` — generated result tables
- `paper/figures/` — generated PNG/PDF result figures
- `DATASET_CARD.md`
- `MODEL_CARD.md`
- `EVAL_PROTOCOL.md`
- `THREAT_MODEL.md`
- `FAILURE_LOG.md`
- `RESEARCH_NOTEBOOK.md`
- `RESEARCH_TALK.md`

## Engineering/reproducibility
- `tests/` — 129 regression/safety/API/invariant/packaging tests across the current suite, including `test_api_e2e.py`
- `scripts/reproduce_all.sh`
- `Makefile`
- `.github/workflows/ci.yml`
- `pyproject.toml`
- `LICENSE`
- `CITATION.cff`

## Release hardening
- `site/index.html` — polished project overview/homepage
- `docs/ARCHITECTURE.md` — system architecture and invariants
- `docs/API.md` — local demo API contract
- `docs/EXPERIMENTS.md` — evaluation interpretation and next study
- `SECURITY.md` — explicit production-security gaps and implemented safeguards
- `FINAL_VALIDATION.md` — exact final validation record
- `RELEASE_NOTES.md` — release-candidate summary
- `Dockerfile` / `docker-compose.yml` — local container deployment

## Final review / quality artifacts
- `REVIEWER_GUIDE.md` — five-minute reviewer path
- `DEMO_SCRIPT.md` — three-minute live demo walkthrough
- `PORTFOLIO_COPY.md` — concise portfolio and interview framing
- `QUALITY_GATES.md` — enforced release criteria
- `results/calibration.json` — OOD calibration and selective-prediction measurements
- `results/coverage.json` — measured test coverage
- `benchmark/evaluate_calibration.py` — reproducible calibration evaluation

## Publication integrity
- `scripts/sync_publication.py` — regenerates publication metrics from result JSON
- `scripts/audit_release.py` — fails on stale claims, malformed calibration bins, stale retrieval leaks, or coverage below release gate
## Public repository / determinism
- `BENCHMARK_CARD.md` — benchmark scope, ground truth, metrics, limitations and canonical seed
- `CONTRIBUTING.md` — contribution/reproduction requirements
- `DEVELOPER_GUIDE.md` — invariants and code navigation
- `RELEASE_CHECKLIST.md` — public-release completion checklist
- `scripts/check_determinism.py` — deterministic generator audit
- `results/determinism.json` — recorded same-seed/different-seed hashes
- `.github/ISSUE_TEMPLATE/` / `.github/pull_request_template.md` — structured public collaboration templates


## Distribution artifacts
- `dist/beliefweave-0.17.0-py3-none-any.whl` — validated installable core package with learned runtime assets.
- `results/package_smoke.json` — wheel build/install/behavior smoke evidence.
- `results/release_smoke.json` — API/UI/export/hard-forget smoke evidence.
- `DEPENDENCY_SNAPSHOT.md` / `results/dependency_snapshot.json` — validated environment versions.
- `ARTIFACT_INDEX.md` — reviewer-facing navigation index.
- `scripts/finalize_release.py` — clean release staging/checksum/zip builder.

## V8 CLI / schema / supply-chain artifacts
- `pwm/cli.py` — installed `pwm` console interface.
- `pwm/schema_version.py` — explicit SQLite schema-version contract and fail-closed compatibility check.
- `results/data_contract.json` — machine-readable tables/columns/enums/schema version.
- `results/wheel_cli_validation.json` — wheel entrypoint + isolated-target doctor/demo/benchmark validation.
- `SBOM.json` — minimal validated-environment component inventory.
- `scripts/reviewer_demo.sh` — one-command reviewer flow after package install.
- `scripts/validate_data_contract.py` — schema/data-contract generator.
- `scripts/validate_wheel_cli.py` — validates console entrypoint and installed wheel behavior.

## Publication and public site
- `paper/BELIEFWEAVE.tex` — self-contained publication manuscript source
- `paper/BELIEFWEAVE.pdf` — rendered publication manuscript
- `paper/references.bib` — reference metadata for external tooling
- `scripts/generate_paper.sh` — deterministic local paper build
- `scripts/generate_site.py` — result-synchronized static-site generator
- `site/index.html` — GitHub Pages-ready project homepage
- `site/paper.pdf` — public-site paper copy
- `site/dashboard.html` — public-site evaluation dashboard
- `.github/workflows/pages.yml` — GitHub Pages deployment workflow
- `.zenodo.json`, `codemeta.json`, `CITATION.cff` — citation/release metadata

## V10 integrity / interface evidence
- `pwm/integrity.py` - non-mutating relational/lifecycle integrity audit.
- `results/openapi.json` - generated FastAPI OpenAPI contract snapshot.
- `results/static_security.json` - lightweight static-security guardrail result.
- `results/runtime_profile.json` - local, environment-dependent runtime profile.
- `results/test_summary.json` - machine-readable pytest summary.
- `docs/OPENAPI_CONTRACT.md`, `docs/INTEGRITY.md`, `docs/PERFORMANCE.md` - reviewer-facing contract documentation.

## Project homepage / 60-second review surface
- `site/index.html` — standalone 14-section hiring-manager project page.
- `site/demo.html` — interactive USE / ASK / ABSTAIN trajectory replay.
- `site/benchmark.html` — benchmark, baselines, ablations, and downloadable evaluation artifacts.
- `site/technical.html` — engineering / training / evaluation deep dive.
- `site/blog.html` — accessible research blog post.
- `site/beliefweave-demo.mp4` — short visual demo video.
- `site/downloads/beliefweave-code.zip` — reproducibility-oriented source bundle.
- `site/downloads/memworldbench_1000x100.jsonl.gz` — compressed full synthetic longitudinal dataset.
- `results/site_contract.json` — machine-readable validation of the 14-section project page contract.


## Paper-grade authority evaluation
- `benchmark/paper_grade_eval.py` — 640-case BeliefShiftBench-v2, frozen 320-case test split, eight baselines/policies, bootstrap CIs, exact McNemar tests, threshold/cost sweeps, risk–coverage, calibration, and component ablations.
- `benchmark/behavior_intervention_eval.py` — controlled counterfactual response-intervention evaluation.
- `benchmark/error_propagation_eval.py` — controlled fault-injection / error-propagation sensitivity analysis.
- `benchmark/horizon_scaling.py` — 10 / 100 / 1k / 10k local memory-core scaling evaluation.
- `benchmark/beliefshift_v2_test_manifest.json` — frozen held-out authority test manifest.
- `benchmark/croissant.json` — benchmark metadata for dataset/evaluation interoperability.
- `results/paper_grade_eval.json` — primary paper-grade authority results and statistics.
- `results/behavior_intervention.json` — intervention-fidelity measurements.
- `results/error_propagation.json` — fault-injection measurements.
- `results/horizon_scaling.json` — local scaling measurements.
- `scripts/generate_paper_grade_figures.py` — regenerates v2 paper figures from checked-in result JSON.
- `paper/figures/authority_baselines.{pdf,png}` — held-out exact-action comparison.
- `paper/figures/risk_coverage.{pdf,png}` — selective-personalization tradeoff.
- `paper/figures/authority_ablation_v2.{pdf,png}` — structural-signal ablations.
- `paper/figures/horizon_scaling.{pdf,png}` — local memory-core scaling.

## External and human evaluation harnesses
- `benchmark/external/longmemeval_adapter.py` — LongMemEval ingestion/evidence-recall adapter; no external score is fabricated.
- `benchmark/external/personamem_adapter.py` — PersonaMem-style provider-neutral request builder.
- `benchmark/external/status.json` — machine-readable execution status and scientific boundary for external evaluations.
- `human_eval/PROTOCOL.md` — blind A/B personalization evaluation protocol.
- `human_eval/annotation_schema.json` — annotation contract.
- `human_eval/index.html` — local annotation surface.
- `human_eval/analyze.py` — preference analysis with Wilson confidence intervals.

## Decision-theoretic authority layer
- `pwm/belief_governance.py` — includes `AuthorityCosts`, `authority_probability`, and `CostSensitiveAuthorityPolicy` in addition to the governed-recall surface.
- `tests/test_decision_theoretic_authority.py` — regression tests for cost-sensitive USE / ASK / ABSTAIN decisions.

## Production-assurance artifacts

- `results/authority_modelcheck.json` — finite exhaustive 9,600-state verification per authority-gate version; V3 has zero declared-property violations.
- `results/privacy_erasure.json` — 50-user provenance-aware hard-forget and export-leakage regression.
- `results/concurrency_integrity.json` — 480-ingest, 12-thread local SQLite integrity stress.
- `benchmark/authority_modelcheck.py` — executable authority-policy state-space checker.
- `benchmark/privacy_erasure_eval.py` — executable privacy/provenance erasure regression.
- `benchmark/concurrency_integrity_eval.py` — executable concurrent ingest/recall stress.
- `benchmark/external/locomo_adapter.py` — provider-neutral LoCoMo evidence-retrieval adapter.
- `scripts/fetch_external_benchmarks.py` — opt-in third-party benchmark fetcher with checksum verification where pinned; raw external bytes are not vendored.


### Transactional/reproducibility assurance
- `results/atomicity_fault_injection.json` — injected-crash atomicity regression (2/2 pass).
- `results/experiment_lineage.json` — result/code/input SHA256 lineage for principal experiments.
- `results/repro_environment.json` — validation-environment comparison to exact reference constraints.
- `constraints/reproducible.txt` — exact reference package versions used for this validated build.
- `benchmark/atomicity_fault_injection_eval.py` — executable rollback/failure-injection evaluation.

- `COMPETITIVE_LANDSCAPE.md` — closest-work matrix and explicit novelty/falsification boundary.

- `results/core_install.json` — dependency-free core wheel installation and runtime smoke evidence.

### User data inventory / process-level resilience
- `results/privacy_inventory.json` — export completeness, full erasure, guarded replay-marker retention, and keyed telemetry checks.
- `results/database_resilience.json` — 4-process writer integrity plus interpreter-crash rollback evidence for the SQLite reference runtime.
- `benchmark/privacy_inventory_eval.py` — executable data-lifecycle assurance.
- `benchmark/database_resilience.py` — executable process-level persistence assurance.
- `docs/adr/0007-user-data-inventory-and-process-resilience.md` — explicit erasure/replay and telemetry-correlation tradeoffs.
