from __future__ import annotations
import argparse,csv,json
from pathlib import Path

def prepare_requests(questions_csv:Path, shared_contexts:Path, out:Path, limit:int|None=None):
    contexts={}
    with shared_contexts.open() as f:
        for line in f:
            x=json.loads(line); key=str(x.get('shared_context_id',x.get('id'))); contexts[key]=x
    rows=[]
    with questions_csv.open(newline='') as f:
        for i,row in enumerate(csv.DictReader(f)):
            if limit and i>=limit:break
            cid=str(row.get('shared_context_id'))
            ctx=contexts.get(cid,{})
            rows.append({'persona_id':row.get('persona_id'),'question_id':row.get('question_id'),'question_type':row.get('question_type'),'context':ctx,'user_query':row.get('user_question_or_message',row.get('user_query')),'correct_answer':row.get('correct_answer'),'all_options':row.get('all_options')})
    out.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows)+'\n');return {'n':len(rows),'out':str(out)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('questions_csv');ap.add_argument('shared_contexts_jsonl');ap.add_argument('--out',default='results/personamem_requests.jsonl');ap.add_argument('--limit',type=int);a=ap.parse_args();print(json.dumps(prepare_requests(Path(a.questions_csv),Path(a.shared_contexts_jsonl),Path(a.out),a.limit),indent=2))
if __name__=='__main__':main()
