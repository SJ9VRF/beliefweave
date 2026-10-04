# BeliefWeave — novelty audit

## Project identity
**BeliefWeave — Governing When Memory May Change Behavior**  
**Aura Yavary**

A direct web search for the exact project name did not surface an existing AI-memory paper, GitHub project, or arXiv work using **BeliefWeave**. That is useful naming evidence, not a trademark clearance.

## Bottom line
BeliefWeave is **novelty-defensible, not proven SOTA**. The broad problem—long-term personalized memory that updates over time and avoids bad personalization—is now crowded. A credible paper must therefore make a narrow claim and compare against the closest work instead of presenting temporal memory or restraint as new.

The defensible claim is:

> **After retrieval and user-state inference, each remembered belief should face a separate behavioral-authority decision: USE it, ASK the user, or ABSTAIN. BeliefWeave makes that decision explicit, cost-sensitive, auditable, and counterfactually testable.**

## Closest work and what it already covers

| Work | What it already does | Consequence for BeliefWeave |
|---|---|---|
| **OP-Bench + Self-ReCheck (2026)** | Formalizes over-personalization (irrelevance, repetition, sycophancy) and filters retrieved memories before generation. | We **cannot** claim that filtering unnecessary memories or avoiding over-personalization is new. This is the closest conceptual overlap. |
| **PersonaMem / PersonaMem-v3** | Evolving user profiles, personalized responses, omni-platform personal intelligence, and explicit restraint when personalization is inappropriate, outdated, repetitive, or unnecessary. | We **cannot** claim that “knowing when not to personalize” is new. |
| **QUMem (2026)** | Query-conditioned user-state inference over temporally evolving and context-dependent preferences; reports SOTA on PersonaMem/KnowU-Bench. | Temporal/contextual user-state inference is prior work, not our novelty. |
| **Memora (ACL 2026)** | Forgetting-aware evaluation and penalties for reuse of obsolete/invalid memory. | Forgetting and invalid-memory handling are prior work. |
| **Graphiti / Zep** | Temporal validity, provenance, supersession/invalidation, graph retrieval. | Temporal provenance is engineering context, not our novelty. |
| **PAHF (2026)** | Continual personalization, preference drift, pre-action clarification, post-action feedback. | Asking clarifying questions under preference uncertainty is not unique by itself. |
| **LongMemEval / LongMemEval-V2** | Long-horizon retrieval, temporal reasoning, updates, abstention, and agent/environment memory. | They are external evaluation targets; they do not validate BeliefWeave until actually run. |

## Narrow contribution worth defending
BeliefWeave combines five elements at a different decision boundary:

1. **Post-retrieval authority variable.** Relevance and behavioral permission are separate variables.
2. **Three-way per-memory action.** `USE`, `ASK`, or `ABSTAIN` rather than a hidden binary “keep/drop” side effect.
3. **Explicit decision costs.** False personalization, missed personalization, and clarification have visible costs and can be sensitivity-tested.
4. **Counterfactual intervention.** Remove a memory and test whether downstream behavior changes exactly when that memory should have causal authority.
5. **Specification testing.** Frozen challenge manifests, metamorphic invariants, mutation adequacy, and finite-state policy checks supplement ordinary benchmark accuracy.

The novelty is therefore **not a new memory store** and **not a claim to have invented restraint**. It is a governance/evaluation layer over memory use.

## Why the project is interesting to frontier-agent teams
A useful personal agent can retrieve a true fact and still make the wrong decision by using it. Examples include a preference that was true six months ago, a private or third-party fact, a context-specific constraint, a contradicted belief, or an inference the user never confirmed. The failure is downstream of retrieval. That makes behavioral authority relevant to personal agents, proactive agents, memory systems, and tool-using agents where a remembered belief can change an action rather than just wording.

## Evidence already present
- BeliefShiftBench-v2 frozen held-out controlled test.
- Counterfactual response intervention.
- Calibration and risk/coverage analysis.
- Cost and threshold sensitivity.
- Component ablations and fault injection.
- 10K-turn local memory-core scaling.
- 30-seed within-specification stability.
- Unseen-composition and sealed-specification challenges that exposed real specification gaps.
- Metamorphic invariants, mutation adequacy, and finite-state authority-policy checking.
- Transaction, privacy-erasure, provenance-integrity, and concurrency tests for the implementation.

## Evidence still required before a SOTA claim
A serious **SOTA** claim requires the system to beat strong contemporary methods on a shared external benchmark under the same evaluation protocol. That has **not** happened yet. Required evidence includes:

1. OP-Bench / Self-ReCheck comparison.
2. PersonaMem-v3 end-to-end personalized-response evaluation.
3. LongMemEval and/or Memora memory/update evaluation.
4. QUMem and strong temporal-memory baselines where their code/evaluation contract permits fair comparison.
5. Blind human judgments of downstream personalization quality, intrusiveness, and whether clarification was preferable.

Until those runs exist, use **“novelty-defensible”**, **“SOTA-aligned evaluation”**, or **“controlled mechanism evidence”**—not “proven SOTA.”

## Claim language
**Defensible:** “explicit post-retrieval behavioral authority for remembered user information,” “three-way memory-use governance,” “cost-sensitive authority,” “counterfactual memory-intervention evaluation,” “controlled synthetic evidence.”

**Do not use yet:** “first system to know when not to personalize,” “proven SOTA,” “best memory system,” “human-validated,” or external-benchmark superiority.
