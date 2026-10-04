# External evaluation

BeliefWeave ships executable adapters/contracts without inventing third-party scores. The current external targets are **LongMemEval-v1**, **LongMemEval-V2**, **PersonaMem-v1**, and especially **PersonaMem-v3**.

## Why these targets
LongMemEval tests long-horizon memory abilities such as temporal reasoning, updates, and abstention. LongMemEval-V2 extends the setting to agentic environment experience. PersonaMem evaluates evolving user profiles and personalized responses. PersonaMem-v3 is the closest current overlap because it explicitly measures **over-personalization and restraint**. BeliefWeave therefore does **not** claim that restraint itself is novel. Its narrower contribution is an explicit per-memory `USE / ASK / ABSTAIN` authority decision, a cost-sensitive objective, and counterfactual intervention diagnostics.

## What is implemented
- `longmemeval_adapter.py`: evidence-session retrieval contract for LongMemEval-v1.
- `personamem_adapter.py`: provider-neutral PersonaMem-v1 request materialization.
- `public_benchmark_registry.json`: frozen metadata and execution boundary for v1/v2/v3 targets.

## What is not claimed
No LongMemEval, LongMemEval-V2, PersonaMem-v1, or PersonaMem-v3 benchmark score is reported in this release. Those runs require official third-party bytes and, for response-quality evaluation, external model/evaluator execution.
