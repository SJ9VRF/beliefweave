# Reproducible Results Tables

Generated from checked-in JSON outputs by `scripts/generate_results_tables.py`.

## Temporal state ablation

| System | Preference reversal retirement | Temporary expiry |
|---|---:|---:|
| Append-only | 0.0% | 0.0% |
| Latest predicate | 0.0% | 0.0% |
| BeliefWeave | 100.0% | 100.0% |

## Retrieval

| Retriever | Hit@1 | Hit@3 | MRR | Stale leaks |
|---|---:|---:|---:|---:|
| Lexical baseline | 55.0% | 86.7% | 0.683 | 0 |
| Local hybrid | 73.3% | 95.0% | 0.835 | 0 |

Controlled retrieval cases: **120**.

## Robustness / regression

| Evaluation | Result |
|---|---:|
| Hard scenarios | 360/360 |
| OOD observation router | 65.8% (114 examples) |
| Hybrid conflict controlled challenge | 100.0% |
| Adversarial engine checks | 5/5 |
| Stress active exact contradictions | 0 |
| Stress interactions | 2,000 |

## Longitudinal slice

- users: **20**
- turns/user: **100**
- interactions: **2,000**
- final current-food accuracy: **100.0%**
- old-belief retirement at reversal: **100.0%**
- mean active stale food memories: **0**

> Scientific boundary: these are synthetic, deterministic, template-controlled, or local stress measurements. They are engineering/research-prototype evidence, not real-user performance claims.

## BeliefShiftBench-v2 held-out authority results

| Policy | Exact action | False personalization | CPR |
|---|---:|---:|---:|
| Retrieval-only | 37.5% | 62.5% | 1.250 |
| Temporal + context | 62.5% | 37.5% | 0.750 |
| Cost-sensitive authority | 83.1% | 0.0% | 0.105 |
| BeliefWeave | 96.9% | 1.6% | 0.094 |
