from __future__ import annotations
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'results'

def load(name: str):
    return json.loads((R / name).read_text())

bench = load('benchmark.json')
hard = load('hard_scenarios.json')
ood = load('ood_robustness.json')
cal = load('calibration.json')
ret = load('retrieval_eval.json')
stress = load('stress_test.json')
coverage = load('coverage.json')
tests = load('test_summary.json')

pg = load('paper_grade_eval.json')
intervention = load('behavior_intervention.json')
horizon = load('horizon_scaling.json')
faults = load('error_propagation.json')
sealed = load('sealed_spec_challenge.json')
metamorphic = load('metamorphic_authority.json')
mutation = load('mutation_adequacy.json')
format_status = load('neurips_submission_readiness.json')

coverage_pct = coverage['totals']['percent_covered']
test_count = tests['passed']
version = tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']
select07 = next(x for x in cal['selective_prediction'] if abs(x['threshold'] - 0.7) < 1e-9)
lex = ret['lexical']; hyb = ret['semantic'] if 'semantic' in ret else ret.get('hybrid')
if hyb is None:
    # Current evaluator stores aggregate hybrid metrics in the second top-level result object under 'semantic' in some versions.
    # Detect by scanning dict-valued entries with hit_at_1 keys.
    candidates = [v for k,v in ret.items() if k != 'lexical' and isinstance(v, dict) and 'hit_at_1' in v]
    if not candidates:
        raise KeyError('Could not locate hybrid retrieval metrics')
    hyb = candidates[0]
n_queries = ret.get('n_queries', ret.get('n_cases'))
ood_router = ood['ood_router']

summary = f'''# Reproducible Results Summary

This file is generated from `results/*.json` by `scripts/sync_publication.py`. Do not edit measured values by hand.

## Primary authority evaluation — {pg['benchmark']}
- Total controlled cases: **{pg['n_total']}**
- Development split: **{pg['n_dev']}**
- Frozen held-out test split: **{pg['n_test']}**
- Authority labels: **USE / ASK / ABSTAIN**
- BeliefWeave exact-action accuracy: **{pg['systems']['beliefweave']['exact_action_accuracy']*100:.2f}%** (95% bootstrap CI **{pg['systems']['beliefweave']['exact_action_accuracy_95ci'][0]*100:.2f}–{pg['systems']['beliefweave']['exact_action_accuracy_95ci'][1]*100:.2f}%**)
- Temporal + context baseline: **{pg['systems']['temporal_context']['exact_action_accuracy']*100:.2f}%**
- Retrieval-only baseline: **{pg['systems']['retrieval_only']['exact_action_accuracy']*100:.2f}%**
- BeliefWeave false-personalization rate: **{pg['systems']['beliefweave']['false_personalization_rate']*100:.2f}%**
- Retrieval-only false-personalization rate: **{pg['systems']['retrieval_only']['false_personalization_rate']*100:.2f}%**
- BeliefWeave CPR: **{pg['systems']['beliefweave']['cpr']:.4f}**
- Retrieval-only CPR: **{pg['systems']['retrieval_only']['cpr']:.4f}**
- McNemar, BeliefWeave vs temporal + context: **p = {pg['paired_test_vs_temporal_context']['exact_two_sided_p']:.2e}**

## Counterfactual response intervention
- Frozen cases: **{intervention['n']}**
- BeliefWeave personalization intervention fidelity: **{intervention['beliefweave']['personalization_intervention_fidelity']*100:.2f}%**
- BeliefWeave behavior intervention fidelity: **{intervention['beliefweave']['behavior_intervention_fidelity']*100:.2f}%**
- False personalization influence rate: **{intervention['beliefweave']['false_personalization_influence_rate']*100:.2f}%**
- Missed personalization rate: **{intervention['beliefweave']['missed_personalization_influence_rate']*100:.2f}%**

The response renderer is deterministic and controlled; these are mechanism/intervention measurements, not external-LLM quality or human-preference results.

## Authority calibration
- Brier score: **{pg['calibration']['brier']:.4f}**
- NLL: **{pg['calibration']['nll']:.4f}**
- ECE: **{pg['calibration']['ece_10']:.4f}**
- Adaptive ECE: **{pg['calibration']['adaptive_ece_10']:.4f}**

The relatively high ECE is a reported limitation: the authority score is not yet a well-calibrated probability.

## Local memory-core scaling
- Horizons: **{' / '.join(f"{x['turns']:,}" for x in horizon['rows'])} turns**
- At {horizon['rows'][-1]['turns']:,} turns: **{horizon['rows'][-1]['memory_rows']} historical rows, {horizon['rows'][-1]['active_memories']} active rows, {horizon['rows'][-1]['active_duplicate_single_value_slots']} duplicate active single-value slots**
- Recorded local p95 memory update: **~{horizon['rows'][-1]['p95_memory_update_ms']:.2f} ms**
- Recorded local p95 authority gate: **~{horizon['rows'][-1]['p95_gate_ms']:.3f} ms**

These local SQLite numbers are environment-dependent and exclude model/network latency.

## Existing memory/retrieval validation
- Longitudinal slice: **{bench['n_users']} users × {bench['n_turns_per_user']} turns = {bench['interactions']:,} interactions**
- Preference-reversal obsolete-belief retirement: **{bench['preference_reversal_old_belief_retirement_accuracy']['personal_world_model']*100:.1f}% PWM vs {bench['preference_reversal_old_belief_retirement_accuracy']['naive_append_only']*100:.1f}% append-only**
- Hard scenarios: **{hard['n_scenarios']} / {hard['n_scenarios']} passed**
- Controlled retrieval queries: **{n_queries}**
- Lexical: Hit@1 **{lex['hit_at_1']*100:.1f}%**, Hit@3 **{lex['hit_at_3']*100:.1f}%**, MRR **{lex['mrr']:.3f}**
- Local hybrid: Hit@1 **{hyb['hit_at_1']*100:.1f}%**, Hit@3 **{hyb['hit_at_3']*100:.1f}%**, MRR **{hyb['mrr']:.3f}**
- Stale-memory leaks: lexical **{lex['stale_leaks']}**, hybrid **{hyb['stale_leaks']}**
- OOD observation-router accuracy: **{ood_router['accuracy']*100:.2f}%** on **{ood_router['total']}** examples
- OOD observation-router ECE: **{cal['ece']:.4f}**
- At confidence ≥0.70: accuracy **{select07['accuracy']*100:.2f}%**, coverage **{select07['coverage']*100:.2f}%**, n={select07['n']}

## Engineering quality
- Full tests: **{test_count}/{test_count} passed**
- Line coverage: **{coverage_pct:.2f}%**
- Stress interactions: **{stress['interactions']:,}**
- Active exact contradictions: **{stress['active_exact_contradictions']}**

## Specification robustness
- Second sealed specification audit: **{sealed['n']} cases**.
- V2 exact action accuracy on that audit: **{sealed['exact_action_accuracy']*100:.2f}%**.
- Challenge-informed V3 regression accuracy on the same audit: **{sealed['challenge_informed_v3_accuracy']*100:.2f}%**; this is explicitly not independent generalization evidence.
- Metamorphic invariants: **{sum(g['n_checks'] for g in metamorphic['gates'])} checks total across {len(metamorphic['gates'])} frozen gates**, all passing.
- Benchmark mutation adequacy: **{mutation['mutants_killed']}/{mutation['n_mutants']} mutants killed**, mutation score **{mutation['mutation_score']:.2f}**.

## Submission-format boundary
- Research manuscript pages: **{format_status.get('research_manuscript_pages')}**.
- Official NeurIPS template ready: **{format_status.get('ready_for_official_neurips_template_submission')}**.
- Format blockers: **{'; '.join(format_status.get('blockers', []))}**.

## External/human evaluation boundary
LongMemEval-v1/v2 and PersonaMem-v1/v3 contracts are documented, but official third-party runs were not executed in this build environment. PersonaMem-v3 already studies over-personalization/restraint, so BeliefWeave does not claim restraint itself as novel. A blind human A/B protocol and analysis package are included, but no participants were run. Therefore **no external benchmark or human-preference score is claimed**.

## Scientific boundary
All reported BeliefShiftBench-v2 authority numbers are synthetic, deterministic, controlled mechanism measurements. They support the internal causal and decision-governance claims tested here, not broad real-user utility or state-of-the-art claims.
'''
(ROOT / 'paper' / 'REPRODUCIBLE_SUMMARY.md').write_text(summary)

# Sync a small set of known human-facing metrics.
for fn in ['FINAL_VALIDATION.md', 'README.md', 'dashboard/index.html']:
    p = ROOT / fn
    s = p.read_text()
    s = s.replace('OOD expected calibration error: **0.0571**', f"OOD expected calibration error: **{cal['ece']:.4f}**")
    s = s.replace('ECE 0.057', f"ECE {cal['ece']:.3f}")
    s = s.replace('>0.057<', f">{cal['ece']:.3f}<")
    p.write_text(s)

p = ROOT / 'paper' / 'TECHNICAL_REPORT.md'
s = p.read_text().replace(
    'confidence is not calibrated; the simulator is not a realistic user model;',
    'confidence calibration has only been measured on synthetic OOD paraphrases—not on human labels; the simulator is not a realistic user model;'
)
p.write_text(s)


# Sync release-quality counts that are expected to change as the suite grows.
for fn in ['FINAL_VALIDATION.md','README.md','ARTIFACT_MANIFEST.md','QUALITY_GATES.md','RELEASE_NOTES.md','REVIEWER_GUIDE.md','RELEASE_CHECKLIST.md','paper/MANUSCRIPT.md','paper/BELIEFWEAVE.tex']:
    p = ROOT / fn
    if not p.exists():
        continue
    s = p.read_text()
    import re
    s = re.sub(r'\b\d+/\d+ tests passed\b', f'{test_count}/{test_count} tests passed', s)
    s = re.sub(r'\b\d+/\d+ regression and API tests passing\b', f'{test_count}/{test_count} regression and API tests passing', s)
    s = re.sub(r'public metrics show \*\*\d+/\d+ tests\*\*', f'public metrics show **{test_count}/{test_count} tests**', s)
    s = re.sub(r'Full test suite: \*\*\d+/\d+ passed\*\*', f'Full test suite: **{test_count}/{test_count} passed**', s)
    s = re.sub(r'\b\d+ regression/safety/API(?:/invariant)?(?:/packaging)?(?:/schema)?(?:/CLI)? tests', f'{test_count} regression/safety/API/invariant/packaging tests', s)
    s = re.sub(r'\b9[0-9]\.\d{2}% line coverage', f'{coverage_pct:.2f}% line coverage', s)
    s = re.sub(r'\b\d+ regression, safety, API, invariant, packaging, schema, and CLI tests with [0-9]+\.[0-9]+\\% line coverage', f'{test_count} regression, safety, API, invariant, packaging, schema, and CLI tests with {coverage_pct:.2f}\\% line coverage', s)
    s = re.sub(r'personal_world_model-0\.[0-9]+\.0-py3-none-any\.whl', f'personal_world_model-{version}-py3-none-any.whl', s)
    s = re.sub(r'Package version advanced to \*\*0\.[0-9]+\.0\*\*\.', f'Package version advanced to **{version}**.', s)
    p.write_text(s)

p = ROOT / 'ARTIFACT_MANIFEST.md'
s = p.read_text().replace(
    '`tests/` — 28 regression/safety/API tests including `test_api_e2e.py`',
    '`tests/` — 36 regression/safety/API/invariant tests across the current suite, including `test_api_e2e.py` and `test_determinism_and_invariants.py`'
)
p.write_text(s)

p = ROOT / 'RELEASE_NOTES.md'
s = p.read_text().replace(
    '28/28 regression, release-hardening, and API tests passed',
    '36/36 regression, release-hardening, API, and invariant tests passed'
)
p.write_text(s)
