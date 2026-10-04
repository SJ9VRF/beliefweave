from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results'
load=lambda n: json.loads((R/n).read_text())
pg=load('paper_grade_eval.json'); sealed=load('sealed_spec_challenge.json'); meta=load('metamorphic_authority.json'); mut=load('mutation_adequacy.json'); unseen=load('unseen_composition.json'); sens=load('sensitivity_summary.json'); fmt=load('neurips_submission_readiness.json')
failed=[(k,v) for k,v in sealed['family_breakdown'].items() if v['accuracy']<1]
lines=[
'# BeliefWeave Supplement',
'',
'This supplement expands the controlled evaluation and records boundaries that should not be compressed into the main narrative.',
'',
'## A. Frozen primary evaluation',
'',
f"BeliefShiftBench-v2 contains {pg['n_total']} controlled cases ({pg['n_dev']} development, {pg['n_test']} frozen test). The frozen BeliefWeave policy reaches {pg['systems']['beliefweave']['exact_action_accuracy']*100:.2f}% exact USE/ASK/ABSTAIN accuracy and {pg['systems']['beliefweave']['false_personalization_rate']*100:.2f}% false personalization on the test split.",
'',
'## B. Post-hoc unseen composition',
'',
f"Across {unseen['total_decisions']:,} decisions, the original gate reaches {unseen['mean_exact_action_accuracy']*100:.1f}% exact action accuracy. The challenge-informed patch reaches 100% on the same suite, but that number is regression evidence because the patch was written after observing the failures.",
'',
'## C. Second sealed specification audit',
'',
f"The second audit contains {sealed['n']} cases. Frozen V2 reaches {sealed['exact_action_accuracy']*100:.2f}% exact action accuracy. Challenge-informed V3 reaches {sealed['challenge_informed_v3_accuracy']*100:.1f}% on the same suite and is not counted as independent generalization evidence.",
'',
'Failed V2 families:',
]
for k,v in failed:
    lines.append(f"- `{k}` — {v['accuracy']*100:.1f}% — {v['note']}")
lines += ['', '## D. Metamorphic invariants', '']
for g in meta['gates']:
    lines.append(f"- {g['gate']}: {g['n_checks']-g['n_failed']}/{g['n_checks']} checks passed.")
lines += ['', 'These properties test monotonic or safety-preserving transformations; they are consistency evidence, not user-level utility evidence.', '', '## E. Mutation adequacy', '', f"The primary frozen benchmark kills {mut['mutants_killed']}/{mut['n_mutants']} deliberately broken policies (mutation score {mut['mutation_score']:.2f}).", '']
for k,v in mut['mutants'].items():
    lines.append(f"- `{k}`: accuracy {v['exact_action_accuracy']*100:.2f}%, changed decisions {v['changed_decisions']}, killed={v['killed']}.")
lines += ['', '## F. Sensitivity', '', 'Threshold and cost sweeps are checked in under `results/sensitivity_summary.json`. The main paper reports the stable region rather than selecting a single favorable point without context.', '', '## G. External and human evidence boundary', '', 'No LongMemEval-v1/v2, PersonaMem-v1/v3, or human-preference score is claimed. PersonaMem-v3 already evaluates over-personalization/restraint, so BeliefWeave does not claim restraint itself as novel. The narrower contribution is the explicit memory-level authority action surface, cost-sensitive decision rule, counterfactual intervention diagnostics, and specification-testing machinery.', '', '## H. Submission-format status', '', f"Research manuscript pages: {fmt.get('research_manuscript_pages')}. Official NeurIPS-template readiness: {fmt.get('ready_for_official_neurips_template_submission')}.", '']
for b in fmt.get('blockers',[]): lines.append(f"- {b}")
lines += ['', 'The repository intentionally does not recreate the official conference style. Final submission formatting must use the official style file without custom margin/font overrides.','']

lines += ['', '## I. Transactional ingest guarantee', '', 'The runtime writes one user ingest as a single `BEGIN IMMEDIATE` SQLite transaction spanning the source event, derived memory rows, supersession state, and conflict links. Two explicit failure-injection cases crash after a memory insert and during conflict resolution. Both leave the database identical to its pre-ingest state and pass the relational/provenance integrity audit. This is an engineering atomicity guarantee for the local SQLite implementation, not a distributed-transaction claim.', '', '## J. Experiment lineage and validation environment', '', '`results/experiment_lineage.json` binds the principal result files to SHA256 hashes of their generating scripts and checked input manifests. `constraints/reproducible.txt` records the exact package versions used for validation, while `pyproject.toml` remains the supported compatibility contract. The reference constraints are intentionally not presented as a universal cross-platform lockfile.', '', '## K. User data inventory and process resilience', '', '`results/privacy_inventory.json` checks that a user export includes persisted control metadata, that full erasure leaves no user rows, that guarded erasure retains only scrubbed hashed replay tombstones, and that telemetry correlation identifiers are HMAC-keyed rather than plain digests. `results/database_resilience.json` uses independent processes against one SQLite file and separately terminates an interpreter with an uncommitted event+memory transaction; recovery leaves zero partial rows and passes integrity. These are local reference-runtime engineering checks, not legal-compliance or distributed-durability claims.', '']
(ROOT/'paper/SUPPLEMENT.md').write_text('\n'.join(lines))
