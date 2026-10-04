from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import json,tempfile,random
from pathlib import Path
from datetime import datetime, timezone, timedelta
from pwm.memory.schema import MemoryRecord, MemoryType, SourceType, MemoryStatus
from pwm.memory.store import MemoryStore
from pwm.memory.retriever import MemoryRetriever
from pwm.memory.semantic_retriever import SemanticMemoryRetriever
ROOT=Path(__file__).resolve().parents[1]
random.seed(37)

FOOD=['sushi','quiet cafes','Italian food','tea','Japanese cuisine']
GOALS=['publish a paper','finish my thesis','save for a house','learn French']
ROUTINES=['run in the morning','work out before breakfast','walk after lunch']
DISTRACTORS=[('likes','jazz',MemoryType.PREFERENCE,None),('lives_in','New York',MemoryType.FACT,None),('goal','learn French',MemoryType.GOAL,None),('usually','read at night',MemoryType.ROUTINE,None)]

def make_cases():
    cases=[]
    for i in range(20):
        v=FOOD[i%len(FOOD)]; cases.append({'name':f'food_{i}','query':random.choice(['Where should I go for dinner?','What food place fits me?','Any restaurant idea for me?']),'context':None,'gold':[v],'target':('likes',v,MemoryType.PREFERENCE,None)})
        v=GOALS[i%len(GOALS)]; cases.append({'name':f'career_{i}','query':random.choice(['What matters for my career right now?','What goal should I focus on?','What am I working toward professionally?']),'context':None,'gold':[v],'target':('goal',v,MemoryType.GOAL,None)})
        v=ROUTINES[i%len(ROUTINES)]; cases.append({'name':f'fitness_{i}','query':random.choice(['How should I plan my workout?','What is my exercise routine?','Remind me how I usually train.']),'context':None,'gold':[v],'target':('usually',v,MemoryType.ROUTINE,None)})
        cases.append({'name':f'workctx_{i}','query':'How should you write this message?','context':'work','gold':['formal tone'],'target':('prefers','formal tone',MemoryType.PREFERENCE,'work'),'extra':[('prefers','casual tone',MemoryType.PREFERENCE,'friends')]})
        cases.append({'name':f'friendctx_{i}','query':'How should you write this message?','context':'friends','gold':['casual tone'],'target':('prefers','casual tone',MemoryType.PREFERENCE,'friends'),'extra':[('prefers','formal tone',MemoryType.PREFERENCE,'work')]})
        cases.append({'name':f'restrict_{i}','query':random.choice(['What food should I avoid?','Any restriction I should remember?','What can I not eat?']),'context':None,'gold':['raw fish'],'target':('avoids','raw fish',MemoryType.CONSTRAINT,None)})
    return cases
CASES=make_cases()

def setup_store(path:Path,case):
    s=MemoryStore(path); now=datetime.now(timezone.utc)
    mems=[case['target']]+case.get('extra',[])+random.sample(DISTRACTORS,k=3)
    random.shuffle(mems)
    for i,(pred,val,typ,ctx) in enumerate(mems):
        s.add(MemoryRecord(user_id='u',subject='user',predicate=pred,value=val,memory_type=typ,source_type=SourceType.EXPLICIT,confidence=.95,source_event_ids=[f'e{i}'],valid_from=now.isoformat(),context_scope=ctx,importance=.8,stability=.8))
    s.add(MemoryRecord(user_id='u',subject='user',predicate='likes',value='old restaurant choice',memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.99,source_event_ids=['stale'],valid_from=(now-timedelta(days=400)).isoformat(),importance=1,stability=1,status=MemoryStatus.SUPERSEDED))
    return s

def score(cls):
    rows=[]
    for case in CASES:
        with tempfile.TemporaryDirectory() as d:
            r=cls(setup_store(Path(d)/'db.sqlite',case)).retrieve('u',case['query'],limit=3,context=case['context'])
            vals=[x.memory.value for x in r]; gold=set(case['gold']); hits=[v for v in vals if v in gold]
            rank=next((i for i,v in enumerate(vals,1) if v in gold),None)
            rows.append({'case':case['name'],'top':vals,'hit_at_1':bool(vals and vals[0] in gold),'hit_at_3':bool(hits),'reciprocal_rank':0 if rank is None else 1/rank,'stale_leak':any('old restaurant' in v for v in vals)})
    n=len(rows)
    return {'cases':rows,'hit_at_1':sum(x['hit_at_1'] for x in rows)/n,'hit_at_3':sum(x['hit_at_3'] for x in rows)/n,'mrr':sum(x['reciprocal_rank'] for x in rows)/n,'stale_leaks':sum(x['stale_leak'] for x in rows)}

def main():
    out={'lexical':score(MemoryRetriever),'semantic_local':score(SemanticMemoryRetriever),'n_cases':len(CASES)}
    (ROOT/'results'/'retrieval_eval.json').write_text(json.dumps(out,indent=2))
    print(json.dumps({'n_cases':len(CASES),'lexical':{k:out['lexical'][k] for k in ('hit_at_1','hit_at_3','mrr','stale_leaks')},'semantic_local':{k:out['semantic_local'][k] for k in ('hit_at_1','hit_at_3','mrr','stale_leaks')}},indent=2))
if __name__=='__main__':main()
