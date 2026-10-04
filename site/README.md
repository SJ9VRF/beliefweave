# BeliefWeave

**Governing When Memory May Change Behavior**  
**Aura Yavary**

BeliefWeave studies a narrow question in long-term personalization: **when should a remembered belief be allowed to change an AI system's behavior?**

Retrieval relevance is not the same as behavioral authority. A memory can be relevant and still be stale, context-specific, weakly inferred, contradicted, superseded, or otherwise inappropriate to use. BeliefWeave keeps those decisions separate: retrieve first, then route each candidate belief to **USE**, **ASK**, or **ABSTAIN**.

The fastest review path is `site/index.html`. The research paper is `paper/BELIEFWEAVE.pdf`.

## Main controlled result

The primary paper evaluation is **BeliefShiftBench-v2**, a deterministic 640-case benchmark with 320 development cases and a frozen 320-case test manifest. Gold labels are exact three-way actions rather than a binary use/not-use label.

| Policy | Exact USE/ASK/ABSTAIN | False personalization | CPR ↓ |
| --- | ---: | ---: | ---: |
| Retrieval-only | 37.5% | 62.5% | 1.250 |
| Temporal + context | 62.5% | 37.5% | 0.750 |
| Cost-sensitive authority | 83.1% | **0.0%** | 0.105 |
| **BeliefWeave** | **96.9%** | 1.6% | **0.094** |

BeliefWeave's exact-action bootstrap 95% CI is **95.0–98.8%**. Against the temporal+context baseline, the paired exact McNemar comparison has 110 BeliefWeave-only correct cases and zero baseline-only correct cases. These are controlled synthetic results; they are not an external SOTA claim.

A controlled response-level intervention suite reports **98.4% personalization-intervention fidelity**. Fault injection separately measures how extraction/source, lifecycle-state, context, conflict, authority, and generation failures propagate downstream.

## Formal view

Let `p` be the probability that a retrieved memory should be allowed to personalize the current decision. With explicit costs for false personalization, missed personalization, and clarification:

```text
L(USE)     = (1 - p) * C_false_personalization
L(ABSTAIN) = p * C_missed_personalization
L(ASK)     = C_clarification
```

A Bayes-style authority policy chooses the lowest expected-cost action. The repository includes both this explicit cost-sensitive policy and the threshold policy used by the current BeliefWeave prototype.

## What I built

- typed temporal memories with provenance, confidence, context, validity, lifecycle state, supersession, and conflict links;
- a current-user-state layer that keeps historical evidence separate from active beliefs;
- retrieval followed by an explicit authority decision;
- correction, soft deletion, hard forgetting, and memory inspection;
- structural guards around learned observation/conflict components;
- a FastAPI service, CLI, interactive browser demo, paper, benchmark pages, and reproducible evaluation scripts.

The implementation is deliberately inspectable: I can trace why a memory was written, why it was retrieved, and why it was or was not allowed to influence behavior.

## Installation profiles

The core runtime is intentionally dependency-light:

```bash
pip install beliefweave
```

That path uses the rule-based extractor, lexical retriever, and deterministic conflict resolver. This is also the **default even when ML libraries happen to be installed**, so environment drift cannot silently change runtime semantics. Optional local ML components are enabled with:

```bash
pip install 'beliefweave[ml]'
```

The engine exposes `runtime_capabilities()` so applications can record which path is active instead of inferring it from the environment. Timestamps entering the engine are validated and canonicalized to aware UTC ISO-8601 before persistence or idempotency hashing; invalid time values fail fast. The release pipeline also installs the wheel in a clean virtual environment with `--no-deps` and runs an ingest/state smoke test.

For operational telemetry, applications may pass an `observer` callback to `PersonalMemoryEngine`. Events contain operation names, counts, gate version, a short HMAC-keyed user correlation token, and component mode; they deliberately exclude raw user text, memory values, and context. Observer failures are isolated from memory semantics.

## Public API

New integrations use the project name directly:

```python
from beliefweave import PersonalMemoryEngine

engine = PersonalMemoryEngine("beliefweave.db")
engine.ingest("user-1", "I prefer aisle seats", idempotency_key="req-1")
for item in engine.governed_recall("user-1", "book my next flight"):
    print(item["gate"].action, item["gate"].reason)
```

User corrections use `engine.correct_memory(...)`: they create a new user-verified memory and source event, then supersede the previous version instead of silently mutating history. Hard-forget receipts retain only the minimum replay tombstone: raw idempotency keys are never persisted, and request/event metadata is scrubbed after deletion.

The historical `pwm` namespace remains available only so frozen experiments and older artifacts continue to reproduce. The short rationale for the main design boundaries is in `docs/ARCHITECTURE_DECISIONS.md`.

## User data inventory and erasure

`export_user_data()` now inventories persisted control metadata as well as events, memories, and current state. Idempotency receipts expose only stored digests and scrubbed tombstone fields; raw idempotency keys are never persisted.

`purge_user_data()` makes the deletion trade-off explicit. Full erasure removes events, memories, and receipts. Guarded erasure retains only hashed, scrubbed replay tombstones so stale client retries cannot recreate deleted content. The latter is intentionally *not* described as complete erasure because minimal user-scoped control metadata remains.

Operational correlation identifiers are HMAC-derived rather than plain hashes. Without a caller-supplied key, the correlation secret is random per engine instance; stable cross-process telemetry requires an explicit secret.

Process-level SQLite assurance now includes independent writer processes and a forced interpreter exit with an uncommitted event+memory transaction. The recovered database contains no partial rows and passes the integrity audit. This is evidence for the checked reference runtime, not a distributed durability claim.

## Evaluation suite

The paper-grade local suite now includes:

- **BeliefShiftBench-v2:** 640 controlled cases, frozen 320-case test split, eight failure families;
- **stronger metadata baselines:** retrieval-only, confidence-only, provenance-only, temporal+context, metadata scoring, cost-sensitive authority, oracle;
- **statistics:** 1,000-sample bootstrap CIs and paired exact McNemar tests;
- **sensitivity:** threshold grid, cost grid, risk–coverage analysis;
- **calibration:** Brier score, NLL, ECE, adaptive ECE;
- **ablation:** remove time, context, provenance, verification, conflict, or lifecycle status;
- **counterfactual behavior:** memory-removal intervention fidelity;
- **fault injection:** stage-wise error propagation;
- **scaling:** 10 / 100 / 1k / 10k turn memory-core stress tests;
- **generalization audit:** unseen-composition challenge plus 30-seed stochastic stability;
- **submission hygiene:** Croissant core + RAI metadata, local structural validator, human-study power planning, and a NeurIPS pre-submission checklist;
- **supporting diagnostics:** retrieval Hit@k/MRR, temporal reversal/expiry, OOD paraphrases, hard scenarios, API/schema/invariant tests.

## External benchmark and human-evaluation boundary

The repo includes executable adapters for **LongMemEval** and **PersonaMem** under `benchmark/external/`, but it does not bundle third-party datasets or fabricate scores. The LongMemEval harness measures evidence-session recall using the official `answer_session_ids`; official answer-quality scoring still requires a reader model and the benchmark evaluator. The PersonaMem harness builds provider-neutral evaluation requests.

`human_eval/` contains a blind comparison protocol, annotation schema, local collection form, and analysis script. **No human result is claimed** until a real study is recruited and run.

This boundary matters: the current paper supports a controlled mechanism claim, not a claim that BeliefWeave is already the best real-world personalized memory system.

## Generalization audit

The frozen v2 test split is honest but not template-independent: development and test share the same eight scenario families. To make that weakness measurable, V17 adds a separate **unseen-composition challenge** with structural combinations absent from v2. The original gate reaches **75.0% exact action accuracy** across 2,880 decisions. Its failures are concentrated in three unsupported conditions: future-effective beliefs, scoped memories when the current context is unknown, and high-confidence synthetic evidence.

A separate `DecisionAwareBeliefGateV2` patches those three cases and reaches 100% on the same challenge. That number is **not** treated as independent generalization evidence because the patch was written after observing the challenge failures. It exists as a regression target.

A complementary 30-seed stochastic suite perturbs confidence, provenance, lifecycle state, and context within pre-specified label-safe ranges. Across 12,000 decisions per policy, the original BeliefWeave gate remains at 100% exact accuracy; this measures within-specification stability, not distribution-shift generalization.

Sensitivity analysis is intentionally unflattering where appropriate: only 8 of 168 threshold settings land within one percentage point of the best exact accuracy, and only 20% of the 60 tested cost settings simultaneously exceed 80% exact accuracy and stay at or below 5% false personalization. The cost trade-off is therefore a real modeling choice, not a decorative hyperparameter.

## Known weakness

The lightweight observation router reaches only **65.8%** accuracy on held-out paraphrase families. That is the clearest upstream weakness. The new fault-injection analysis makes the consequence explicit: a strong authority policy cannot repair a belief that was extracted or attributed incorrectly.

The raw authority score is also not yet well calibrated on the held-out synthetic split (ECE ≈ 0.224). It should not be interpreted as a production probability without independent labels and calibration.

## Reproduce

```bash
python -m pip install -e '.[dev,ml,demo]'
./scripts/reproduce_all.sh
```

To retrain the serialized lightweight models before reproduction:

```bash
RETRAIN=1 ./scripts/reproduce_all.sh
```

External benchmark data is intentionally separate. See `benchmark/external/README.md`.

## Project map

- `paper/BELIEFWEAVE.pdf` — research manuscript
- `paper/BELIEFWEAVE.tex` — manuscript source
- `results/paper_grade_eval.json` — held-out baselines, CIs, sensitivity, calibration, ablations
- `results/behavior_intervention.json` — counterfactual intervention results
- `results/error_propagation.json` — controlled fault-injection decomposition
- `results/horizon_scaling.json` — 10k-turn memory-core scaling
- `results/unseen_composition.json` — post-hoc structural challenge and challenge-informed regression patch
- `results/stochastic_stability.json` — 30-seed within-specification stability
- `results/sensitivity_summary.json` — compact threshold/cost sensitivity audit
- `results/power_analysis.json` — human A/B planning calculation
- `submission/` — NeurIPS readiness, Croissant status, external-evidence boundary, and human-eval planning
- `benchmark/beliefshift_v2_test_manifest.json` — frozen test IDs
- `benchmark/croissant.json` — machine-readable benchmark metadata
- `benchmark/external/` — LongMemEval / PersonaMem adapters
- `human_eval/` — blind human-evaluation protocol and tools
- `site/index.html` — project homepage
- `site/demo.html` — interactive authority-gate demo
- `FAILURE_LOG.md` — failure-driven design record
- `NOVELTY_AUDIT.md` — nearby-work comparison
- `FINAL_VALIDATION.md` — artifact validation record

For a short research review, start with `REVIEWER_GUIDE.md`.

## Production assurance

The research gates remain frozen as `v1` and `v2` so the paper results can be reproduced. The runtime default is now the hardened `v3` policy. The API returns the gate version used for each governed-recall decision.

The authority policy is also exhaustively enumerated over a declared 9,600-state discrete model. Under six stated invariants, V1 has 560 property violations, V2 has 146, and the production V3 policy has 0. This is finite model checking of the declared state space, not a proof over arbitrary code or unmodeled metadata.

Privacy/integrity assurance includes an atomic hard-forget path that repairs or purges sibling provenance when source events are shared. A 50-user erasure regression found zero deleted-event leakage in exports and repaired all 50 multi-source sibling cases. A separate 480-ingest, 12-thread SQLite stress run completed with zero errors and a passing integrity check. These are local engineering tests, not claims of distributed production scale or legal privacy compliance.


## Demo deployment boundary

The FastAPI app is safe-by-default as a local demo: without `BELIEFWEAVE_DEMO_TOKEN`, `/api/*` accepts loopback clients only. Docker Compose requires an explicit token. This is not a claim of production authentication or per-user authorization; see `SECURITY.md`.
