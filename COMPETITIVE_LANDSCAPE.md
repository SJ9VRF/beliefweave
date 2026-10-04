# Competitive landscape — behavioral authority for personal AI

**Project:** BeliefWeave — Governing When Memory May Change Behavior  
**Author:** Aura Yavary

## The nearest question
Most memory work asks one of three questions: *what should be stored?*, *what should be retrieved?*, or *what is the user's current state?* BeliefWeave targets the next decision: **given a retrieved belief, should it be allowed to influence the current behavior?**

## Closest systems

| System / benchmark | Primary target | Closest overlap | BeliefWeave boundary |
|---|---|---|---|
| OP-Bench / Self-ReCheck | Over-personalization; memory filtering | Decides whether retrieved memory should be reconsidered/filtered | Explicit auditable `USE/ASK/ABSTAIN`, explicit costs, causal intervention, spec testing |
| PersonaMem-v3 | Holistic personal intelligence + restraint | Avoid inappropriate/outdated/unnecessary personalization | Memory-level authority decision and intervention diagnostics rather than only end-response performance |
| QUMem | Query-conditioned current user state | Temporal/context applicability and conflicting preferences | Authority begins **after** state inference/retrieval |
| Memora | Remember/forget obsolete information | Invalidated memories should not be reused | Adds permission-to-influence and clarification/abstention decision |
| Graphiti/Zep | Temporal context graph + provenance | Validity windows, provenance, deletion propagation | Uses those signals as inputs to an explicit behavioral decision |
| PAHF | Continual preference adaptation | Clarification and preference drift | Formalizes clarification as one action in a per-memory authority policy |
| LongMemEval | Long-horizon memory competence | Updates, temporal reasoning, abstention | External competence benchmark; not the same target variable |

## What would falsify the novelty/value claim
The project becomes substantially less interesting if a strong existing method such as Self-ReCheck or an LLM authority judge matches the `USE/ASK/ABSTAIN` policy, intervention fidelity, and cost-risk tradeoff without BeliefWeave's explicit state. That comparison should be treated as a priority experiment, not avoided.

## Hiring-manager reading
The strongest signal in this project is not the number of artifacts. It is the research judgment to narrow the claim after finding overlapping work, preserve negative results, and turn a vague personalization failure into a testable decision surface with explicit failure modes and invariants.
