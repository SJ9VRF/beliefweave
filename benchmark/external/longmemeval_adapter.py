from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path
from pwm.engine import PersonalMemoryEngine

def run(path:Path,max_items:int|None=None,k:int=5):
    data=json.loads(path.read_text()); data=data[:max_items] if max_items else data
    rows=[]
    for idx,item in enumerate(data):
        with tempfile.TemporaryDirectory() as d:
            e=PersonalMemoryEngine(Path(d) / 'lme.sqlite', enable_ml=True); uid=f'lme-{idx}'
            for sid,date,session in zip(item['haystack_session_ids'],item['haystack_dates'],item['haystack_sessions']):
                for turn in session:
                    if turn.get('role')!='user': continue
                    e.ingest(uid,turn.get('content',''),conversation_id=sid,timestamp=date)
            hits=[]
            for r in e.recall(uid,item['question'],limit=k,now=item.get('question_date')):
                for eid in r.memory.source_event_ids:
                    ev=e.events.get(eid)
                    if ev and ev.conversation_id:hits.append(ev.conversation_id)
            gold=set(item.get('answer_session_ids',[])); hit=bool(gold.intersection(hits)) if gold else item['question_id'].endswith('_abs') and not hits
            rows.append({'question_id':item['question_id'],'question_type':item['question_type'],'gold_session_ids':sorted(gold),'retrieved_session_ids':hits,'session_recall_hit':hit})
    by={}
    for r in rows:
        by.setdefault(r['question_type'],[]).append(r['session_recall_hit'])
    return {'benchmark':'LongMemEval-retrieval-adapter','n':len(rows),'session_recall_at_k':sum(r['session_recall_hit'] for r in rows)/max(1,len(rows)),'by_type':{k:sum(v)/len(v) for k,v in by.items()},'rows':rows,'boundary':'Retrieval evidence coverage only; official LongMemEval answer-quality evaluation requires a reader model and the official evaluator.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('dataset');ap.add_argument('--max-items',type=int);ap.add_argument('-k',type=int,default=5);ap.add_argument('--out',default='results/longmemeval_external.json');a=ap.parse_args();r=run(Path(a.dataset),a.max_items,a.k);Path(a.out).write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
