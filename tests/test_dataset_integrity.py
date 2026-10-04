import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_memworldbench_shape_and_required_fields():
    p=ROOT/'benchmark/data/memworldbench_1000x100.jsonl'
    assert p.exists()
    users=set(); n=0
    with p.open() as f:
        for line in f:
            row=json.loads(line); n+=1
            users.add(row['user_id'])
            assert row.get('text')
            assert row.get('timestamp')
    assert n==100_000
    assert len(users)==1_000

def test_hard_scenario_count_and_categories():
    p=ROOT/'benchmark/data/hard_scenarios_360.jsonl'
    rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    assert len(rows)==360
    cats={r['category'] for r in rows}
    assert cats=={'preference_reversal','context_dependence','temporary_state','explicit_correction','third_party_attribution','multilingual'}
