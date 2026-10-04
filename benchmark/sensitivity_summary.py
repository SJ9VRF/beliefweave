from __future__ import annotations
import json, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
x=json.loads((ROOT/'results'/'paper_grade_eval.json').read_text())
# Threshold sweep summary for BeliefWeave-style gate.
ts=x['threshold_sweep']
# The sweep may contain several ask thresholds per use threshold. summarize exact-accuracy plateau.
acc=[r['exact_action_accuracy'] for r in ts]
best=max(acc); near=[r for r in ts if r['exact_action_accuracy']>=best-.01]
# Cost sensitivity summary.
cs=x['cost_sensitivity']
cpr=[r['cpr'] for r in cs]
exact=[r['exact_action_accuracy'] for r in cs]
# How often the cost-sensitive policy stays at least 80% exact and avoids false personalization.
robust=[r for r in cs if r['exact_action_accuracy']>=.80 and r['false_personalization_rate']<=.05]
out={
 'threshold_sweep':{
   'n_settings':len(ts),'best_exact_action_accuracy':best,
   'near_best_within_1pp_count':len(near),
   'near_best_fraction':len(near)/len(ts),
   'exact_action_accuracy_min':min(acc),'exact_action_accuracy_max':max(acc),
 },
 'cost_sensitivity':{
   'n_settings':len(cs),'exact_action_accuracy_min':min(exact),'exact_action_accuracy_max':max(exact),
   'cpr_min':min(cpr),'cpr_max':max(cpr),
   'settings_ge_80pct_exact_and_le_5pct_false_personalization':len(robust),
   'fraction_ge_80pct_exact_and_le_5pct_false_personalization':len(robust)/len(cs),
 },
 'interpretation':'Sensitivity is reported as a range, not as proof of universal robustness. Different application costs can rationally change the optimal ASK/ABSTAIN tradeoff.'
}
(ROOT/'results'/'sensitivity_summary.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2))
