# BeliefShiftBench-v2

BeliefShiftBench-v2 evaluates **behavioral authority after retrieval**: given a retrieved personal memory and current context, should the system **USE**, **ASK**, or **ABSTAIN**?

## Construction

- 640 deterministic controlled cases
- 320 development cases
- 320 frozen held-out test cases
- 8 failure families: valid explicit, valid observed, stale, context mismatch, weak inference, unresolved conflict, inactive/superseded, medium authority
- frozen test IDs: `benchmark/beliefshift_v2_test_manifest.json`

This is author-constructed synthetic data. The frozen split limits direct item-level tuning but does not remove construction bias.

## Main metrics

- exact three-way action accuracy
- binary use accuracy
- false-personalization rate
- USE precision/recall
- ASK / ABSTAIN rate
- Counterfactual Personalization Regret (CPR)
- personalization and behavior intervention fidelity

## Statistical protocol

Main policy metrics use 1,000-sample bootstrap 95% confidence intervals. Deterministic policy comparisons use paired exact McNemar tests over per-case action correctness. Threshold and cost sensitivity are reported separately from the pre-specified default policy.

## Baselines

Retrieval-only, confidence-only, provenance-only, temporal+context filtering, metadata score without hard vetoes, cost-sensitive authority, and oracle.

## Scientific boundary

The benchmark isolates temporal/provenance/context/conflict mechanisms. It is not independent human annotation and is not evidence of cross-paper SOTA. External adapters for LongMemEval and PersonaMem are included separately and are only reportable after real runs.
