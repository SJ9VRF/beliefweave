import csv, json
from pathlib import Path
from benchmark.external.personamem_adapter import prepare_requests
ROOT=Path(__file__).resolve().parents[1]
def test_public_registry_has_non_score_claim_policy():
    x=json.loads((ROOT/'benchmark/external/public_benchmark_registry.json').read_text())
    assert x['longmemeval']['n_questions']==500
    assert x['personamem_v1']['public_32k_rows']==589
    assert 'no external benchmark score' in x['claim_policy'].lower()
def test_personamem_adapter_smoke(tmp_path):
    q=tmp_path/'q.csv'; c=tmp_path/'c.jsonl'; o=tmp_path/'out.jsonl'
    cols=['persona_id','question_id','question_type','topic','context_length_in_tokens','context_length_in_letters','distance_to_ref_in_blocks','distance_to_ref_in_tokens','num_irrelevant_tokens','distance_to_ref_proportion_in_context','user_question_or_message','correct_answer','all_options','shared_context_id','end_index_in_shared_context']
    with q.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerow({k:'' for k in cols}|{'persona_id':'p','question_id':'q1','question_type':'track_full_preference_evolution','user_question_or_message':'What do I prefer?','correct_answer':'(a)','all_options':'["(a) x"]','shared_context_id':'ctx','end_index_in_shared_context':'1'})
    c.write_text(json.dumps({'shared_context_id':'ctx','messages':[{'role':'user','content':'I like x'}]})+'\n')
    r=prepare_requests(q,c,o)
    assert r['n']==1
    row=json.loads(o.read_text().splitlines()[0]);assert row['question_id']=='q1' and row['context']['shared_context_id']=='ctx'
