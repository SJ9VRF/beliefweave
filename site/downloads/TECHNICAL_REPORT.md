# BeliefWeave: Governing When Memory May Change Behavior

## Abstract
Most assistant-memory prototypes treat personalization as retrieval over stored text. This project instead models personal memory as temporal state estimation over an evolving user. The implementation separates raw events, grounded observations, typed memories, and a materialized current user state. Each memory carries provenance, confidence, temporal validity, context, lifecycle status, and conflict/supersession relationships. The system includes user controls, temporary-state expiry, conservative conflict semantics, query-aware retrieval, locally trained routing/conflict components, longitudinal simulation, ablations, robustness tests, and a live inspection UI.

We release **MemWorldBench**, a controlled package with 100,000 generated interactions from 1,000 simulated users plus 360 hard scenarios. A quick executable slice uses 2,000 interactions for reproducible CI-scale evaluation. In controlled preference-reversal probes, the temporal world model retires obsolete beliefs while an append-only baseline does not. The repository also reports a deliberately harder paraphrase-family test on which the lightweight local observation router reaches only 65.8%, identifying semantic extraction as the main current model-quality bottleneck. All measurements are synthetic or local engineering validation; no real-user performance claim is made.

## 1. Problem formulation
The useful question for personal AI is not only “what did the user say?” but:

**What is currently believed about the user, why, under which context, with what confidence, and until when?**

We represent interaction history as observations over a changing latent user state rather than as a single text store.

`interaction → observation → write decision → typed memory → temporal/conflict update → current user state → retrieval`

## 2. Representation
A memory stores subject, predicate, value, memory type, source type, confidence, source event IDs, creation/update time, validity interval, stability, importance, context scope, lifecycle status, supersession/conflict links, retrieval statistics, verification and correction count.

A crucial distinction is maintained throughout:

`Event ≠ Observation ≠ Memory ≠ Current State`

This makes provenance, debugging and temporal evaluation explicit.

## 3. Memory write and extraction
The baseline write policy uses memory type, explicitness, confidence and temporality. A locally trained TF–IDF/logistic-regression router expands coverage for additional self-statements, while deterministic slot extraction prevents the model from inventing unsupported values.

The system guards against common attribution failures such as third-party statements, role-play/hypothetical language and explicit “don’t remember/save this” instructions.

## 4. Temporal state and conflict semantics
Memory is additive by default. Multiple goals, likes, constraints, routines and commitments may coexist. The system only supersedes a belief when there is evidence for replacement, including:
- opposite preference polarity about the same/related object
- explicit correction of a related value
- update to a single-valued state attribute
- temporal expiry

Context-scoped preferences coexist. Preference-vs-constraint tension is represented as an apparent conflict rather than destructive overwrite.

This conservative policy was introduced after a learned conflict classifier incorrectly attempted to supersede an unrelated preference with a goal during OOD testing. Learned conflict classification is now structurally gated and cannot overwrite incompatible memory families.

## 5. User control and deletion
Users can inspect, correct and delete memories. Retrieval and current-state materialization use only ACTIVE memories. The engine supports two explicit deletion modes: soft deletion keeps a tombstone excluded from state/retrieval, while hard forgetting atomically purges the selected memory row and its source events, then repairs surviving sibling provenance or purges siblings that would otherwise become source-less. This prototype does not claim production-grade privacy; encryption, authorization, legal retention, tenant isolation and comprehensive PII policy remain out of scope.

## 6. Retrieval
The included retriever is entirely local and reproducible. It combines word/character TF–IDF similarity with small transparent synonym expansions plus confidence, importance, recency, stability and context priors. This avoids pretending that an unavailable external embedding model was used while still providing a stronger baseline than raw lexical overlap.

## 7. MemWorldBench
The repository contains:
- 1,000 synthetic users × 100 turns = **100,000 generated interactions**
- 360 controlled hard scenarios, 60 per category
- a 2,000-interaction executable longitudinal benchmark slice
- controlled ablations against append-only and latest-predicate baselines
- OOD paraphrase-family tests
- a 2,000-interaction stress/invariant run

Hard-scenario categories include preference reversal, context dependence, temporary states, explicit corrections, third-party attribution and multilingual memory.

## 8. Results
### Controlled longitudinal slice
From `results/benchmark.json`:
- final current-food accuracy: 100% for both PWM and append-only on the terminal probe, demonstrating that this metric alone is not discriminative
- old-belief retirement at reversal: 100% PWM vs 0% append-only
- mean active stale food memories: 0
- recorded mean ingest latency: ~1.82 ms on the latest local reproduction

### Ablations
From `results/ablations.json`:
- reversal retirement: append-only 0%, latest-predicate 0%, full PWM 100%
- temporary expiry: append-only 0%, latest-predicate 0%, full PWM 100%

### Hard scenarios
All 360 generated deterministic scenarios pass. This is regression coverage, not a broad generalization score.


### Retrieval relevance
On a 120-query controlled benchmark with shuffled insertion order, context-sensitive cases, distractors, and superseded-memory probes, the local hybrid retriever reaches **73.3% Hit@1**, **95.0% Hit@3**, and **0.835 MRR**, compared with **55.0% Hit@1**, **86.7% Hit@3**, and **0.683 MRR** for the lexical baseline. Both record **0 stale-memory leaks**. These are controlled relevance measurements, not a substitute for human judgments of downstream response utility.

### Linguistic distribution shift
The observation router reaches **65.8%** on held-out paraphrase families (`results/ood_robustness.json`). Per-class weakness is largest for commitment and routine language. This is the clearest current evidence that a stronger semantic encoder or LLM-based grounded extractor is needed.

### Stress validation
A recorded 2,000-interaction run completes with 0 active exact likes/dislikes contradictions. Throughput is stored in `results/stress_test.json` and intentionally not frozen into the manuscript because it is environment-dependent; it is a prototype measurement, not a production benchmark.

## 9. Failure-driven design changes
Several failures directly changed the architecture:
1. **Historical-time expiry bug:** state evaluation initially mixed simulated timestamps with wall-clock time. State/retrieval are now explicitly time-aware.
2. **Third-party poisoning:** “My friend says I love sushi” risked first-person memory. Attribution guards and regression tests were added.
3. **Classifier overwrite:** a learned conflict model mislabeled an unrelated preference+goal pair. Structural safety gates now bound learned authority.
4. **Multi-valued collapse:** same-predicate values such as “I love sushi” and “I love jazz” could be mistaken for drift. Additive-by-default semantics now preserve both.
5. **Role-play leakage:** hypothetical preference text could enter memory through the rule baseline. Role-play guards now precede extraction.

## 10. Limitations
The current semantic layer is intentionally lightweight. The router generalizes imperfectly to unseen phrasing; the retriever uses local TF–IDF rather than a strong embedding model; multilingual support is narrow; confidence calibration has only been measured on synthetic OOD paraphrases—not on human labels; the simulator is not a realistic user model; there is no human-subject evaluation; privacy/security controls are prototype-level.

## 11. Next empirical milestone
The most scientifically meaningful next iteration is not more synthetic scale. It is:
1. independently authored longitudinal conversations
2. multiple human annotators + adjudication
3. learned grounded extraction with calibrated uncertainty
4. downstream response-utility evaluation
5. stale-memory-harm and unsupported-inference metrics
6. privacy/deletion verification under adversarial replay
7. stronger multilingual and semantic-retrieval baselines

That study would test whether the state-estimation formulation improves real interaction quality rather than only controlled memory mechanics.

## 12. Reproducible presentation artifacts
`paper/figures/` contains PNG/PDF figures generated directly from result JSON, and `paper/RESULTS_TABLES.md` contains reproducible tables. Both are regenerated by `./scripts/reproduce_all.sh`.

## Paper-grade authority evaluation

The current primary evaluation is `benchmark/paper_grade_eval.py`. It replaces the earlier binary 180-case authority probe as the main paper evidence with a three-action benchmark: **USE / ASK / ABSTAIN**. BeliefShiftBench-v2 contains 640 deterministic cases split into 320 development and 320 frozen test cases across eight authority failure families.

The evaluator reports exact action accuracy, binary use accuracy, false personalization, CPR, use precision/recall, action rates, 1,000-sample bootstrap intervals, paired exact McNemar comparisons, calibration metrics, risk–coverage, threshold sensitivity, cost sensitivity, and leave-one-signal-out ablations.

`benchmark/behavior_intervention_eval.py` adds a deterministic response-level causal check. `benchmark/error_propagation_eval.py` injects staged faults to separate extraction/source, lifecycle-state, context, conflict, authority, and generation failures. `benchmark/horizon_scaling.py` tests the local memory substrate through 10,000 turns.

The repository also contains external LongMemEval and PersonaMem adapters plus a blind human-evaluation kit. They are deliberately shipped without fabricated results; third-party/model/human scores only become reportable after actual execution.

## Production policy assurance

Paper experiments retain frozen V1/V2 authority variants. The engine's default governed-recall policy is V3, and API responses expose the gate version that made the decision. An exhaustive enumeration of a declared 9,600-state policy model checks status, temporal validity, source class, confidence, verification, provenance, privacy sensitivity, context relationship, and conflict. Across six stated invariants the audit finds 560 violations in V1, 146 in V2, and 0 in V3. This is finite verification of that discrete model, not formal verification of the full Python program.

A 50-user privacy-erasure regression checks deletion of source events, retention of unrelated evidence, repair of multi-source provenance, absence of deleted-event leakage in complete exports, and database integrity. All 50 multi-source cases are repaired and no export leakage is observed. A separate single-process, 12-thread SQLite stress executes 480 end-to-end ingests with zero errors and a passing integrity check; recorded p95 latency is about 229 ms in that environment. The concurrency result is explicitly not a distributed or multi-process production benchmark.
## Runtime profiles and observability

The install surface is split deliberately. `pip install beliefweave` runs the deterministic rule-based extractor, lexical retriever, and conflict resolver with no third-party runtime dependency. `beliefweave[ml]` enables the checked local TF-IDF/router/conflict components. `runtime_capabilities()` reports the active path explicitly.

`PersonalMemoryEngine` also accepts an optional observer callback for operation-level telemetry. Observer events carry counts, gate/component versions, event or memory identifiers, and a short one-way user correlation key; they exclude raw user text, memory values, and context. Observer failures are isolated from memory semantics. This is a narrow property of the reference runtime, not a claim about host-application logging compliance.

