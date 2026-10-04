from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import json, math
from pathlib import Path
from pwm.observations.learned_router import LearnedObservationRouter
ROOT=Path(__file__).resolve().parents[1]
OOD={
 'PREFERENCE':['When I get to choose, {v} is usually my pick.','I gravitate toward {v}.','I would take {v} over the alternatives.'],
 'GOAL':['A target I am pursuing is to {v}.','I am setting out to {v}.','The outcome I am working toward is to {v}.'],
 'CONSTRAINT':['Keep {v} off the table for me.','{v} is something I need to avoid.','Please treat {v} as a restriction.'],
 'COMMITMENT':['I promised myself I would {v}.','I am on the hook to {v}.','I still owe it to myself to {v}.'],
 'ROUTINE':['It is typical for me to {v}.','On most days, I end up {v}.','A recurring habit of mine is to {v}.'],
 'NONE':['My colleague says I love {v}.','Suppose I loved {v}; what then?','Can you explain {v}?','She told me she prefers {v}.']
}
VALS=['sushi','quiet cafes','jazz','morning workouts','French','tea']

def main():
    r=LearnedObservationRouter(ROOT/'results'/'observation_router.joblib')
    rows=[]
    for gold,temps in OOD.items():
        for t in temps:
            for v in VALS:
                z=r.route(t.format(v=v)); rows.append((gold,z.label,z.confidence))
    n=len(rows)
    brier=sum((1-c)**2 if g==p else c**2 for g,p,c in rows)/n
    nll=-sum(math.log(max(1e-9,c if g==p else 1-c)) for g,p,c in rows)/n
    bins=[]; ece=0.0
    for lo in [0,.2,.4,.6,.8]:
        hi=lo+.2; xs=[x for x in rows if (lo <= x[2] < hi) or (hi >= 1.0 and lo <= x[2] <= hi)]
        if not xs: continue
        acc=sum(g==p for g,p,_ in xs)/len(xs); conf=sum(c for _,_,c in xs)/len(xs)
        ece += len(xs)/n*abs(acc-conf)
        bins.append({'lo':lo,'hi':hi,'n':len(xs),'accuracy':acc,'mean_confidence':conf})
    thresholds=[]
    for th in [0,.5,.6,.7,.8,.9]:
        xs=[x for x in rows if x[2]>=th]
        thresholds.append({'threshold':th,'coverage':len(xs)/n,'accuracy':sum(g==p for g,p,_ in xs)/len(xs) if xs else None,'n':len(xs)})
    out={'n':n,'ece':ece,'brier_like':brier,'nll_binary_correctness':nll,'bins':bins,'selective_prediction':thresholds,
         'recommended_operating_point':{'threshold':0.7,'rationale':'Raises OOD precision materially; low-confidence candidates should not be persisted without stronger evidence or user confirmation.'}}
    (ROOT/'results'/'calibration.json').write_text(json.dumps(out,indent=2))
    print(json.dumps({'n':n,'ece':round(ece,4),'threshold_0.7':next(x for x in thresholds if x['threshold']==.7)},indent=2))
if __name__=='__main__': main()
