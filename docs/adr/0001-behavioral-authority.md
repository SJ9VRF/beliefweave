# ADR 0001 — Separate retrieval relevance from behavioral authority

## Decision
A retrieved memory is not automatically allowed to change behavior. Retrieval and authority are separate stages. The authority stage emits one of three actions: `USE`, `ASK`, or `ABSTAIN`.

## Why
A memory can be topically relevant while still being stale, weakly inferred, context-specific, contradicted, privacy-sensitive, or otherwise unsafe to act on. Folding that judgment into retrieval makes failures hard to localize and impossible to audit cleanly.

## Consequences
- Retrieval quality and behavioral authority are evaluated separately.
- Authority decisions carry explicit reasons and are versioned.
- Counterfactual memory removal can test whether a memory had appropriate causal influence.
- The design adds a policy boundary that must itself be calibrated and evaluated.
