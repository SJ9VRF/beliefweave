# Experiments and interpretation

## Reproduction

```bash
./scripts/reproduce_all.sh
```

This executes regression tests, the controlled longitudinal benchmark, 360 hard scenarios, OOD routing evaluation, controlled ablations, and dashboard generation.

## What the results establish

The deterministic and template-controlled evaluations show that the implementation satisfies the intended memory lifecycle semantics under the scenarios covered by the tests: preference reversal, expiry, context dependence, explicit correction, attribution guards, and multilingual canonicalization.

## What the results do not establish

They do not establish real-user usefulness, broad semantic robustness, calibrated personalization benefit, privacy acceptance, or generalization to unconstrained conversation. The OOD router score is intentionally reported to expose this gap.

## Next empirical study

A publishable follow-up should use independently authored longitudinal dialogues, multiple annotators, blinded system comparison, downstream response-utility judgments, calibration analysis, privacy review, and pre-registered primary outcomes.
