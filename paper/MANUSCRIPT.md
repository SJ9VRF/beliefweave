# BeliefWeave: Governing When Memory May Change Behavior

## Abstract
Long-horizon personal assistants need more than retrieval over prior text: they need an explicit, updateable estimate of what is currently true about a user. We introduce a **BeliefWeave** architecture that separates raw interaction events, grounded observations, typed memories, and a materialized current user state. Memories carry provenance, confidence, temporal validity, context scope, lifecycle status, and conflict/supersession links. The implementation combines conservative state-update rules with lightweight learned routing components, user-visible inspection and deletion controls, local retrieval, and controlled longitudinal evaluation. On a synthetic 2,000-interaction benchmark slice, PWM retires obsolete beliefs at preference reversal while an append-only baseline does not. A 120-query controlled retrieval suite shows improved ranking over lexical retrieval, while an out-of-distribution paraphrase test exposes the main current weakness: the local observation router reaches only 65.8% accuracy. Selective persistence at confidence ≥0.70 raises accuracy to 83.8% while covering 32.5% of examples. These experiments validate system mechanics and evaluation infrastructure, not real-user utility. We release the code, synthetic benchmark, failure analysis, and reproducible evaluation package to support further study of temporal personal memory.

## 1. Introduction
Memory in a personal assistant is frequently implemented as stored text plus similarity search. That representation answers *what was said before*, but does not directly answer a more useful question: **what should the system currently believe about the user, under which context, and why?** Personal preferences change, constraints expire, goals coexist, corrections override earlier inferences, and statements about third parties or role-play should not silently become personal facts.

We formulate personal memory as **temporal belief-state maintenance over an evolving user**. The system maintains a traceable path from event to observation to memory to current state, with explicit validity and provenance. The design intentionally favors conservative persistence: when evidence is ambiguous, the system can abstain instead of creating a durable memory.

### Contributions
1. A temporal, typed memory architecture that distinguishes event history from current user state.
2. Additive-by-default conflict semantics with explicit supersession, expiry, provenance, and user control.
3. MemWorldBench, a controlled longitudinal benchmark package plus hard scenarios, OOD paraphrases, retrieval relevance probes, and stress tests.
4. A reproducible failure-driven evaluation workflow in which discovered attribution, timing, conflict, and deletion bugs become regression tests.
5. An explicit scientific boundary separating synthetic engineering validation from claims about real-user usefulness or trust.

## 2. Problem formulation
Given interactions \(O_{1:t}\), the system maintains a current estimate of user state \(S_t\):

\[
P(S_t \mid O_{1:t})
\]

The implementation is not a fully probabilistic latent-state model; rather, this formulation motivates the separation between evidence, durable beliefs, and current state. Each memory record contains a value plus metadata required to decide whether it is active, relevant, trustworthy, context-compatible, or superseded.

The core pipeline is:

`interaction → observation → write decision → typed memory → temporal/conflict update → current user state → retrieval`

## 3. Architecture
### 3.1 Event and observation layers
Raw events are immutable provenance records. Candidate observations are extracted separately and may be rejected before persistence. Guards suppress third-party attribution, role-play/hypothetical statements, and explicit instructions not to remember content.

### 3.2 Typed memory
Memory records include type, source, confidence, validity interval, context scope, lifecycle status, source-event IDs, and conflict/supersession relations. Supported categories include preferences, goals, constraints, routines, commitments, facts, and temporary state.

### 3.3 Temporal semantics
Expiry is evaluated relative to an explicit evaluation time, preventing simulated historical events from being compared incorrectly to the wall clock. Temporary memories can automatically become inactive after their validity window.

### 3.4 Conflict and update policy
Memory is **additive by default**. Multiple goals or preferences may coexist. Destructive supersession requires structural compatibility and evidence of replacement, such as opposite polarity for the same object, explicit correction, or an update to a single-valued state attribute. Learned conflict classification is bounded by structural safety gates.

### 3.5 Retrieval
The local retriever combines word/character TF–IDF similarity with transparent synonym expansion and priors for confidence, importance, recency, stability, validity, and context. This is intentionally local and reproducible; no unavailable embedding service is implied.

### 3.6 User control
Users can inspect, correct, soft-delete, or hard-forget memories. Soft deletion retains a tombstone excluded from retrieval/state. Hard forgetting purges the memory row and its source events in this prototype.

## 4. Evaluation
The evaluation package includes a 100,000-interaction generated release dataset, a 2,000-interaction executable benchmark slice, 360 hard scenarios, OOD paraphrase-family tests, a 120-query retrieval suite, controlled ablations, API/regression tests, and a stress/invariant run.

All measured values below are regenerated from `results/*.json`; see `paper/REPRODUCIBLE_SUMMARY.md`.

## 5. Results
### 5.1 Temporal belief retirement
On the controlled preference-reversal probe, PWM retires the obsolete belief in 100% of evaluated cases, versus 0% for the append-only baseline. Temporary-state expiry similarly succeeds in the controlled ablation where append-only and latest-predicate baselines fail.

### 5.2 Retrieval relevance
On 120 controlled queries, the hybrid local retriever reaches 73.3% Hit@1 and 0.835 MRR, compared with 55.0% Hit@1 and 0.683 MRR for the lexical baseline. Both systems record zero stale-memory leaks in this suite.

### 5.3 Distribution shift and selective persistence
The local observation router reaches 65.79% accuracy on 114 held-out paraphrase examples. Calibration evaluation gives ECE 0.0486 on this synthetic OOD set. At a confidence threshold of 0.70, accepted predictions reach 83.78% accuracy at 32.46% coverage. This supports an abstention-oriented write policy: ambiguous candidates should not automatically become durable memories.

### 5.4 Engineering validation
The current suite contains 129 regression/safety/API/invariant/packaging tests with 95.69% line coverage. A 2,000-interaction stress run records zero active exact likes/dislikes contradictions. Throughput measurements are local prototype measurements only.

## 6. Failure-driven design
Several failures changed the system design. Historical-time expiry initially mixed simulation time with wall-clock time. Third-party statements could be misattributed to the user. A learned conflict classifier attempted to overwrite an unrelated preference with a goal. Same-predicate multi-valued preferences risked destructive collapse. Role-play could leak into memory. Release auditing later found a calibration-bin implementation bug that overstated ECE. Each issue was fixed and converted into either a regression test or release-integrity check.

## 7. Limitations
This prototype does not establish real-user personalization quality. The semantic router is lightweight and weak under linguistic distribution shift. Calibration has been measured only on a synthetic OOD paraphrase set, not human labels. Multilingual coverage is narrow. The synthetic user simulator does not model realistic human preference dynamics. There is no human-subject longitudinal study, no independently annotated benchmark, no production authorization/encryption layer, and no formal privacy or legal-retention review.

## 8. Next empirical study
The next meaningful study should use independently authored longitudinal conversations, multiple annotators with adjudication, stronger grounded extraction, and downstream response-utility judgments. Primary outcomes should include stale-memory harm, unsupported-inference rate, correction recovery, retrieval utility delta, temporal consistency, and user-perceived intrusiveness. A successful result would need to show that state-based memory improves interaction quality—not merely controlled bookkeeping.

## 9. Reproducibility
Run:

```bash
python -m pip install -e '.[dev,ml,demo]'
./scripts/reproduce_all.sh
```

The pipeline regenerates evaluation JSON, tables, figures, dashboard assets, publication summary, and release audit checks. `RETRAIN=1` additionally retrains serialized local models.

## Release contracts and integrity

The release also carries machine-readable OpenAPI, test-summary, coverage, database-integrity, static-security-guardrail, and local runtime-profile artifacts. These are engineering evidence, not substitutes for human-subject evaluation or a formal security/privacy review.
