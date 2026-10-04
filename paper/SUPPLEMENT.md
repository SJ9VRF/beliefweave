# BeliefWeave Supplement

This supplement expands the controlled evaluation and records boundaries that should not be compressed into the main narrative.

## A. Frozen primary evaluation

BeliefShiftBench-v2 contains 640 controlled cases (320 development, 320 frozen test). The frozen BeliefWeave policy reaches 96.88% exact USE/ASK/ABSTAIN accuracy and 1.56% false personalization on the test split.

## B. Post-hoc unseen composition

Across 2,880 decisions, the original gate reaches 75.0% exact action accuracy. The challenge-informed patch reaches 100% on the same suite, but that number is regression evidence because the patch was written after observing the failures.

## C. Second sealed specification audit

The second audit contains 480 cases. Frozen V2 reaches 53.33% exact action accuracy. Challenge-informed V3 reaches 100.0% on the same suite and is not counted as independent generalization evidence.

Failed V2 families:
- `archived_scoped_unknown` — 0.0% — Archived evidence should not trigger clarification.
- `deleted_scoped_unknown` — 0.0% — Lifecycle invalidity should dominate missing-context clarification.
- `expired_scoped_unknown` — 0.0% — Expiry should dominate missing-context clarification.
- `malformed_valid_from` — 0.0% — Malformed temporal metadata should fail closed to clarification rather than personalize.
- `malformed_valid_until` — 0.0% — Malformed temporal metadata should fail closed to clarification rather than personalize.
- `missing_provenance_high_conf` — 0.0% — High-confidence memory with no provenance should not immediately personalize.
- `sensitive_unverified` — 0.0% — Sensitive unverified memory warrants confirmation before use.

## D. Metamorphic invariants

- DecisionAwareBeliefGateV2: 185/185 checks passed.
- DecisionAwareBeliefGateV3: 185/185 checks passed.

These properties test monotonic or safety-preserving transformations; they are consistency evidence, not user-level utility evidence.

## E. Mutation adequacy

The primary frozen benchmark kills 6/6 deliberately broken policies (mutation score 1.00).

- `no_status`: accuracy 84.38%, changed decisions 40, killed=True.
- `no_time`: accuracy 84.38%, changed decisions 40, killed=True.
- `no_context`: accuracy 84.38%, changed decisions 40, killed=True.
- `no_conflict`: accuracy 84.38%, changed decisions 40, killed=True.
- `no_provenance`: accuracy 90.62%, changed decisions 30, killed=True.
- `always_use_active`: accuracy 37.50%, changed decisions 195, killed=True.

## F. Sensitivity

Threshold and cost sweeps are checked in under `results/sensitivity_summary.json`. The main paper reports the stable region rather than selecting a single favorable point without context.

## G. External and human evidence boundary

No LongMemEval-v1/v2, PersonaMem-v1/v3, or human-preference score is claimed. PersonaMem-v3 already evaluates over-personalization/restraint, so BeliefWeave does not claim restraint itself as novel. The narrower contribution is the explicit memory-level authority action surface, cost-sensitive decision rule, counterfactual intervention diagnostics, and specification-testing machinery.

## H. Submission-format status

Research manuscript pages: 9. Official NeurIPS-template readiness: False.

- official neurips_2026.sty is not bundled
- paper source does not load neurips_2026.sty
- paper source uses custom geometry rather than the official template

The repository intentionally does not recreate the official conference style. Final submission formatting must use the official style file without custom margin/font overrides.


## I. Transactional ingest guarantee

The runtime writes one user ingest as a single `BEGIN IMMEDIATE` SQLite transaction spanning the source event, derived memory rows, supersession state, and conflict links. Two explicit failure-injection cases crash after a memory insert and during conflict resolution. Both leave the database identical to its pre-ingest state and pass the relational/provenance integrity audit. This is an engineering atomicity guarantee for the local SQLite implementation, not a distributed-transaction claim.

## J. Experiment lineage and validation environment

`results/experiment_lineage.json` binds the principal result files to SHA256 hashes of their generating scripts and checked input manifests. `constraints/reproducible.txt` records the exact package versions used for validation, while `pyproject.toml` remains the supported compatibility contract. The reference constraints are intentionally not presented as a universal cross-platform lockfile.

## K. User data inventory and process resilience

`results/privacy_inventory.json` checks that a user export includes persisted control metadata, that full erasure leaves no user rows, that guarded erasure retains only scrubbed hashed replay tombstones, and that telemetry correlation identifiers are HMAC-keyed rather than plain digests. `results/database_resilience.json` uses independent processes against one SQLite file and separately terminates an interpreter with an uncommitted event+memory transaction; recovery leaves zero partial rows and passes integrity. These are local reference-runtime engineering checks, not legal-compliance or distributed-durability claims.
