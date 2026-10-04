# Final Validation Record

Validated from a clean release working tree.

## Regression and coverage
- **129/129 tests passed**
- **95.69% line coverage** across `pwm` + `demo`
- CI floor: **90%**

## Paper-grade authority evaluation
BeliefShiftBench-v2 contains **640 deterministic controlled cases** split into **320 development + 320 frozen held-out test cases** across eight authority families. The primary endpoint is exact three-way `USE / ASK / ABSTAIN` accuracy.

Held-out test results:
- **BeliefWeave:** exact action accuracy **96.88%**; 95% bootstrap CI **95.00–98.75%**
- **Cost-sensitive authority policy:** **83.13%**
- **Temporal + context filtering:** **62.50%**
- **Metadata score without hard vetoes:** **59.38%**
- **Confidence-only:** **50.00%**
- **Provenance-only:** **50.00%**
- **Retrieval-only:** **37.50%**
- **Oracle:** **100.00%**

False-personalization rate:
- BeliefWeave: **1.56%**
- Retrieval-only: **62.50%**

Counterfactual Personalization Regret (lower is better):
- BeliefWeave: **0.0938**
- Retrieval-only: **1.2500**

Paired significance:
- BeliefWeave vs temporal+context: exact McNemar **p = 1.54e-33**
- BeliefWeave vs metadata-score baseline: exact McNemar **p = 1.50e-36**

Artifacts: `results/paper_grade_eval.json`, `benchmark/beliefshift_v2_test_manifest.json`.

## Counterfactual response intervention
On the **320-case frozen test split**, using the deterministic controlled response renderer:
- BeliefWeave exact action accuracy: **96.88%**
- Personalization intervention fidelity: **98.44%**
- Behavior intervention fidelity: **98.44%**
- False personalization influence rate: **1.56%**
- Missed personalization rate: **0.00%**

Retrieval-only personalization intervention fidelity is **37.50%** and behavior intervention fidelity is **62.50%**.

This is a controlled causal-mechanism test, **not** an external LLM response-quality or human-preference result. Artifact: `results/behavior_intervention.json`.

## Calibration and selective personalization
The current authority score is useful for ranking/selective decisions but is **not yet well calibrated**:
- Brier score: **0.1180**
- NLL: **0.3332**
- ECE (10 bins): **0.2243**
- Adaptive ECE (10 bins): **0.2100**

This limitation is intentionally reported rather than hidden. Threshold sweeps and risk–coverage outputs are stored in `results/paper_grade_eval.json`.

## Component ablations
The cost-sensitive policy's exact-action accuracy on the frozen test split is **83.13%** with all signals. Removing the strongest structural signals gives:
- no temporal validity: **70.63%**
- no context match: **70.63%**
- no conflict signal: **70.63%**
- no lifecycle/status signal: **70.63%**
- no provenance signal: **79.38%**
- no verification signal: **83.13%**

The no-verification result indicates that this controlled benchmark does not isolate a measurable verification contribution; the paper treats that as a benchmark limitation, not evidence that verification is unnecessary.

## Fault-injection / error propagation
Controlled synthetic perturbations were applied to the frozen test cases. Exact-action accuracy changes from clean **96.88%** to:
- extractor/source corruption: **75.00%**
- state/status corruption: **71.88%**
- context loss: **84.38%**
- conflict loss: **84.38%**
- forced-use authority: **25.00%**
- generated behavior that inverts authority: **0.00%**

These are sensitivity measurements under synthetic perturbations, not estimates of real-world fault frequency. Artifact: `results/error_propagation.json`.

## Long-horizon memory-core scaling
A local SQLite memory-core scaling run covers **10 / 100 / 1,000 / 10,000 turns**. At 10,000 turns the controlled workload contains **200 historical memory rows, 25 active rows, and 0 duplicate active single-value slots**.

Recorded local 10k measurements:
- p95 event write: **~0.31 ms**
- p95 memory update: **~0.71 ms**
- p95 authority gate: **~0.009 ms**

These numbers are environment-dependent and exclude model/network latency. Artifact: `results/horizon_scaling.json`.

## Legacy engineering and retrieval validation
- MemWorldBench quick slice: **20 users × 100 turns = 2,000 interactions**
- preference-reversal obsolete-belief retirement: **100% PWM vs 0% append-only**
- temporary-expiry accuracy: **100% PWM vs 0% append-only/latest-predicate**
- hard scenarios: **360/360 passed**
- OOD observation-router accuracy: **65.79% on 114 held-out paraphrase examples**
- selective prediction at confidence ≥0.70: **83.78% accuracy at 32.46% coverage**
- OOD observation-router ECE: **0.0486**
- controlled hybrid-conflict challenge: **100% on 12 cases**
- adversarial engine checks: **5/5**
- retrieval suite: **120 controlled queries**
  - lexical: Hit@1 **55.0%**, Hit@3 **86.7%**, MRR **0.683**, stale leaks **0**
  - local hybrid: Hit@1 **73.3%**, Hit@3 **95.0%**, MRR **0.835**, stale leaks **0**
- stress run: **2,000 interactions**, **0 active exact contradictions**

## External benchmark readiness
Runnable adapters are included for:
- **LongMemEval**: `benchmark/external/longmemeval_adapter.py`
- **PersonaMem-style evaluation**: `benchmark/external/personamem_adapter.py`

The official third-party datasets/model-dependent end-to-end runs were **not executed in this build environment**, so **no external benchmark score is claimed**. The machine-readable status is recorded in `benchmark/external/status.json`.

## Human evaluation readiness
A blind A/B human-evaluation package is included under `human_eval/`, including protocol, annotation schema, local annotation interface, and Wilson-CI analysis code. **No human participants were run and no human-preference result is claimed.**

## Determinism, distribution, and contracts
- canonical synthetic seed: **17**; same-seed logical SHA-256 match: yes; different-seed output differs: yes
- package: `beliefweave` **0.17.0**
- wheel: `dist/beliefweave-0.17.0-py3-none-any.whl`
- isolated wheel install + engine smoke: PASS
- installed `pwm` console entrypoint: PASS
- schema contract: SQLite schema version **4**; future-schema fail-closed regression: PASS
- API/UI release smoke: PASS
- OpenAPI contract snapshot present and release-gated
- database integrity checks: PASS on clean databases + corruption-class regressions
- lightweight static-security guardrail: zero error-severity findings; **not** a formal security audit
- runtime profile exists and is explicitly environment-dependent

## Publication and public-surface validation
- manuscript: `paper/BELIEFWEAVE.pdf` — **9 pages**
- title: **BeliefWeave: Governing When Memory May Change Behavior**
- author: **Aura Yavary**
- PDF rendered and visually inspected with no observed clipping, overlap, or broken glyphs
- PDF project/build date metadata suppressed
- 14/14 required homepage sections present
- 5/5 Hero CTAs present: Paper / Code / Demo / Benchmark / Video
- local artifact links resolve inside the site bundle
- live browser authority gate, benchmark page, technical deep dive, blog, source bundle, dataset, and playable 36-second MP4 are present
- public-facing project surfaces remain date-free

## Scientific boundary
The new authority results are **synthetic, deterministic, controlled mechanism evaluations**. They provide stronger held-out, statistical, ablation, calibration, intervention, fault-injection, and scaling evidence than the earlier prototype evaluation, but they do **not** establish real-user utility, trust, broad external-benchmark superiority, or state of the art. External benchmark and human-study harnesses are included specifically so those claims can be tested without fabricating evidence.

## Reproduce
```bash
python -m pip install -e '.[dev,ml,demo]'
pytest --cov=pwm --cov=demo --cov-fail-under=90 -q
./scripts/reproduce_all.sh
```

## Generalization / submission hardening
- unseen-composition challenge: 2,880 decisions; original gate exact action accuracy **75.0%**
- challenge-informed V2 regression patch on the same suite: **100%** (not counted as independent generalization evidence)
- 30-seed stochastic stability: 12,000 decisions per policy; BeliefWeave exact action accuracy **100%** within pre-specified label-safe perturbations
- threshold sweep: 168 settings; only 8 are within 1 percentage point of the best exact accuracy
- cost sensitivity: 60 settings; 20% jointly exceed 80% exact accuracy and stay at or below 5% false personalization
- Croissant local structural check: core + minimal RAI fields present; official network validation and reviewer-accessible hosting remain submission-time external actions

## Production-governance and privacy assurance

- Runtime default authority policy: **V3**; V1/V2 remain selectable for frozen paper reproduction.
- Finite authority-state audit: **9,600 states per gate**; declared-property violations: **V1 560 / V2 146 / V3 0**.
- Privacy erasure regression: **50 users**, **0 deleted-event export leaks**, **50/50 multi-source sibling provenance repairs**, database integrity PASS.
- Concurrency/integrity stress: **480/480 ingests**, **0 errors**, **12 local threads**, database integrity PASS.
- Scope boundary: model checking covers the declared finite policy model; privacy testing covers the local database; concurrency testing is single-process SQLite. None is a claim of formal verification, legal privacy compliance, or distributed production scale.


## Transactional ingest
- one `BEGIN IMMEDIATE` transaction covers source event, derived memories, supersession, and conflict links
- injected failure after memory insertion: full rollback PASS
- injected failure during conflict resolution: prior state preserved PASS
- `results/atomicity_fault_injection.json`: 2/2 injected faults PASS

## Experiment lineage / reference environment
- `results/experiment_lineage.json`: SHA256-linked code/input/result lineage for principal experiments
- `constraints/reproducible.txt`: exact versions used for validation, explicitly scoped as reference constraints
- `results/repro_environment.json`: reference-environment match PASS
- CI definition covers Python 3.10, 3.11, 3.12, and 3.13
## Core install and observability

- validated wheel installs in a clean virtual environment with `--no-deps`;
- dependency-free core ingest/state smoke: **PASS**;
- optional ML path remains separately exercised by the full research test suite;
- observer payload contract excludes raw text, memory values, context, and raw user identifiers;
- observer failure isolation is regression-tested.


## Deterministic runtime / correction boundary

- default `PersonalMemoryEngine()` remains core even when optional ML dependencies are installed: PASS
- explicit `enable_ml=True` activates the checked local hybrid path: PASS
- timestamps validate and canonicalize to UTC before persistence/idempotency hashing: PASS
- domain-specific API errors map idempotency conflict / hard-forgotten replay / invalid time to 409 / 410 / 422: PASS
- corrections are append-and-supersede with source-event provenance and idempotent replay: PASS
- schema v4 stores hashed idempotency keys; hard-forget tombstones scrub request/event metadata while blocking resurrection: PASS
- unauthenticated remote demo API access fails closed unless the demo transport token is configured: PASS

## User data inventory and process resilience

- complete per-user export includes persisted idempotency control metadata: PASS
- full user erasure removes events, memories, and receipts: PASS
- guarded erasure retains only hashed/scrubbed replay tombstones: PASS
- telemetry correlation identifiers are HMAC-keyed and content-free: PASS
- independent-process SQLite writers: **80/80 events observed**, integrity PASS
- forced interpreter exit inside an uncommitted event+memory transaction: **0 partial events / 0 partial memories**, integrity PASS
- scope boundary: local SQLite reference runtime only; no distributed-durability or legal-compliance claim
