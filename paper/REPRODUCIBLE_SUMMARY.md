# Reproducible Results Summary

This file is generated from `results/*.json` by `scripts/sync_publication.py`. Do not edit measured values by hand.

## Primary authority evaluation — BeliefShiftBench-v2
- Total controlled cases: **640**
- Development split: **320**
- Frozen held-out test split: **320**
- Authority labels: **USE / ASK / ABSTAIN**
- BeliefWeave exact-action accuracy: **96.88%** (95% bootstrap CI **95.00–98.75%**)
- Temporal + context baseline: **62.50%**
- Retrieval-only baseline: **37.50%**
- BeliefWeave false-personalization rate: **1.56%**
- Retrieval-only false-personalization rate: **62.50%**
- BeliefWeave CPR: **0.0938**
- Retrieval-only CPR: **1.2500**
- McNemar, BeliefWeave vs temporal + context: **p = 1.54e-33**

## Counterfactual response intervention
- Frozen cases: **320**
- BeliefWeave personalization intervention fidelity: **98.44%**
- BeliefWeave behavior intervention fidelity: **98.44%**
- False personalization influence rate: **1.56%**
- Missed personalization rate: **0.00%**

The response renderer is deterministic and controlled; these are mechanism/intervention measurements, not external-LLM quality or human-preference results.

## Authority calibration
- Brier score: **0.1180**
- NLL: **0.3332**
- ECE: **0.2243**
- Adaptive ECE: **0.2100**

The relatively high ECE is a reported limitation: the authority score is not yet a well-calibrated probability.

## Local memory-core scaling
- Horizons: **10 / 100 / 1,000 / 10,000 turns**
- At 10,000 turns: **200 historical rows, 25 active rows, 0 duplicate active single-value slots**
- Recorded local p95 memory update: **~0.79 ms**
- Recorded local p95 authority gate: **~0.008 ms**

These local SQLite numbers are environment-dependent and exclude model/network latency.

## Existing memory/retrieval validation
- Longitudinal slice: **20 users × 100 turns = 2,000 interactions**
- Preference-reversal obsolete-belief retirement: **100.0% PWM vs 0.0% append-only**
- Hard scenarios: **360 / 360 passed**
- Controlled retrieval queries: **120**
- Lexical: Hit@1 **55.0%**, Hit@3 **86.7%**, MRR **0.683**
- Local hybrid: Hit@1 **73.3%**, Hit@3 **95.0%**, MRR **0.835**
- Stale-memory leaks: lexical **0**, hybrid **0**
- OOD observation-router accuracy: **65.79%** on **114** examples
- OOD observation-router ECE: **0.0486**
- At confidence ≥0.70: accuracy **83.78%**, coverage **32.46%**, n=37

## Engineering quality
- Full tests: **129/129 passed**
- Line coverage: **95.69%**
- Stress interactions: **2,000**
- Active exact contradictions: **0**

## Specification robustness
- Second sealed specification audit: **480 cases**.
- V2 exact action accuracy on that audit: **53.33%**.
- Challenge-informed V3 regression accuracy on the same audit: **100.00%**; this is explicitly not independent generalization evidence.
- Metamorphic invariants: **370 checks total across 2 frozen gates**, all passing.
- Benchmark mutation adequacy: **6/6 mutants killed**, mutation score **1.00**.

## Submission-format boundary
- Research manuscript pages: **9**.
- Official NeurIPS template ready: **False**.
- Format blockers: **official neurips_2026.sty is not bundled; paper source does not load neurips_2026.sty; paper source uses custom geometry rather than the official template**.

## External/human evaluation boundary
LongMemEval-v1/v2 and PersonaMem-v1/v3 contracts are documented, but official third-party runs were not executed in this build environment. PersonaMem-v3 already studies over-personalization/restraint, so BeliefWeave does not claim restraint itself as novel. A blind human A/B protocol and analysis package are included, but no participants were run. Therefore **no external benchmark or human-preference score is claimed**.

## Scientific boundary
All reported BeliefShiftBench-v2 authority numbers are synthetic, deterministic, controlled mechanism measurements. They support the internal causal and decision-governance claims tested here, not broad real-user utility or state-of-the-art claims.
