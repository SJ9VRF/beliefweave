from __future__ import annotations

import argparse
import json
import tempfile
from collections import defaultdict
from pathlib import Path

from pwm.engine import PersonalMemoryEngine


def _session_items(conversation:dict):
    for key in sorted((k for k in conversation if k.startswith('session_') and k.count('_')==1), key=lambda x:int(x.split('_')[1])):
        turns=conversation.get(key) or []
        for turn in turns:
            text=turn.get('text','')
            if turn.get('blip_caption'):
                text=(text+' [Image: '+turn['blip_caption']+']').strip()
            yield key, turn.get('dia_id'), turn.get('speaker'), text


def run(path:Path, *, top_k:int=10, max_samples:int|None=None, max_questions:int|None=None) -> dict:
    data=json.loads(path.read_text())
    if isinstance(data,dict) and 'samples' in data:data=data['samples']
    if max_samples:data=data[:max_samples]
    rows=[]; by_cat=defaultdict(list); answerable=0
    for si,sample in enumerate(data):
        with tempfile.TemporaryDirectory() as d:
            engine=PersonalMemoryEngine(Path(d) / 'locomo.sqlite', enable_ml=True)
            uid=f'locomo-{si}'
            for session,dia_id,speaker,text in _session_items(sample['conversation']):
                # Preserve the gold dialogue identifier in conversation_id so retrieved
                # source events can be compared directly to LoCoMo evidence annotations.
                engine.ingest(uid, text, conversation_id=dia_id or session)
            qas=sample.get('qa',[])
            if max_questions is not None:qas=qas[:max_questions]
            for qi,qa in enumerate(qas):
                cat=int(qa.get('category',0) or 0)
                gold=qa.get('evidence') or []
                if isinstance(gold,str):gold=[gold]
                # Category 5 is adversarial/no-answer and has no meaningful evidence recall.
                if cat==5 or not gold:
                    rows.append({'sample_id':sample.get('sample_id',si),'question_index':qi,'category':cat,'answerable':False,'evidence_recall_at_k':None})
                    continue
                answerable+=1
                retrieved=[]
                for hit in engine.recall(uid,qa['question'],limit=top_k):
                    for eid in hit.memory.source_event_ids:
                        ev=engine.events.get(eid)
                        if ev and ev.conversation_id:retrieved.append(ev.conversation_id)
                gs=set(gold); rs=set(retrieved)
                recall=len(gs & rs)/len(gs)
                by_cat[str(cat)].append(recall)
                rows.append({'sample_id':sample.get('sample_id',si),'question_index':qi,'category':cat,'answerable':True,'gold_evidence':gold,'retrieved_evidence':retrieved,'evidence_recall_at_k':recall})
    vals=[r['evidence_recall_at_k'] for r in rows if r['evidence_recall_at_k'] is not None]
    return {
        'benchmark':'LoCoMo retrieval-evidence adapter',
        'top_k':top_k,
        'samples':len(data),
        'answerable_questions':answerable,
        'mean_evidence_recall_at_k':sum(vals)/len(vals) if vals else 0.0,
        'by_category':{k:sum(v)/len(v) for k,v in by_cat.items()},
        'rows':rows,
        'boundary':'Retrieval evidence coverage only. LoCoMo end-to-end answer quality requires answer generation/judging; category 5 adversarial questions are excluded from evidence recall.'
    }


def main():
    ap=argparse.ArgumentParser();ap.add_argument('dataset');ap.add_argument('-k','--top-k',type=int,default=10);ap.add_argument('--max-samples',type=int);ap.add_argument('--max-questions',type=int);ap.add_argument('--out',default='results/locomo_external.json');a=ap.parse_args()
    r=run(Path(a.dataset),top_k=a.top_k,max_samples=a.max_samples,max_questions=a.max_questions);Path(a.out).write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
