from __future__ import annotations
import json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Conservative normal-approximation planning numbers for a paired human A/B preference study.
# z=1.96 two-sided alpha=.05, z=.842 for 80% power.
z_alpha=1.96; z_beta=.842
# For a simple one-sample preference proportion against 0.5, use p*(1-p) under alternative.
def n_for_preference(p):
    delta=abs(p-.5)
    if delta==0:return None
    # normal approximation with null and alt variances
    num=(z_alpha*math.sqrt(.25)+z_beta*math.sqrt(p*(1-p)))**2
    return math.ceil(num/(delta**2))
rows=[]
for p in [.60,.65,.70,.75]: rows.append({'true_preference_rate':p,'approx_n_for_80pct_power_two_sided_alpha_0_05':n_for_preference(p)})
out={
 'human_ab_planning':rows,
 'recommended_minimum_complete_pairs':100,
 'recommendation_rationale':'100 complete blind A/B pairs gives useful power for moderate preference effects and leaves room for exclusions; report exact confidence intervals and participant-level clustering when repeated judgments are collected.',
 'boundary':'Planning calculation only. Final analysis should use the realized design, clustered/paired inference where appropriate, and a pre-specified exclusion policy.'
}
(ROOT/'results'/'power_analysis.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
