# Evaluation protocol

## Primary controlled study

Run `python benchmark/paper_grade_eval.py`.

BeliefShiftBench-v2 has a fixed 320-case development split and 320-case test manifest. The primary endpoint is exact USE/ASK/ABSTAIN accuracy on the frozen test split. Secondary endpoints are false personalization, CPR, use precision/recall, and action rates.

Uncertainty: 1,000-sample bootstrap confidence intervals. Paired deterministic comparisons: exact McNemar test.

## Sensitivity and mechanism analysis

The primary script also emits threshold sweeps, cost sweeps, risk–coverage points, Brier/NLL/ECE/adaptive-ECE calibration statistics, and leave-one-signal-out authority ablations.

## Counterfactual behavior

`python benchmark/behavior_intervention_eval.py` removes candidate memory and measures whether personalized content/behavior changes exactly when the gold action requires it. The response renderer is deterministic and is explicitly not an LLM-quality evaluation.

## Fault propagation

`python benchmark/error_propagation_eval.py` injects controlled source/confidence, lifecycle, context, conflict, authority, and generation faults. This estimates sensitivity to staged corruption, not production fault frequency.

## Long-horizon scaling

`python benchmark/horizon_scaling.py` tests the local persistence/update/gating substrate at 10, 100, 1,000, and 10,000 turns with a 2% durable-memory rate. Runtime values are environment-dependent and exclude model/network latency.

## External evaluation

`benchmark/external/` contains LongMemEval and PersonaMem adapters. No external score should be added to the paper unless the official third-party data and required reader/evaluator path have actually run. Human evaluation follows `human_eval/PROTOCOL.md`; no human result may be inferred from synthetic data.
