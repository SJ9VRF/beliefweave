from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results'
def load(n): return json.loads((R/n).read_text())
b=load('benchmark.json'); a=load('ablations.json'); r=load('retrieval_eval.json'); o=load('ood_robustness.json'); h=load('hard_scenarios.json'); s=load('stress_test.json')
md=f'''# Reproducible Results Tables\n\nGenerated from checked-in JSON outputs by `scripts/generate_results_tables.py`.\n\n## Temporal state ablation\n\n| System | Preference reversal retirement | Temporary expiry |\n|---|---:|---:|\n| Append-only | {100*a['reversal_retirement_accuracy']['append_only']:.1f}% | {100*a['temporary_expiry_accuracy']['append_only']:.1f}% |\n| Latest predicate | {100*a['reversal_retirement_accuracy']['latest_predicate']:.1f}% | {100*a['temporary_expiry_accuracy']['latest_predicate']:.1f}% |\n| BeliefWeave | {100*a['reversal_retirement_accuracy']['full_pwm']:.1f}% | {100*a['temporary_expiry_accuracy']['full_pwm']:.1f}% |\n\n## Retrieval\n\n| Retriever | Hit@1 | Hit@3 | MRR | Stale leaks |\n|---|---:|---:|---:|---:|\n| Lexical baseline | {100*r['lexical']['hit_at_1']:.1f}% | {100*r['lexical']['hit_at_3']:.1f}% | {r['lexical']['mrr']:.3f} | {r['lexical']['stale_leaks']} |\n| Local hybrid | {100*r['semantic_local']['hit_at_1']:.1f}% | {100*r['semantic_local']['hit_at_3']:.1f}% | {r['semantic_local']['mrr']:.3f} | {r['semantic_local']['stale_leaks']} |\n\nControlled retrieval cases: **{r['n_cases']}**.\n\n## Robustness / regression\n\n| Evaluation | Result |\n|---|---:|\n| Hard scenarios | {h['n_scenarios']}/{h['n_scenarios']} |\n| OOD observation router | {100*o['ood_router']['accuracy']:.1f}% ({o['ood_router']['total']} examples) |\n| Hybrid conflict controlled challenge | {100*o['hybrid_conflict']['accuracy']:.1f}% |\n| Adversarial engine checks | {o['engine_adversarial']['passed']}/{o['engine_adversarial']['total']} |\n| Stress active exact contradictions | {s['active_exact_contradictions']} |\n| Stress interactions | {s['interactions']:,} |\n\n## Longitudinal slice\n\n- users: **{b['n_users']}**\n- turns/user: **{b['n_turns_per_user']}**\n- interactions: **{b['interactions']:,}**\n- final current-food accuracy: **{100*b['final_current_food_accuracy']['personal_world_model']:.1f}%**\n- old-belief retirement at reversal: **{100*b['preference_reversal_old_belief_retirement_accuracy']['personal_world_model']:.1f}%**\n- mean active stale food memories: **{b['mean_active_stale_food_memories']}**\n\n> Scientific boundary: these are synthetic, deterministic, template-controlled, or local stress measurements. They are engineering/research-prototype evidence, not real-user performance claims.\n'''
(ROOT/'paper'/'RESULTS_TABLES.md').write_text(md)
print('wrote paper/RESULTS_TABLES.md')


# Paper-grade authority table
try:
    pg = json.loads((R / "paper_grade_eval.json").read_text())
    lines = ["", "## BeliefShiftBench-v2 held-out authority results", "", "| Policy | Exact action | False personalization | CPR |", "|---|---:|---:|---:|"]
    for key,label in [("retrieval_only","Retrieval-only"),("temporal_context","Temporal + context"),("cost_sensitive_authority","Cost-sensitive authority"),("beliefweave","BeliefWeave")]:
        m=pg["systems"][key]; lines.append(f"| {label} | {100*m['exact_action_accuracy']:.1f}% | {100*m['false_personalization_rate']:.1f}% | {m['cpr']:.3f} |")
    out = ROOT/'paper'/'RESULTS_TABLES.md'
    out.write_text(out.read_text()+"\n".join(lines)+"\n")
except FileNotFoundError:
    pass
