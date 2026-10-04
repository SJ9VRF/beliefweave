from pathlib import Path
from pwm.engine import PersonalMemoryEngine

ROOT=Path(__file__).resolve().parents[1]
def test_hybrid_paraphrase_and_poisoning(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'m.db', enable_ml=True)
    a=e.ingest('u','I am a big fan of quiet cafes.')
    assert any(x['memory'] and x['memory'].value=='quiet cafes' for x in a['actions'])
    b=e.ingest('u','My friend says I love sushi.')
    assert not b['actions']

def test_semantic_retrieval(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'m.db', enable_ml=True)
    e.ingest('u','I am a big fan of quiet cafes.')
    e.ingest('u','My goal is to publish a paper.')
    r=e.recall('u','Where should I go for a calm coffee place?',limit=1)
    assert r and r[0].memory.value=='quiet cafes'

def test_unrelated_types_never_supersede(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'g.db', enable_ml=True)
    e.ingest('u','I am a big fan of quiet cafes.')
    e.ingest('u','My goal is to publish a paper.')
    active=e.memories.list_active('u')
    assert {m.value for m in active}=={'quiet cafes','publish a paper'}

def test_additive_preferences_goals_constraints(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'add.db', enable_ml=True)
    for text in ['I love sushi.','I love jazz.','My goal is to publish a paper.','My goal is to learn French.','I am avoiding raw fish this month.','I am avoiding dairy this month.']:
        e.ingest('u',text,timestamp='2026-01-01T00:00:00+00:00')
    active=e.memories.list_active('u',now='2026-01-02T00:00:00+00:00')
    vals={m.value for m in active}
    assert {'sushi','jazz','publish a paper','learn French','raw fish this month','dairy this month'} <= vals
