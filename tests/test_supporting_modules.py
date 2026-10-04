from pathlib import Path
from datetime import datetime, timezone
import json, subprocess, sys, tempfile
from pwm.evals.metrics import Counts, exact_contains
from pwm.memory.consolidation import MemoryConsolidator
from pwm.memory.retriever import MemoryRetriever, tokens
from pwm.memory.schema import MemoryRecord, MemoryType, SourceType, Observation
from pwm.memory.store import MemoryStore
from pwm.simulation.generator import LongitudinalUserGenerator
from pwm.temporal import parse_iso, infer_valid_until, is_expired
from pwm.world_model.conflict import ConflictResolver


def _mem(user='u', pred='likes', value='sushi', typ=MemoryType.PREFERENCE, context=None, vf='2026-01-01T00:00:00+00:00'):
    return MemoryRecord(user_id=user, subject='user', predicate=pred, value=value, memory_type=typ,
                        source_type=SourceType.EXPLICIT, confidence=.9, source_event_ids=['e'],
                        context_scope=context, valid_from=vf, importance=.8)


def test_metrics_and_tokens():
    c=Counts(tp=2,fp=1,fn=2)
    assert round(c.precision(),3)==.667
    assert c.recall()==.5
    assert 0<c.f1()<1
    m=_mem()
    assert exact_contains([m],'likes','SUSHI')
    assert tokens("Quiet-cafes and tea") >= {'quiet-cafes','and','tea'}


def test_temporal_helpers():
    assert parse_iso('bad') is None
    start='2026-01-01T00:00:00+00:00'
    assert infer_valid_until('today',start).startswith('2026-01-02')
    assert infer_valid_until('this week',start).startswith('2026-01-08')
    assert infer_valid_until('for 2 weeks',start).startswith('2026-01-15')
    assert infer_valid_until('for 3 days',start).startswith('2026-01-04')
    assert infer_valid_until('forever',start) is None
    assert is_expired('2026-01-01T00:00:00+00:00','2026-01-02T00:00:00+00:00')
    assert not is_expired(None,'2026-01-02T00:00:00+00:00')


def test_consolidation_and_lexical_retrieval(tmp_path:Path):
    store=MemoryStore(tmp_path/'x.db')
    a=_mem(context='food'); b=_mem(pred='goal',value='publish a paper',typ=MemoryType.GOAL)
    store.add(a); store.add(b)
    sections=MemoryConsolidator(store).consolidate('u',now='2026-01-02T00:00:00+00:00')
    assert {s.category for s in sections}=={'preference','goal'}
    out=MemoryRetriever(store).retrieve('u','sushi food',context='food',now='2026-01-02T00:00:00+00:00')
    assert out and out[0].memory.value=='sushi'
    assert out[0].reasons['context_bonus']>0


def test_generator_is_deterministic_and_writes(tmp_path:Path):
    g1=LongitudinalUserGenerator(seed=11); g2=LongitudinalUserGenerator(seed=11)
    a=g1.trajectory('u',100); b=g2.trajectory('u',100)
    assert [x.text for x in a]==[x.text for x in b]
    assert any(x.kind=='drift' for x in a)
    assert any(x.kind=='temporary' for x in a)
    p=tmp_path/'d.jsonl'; rows=LongitudinalUserGenerator(seed=4).generate(2,10,p)
    assert len(rows)==20 and len(p.read_text().splitlines())==20


def test_conflict_rule_branches():
    r=ConflictResolver()
    old=_mem(context='work')
    obs=Observation(subject='user',attribute='likes',value='sushi',memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.9,source_event_id='e2',context_scope='home')
    assert r.classify(old,obs).value=='context_dependent'
    obs2=Observation(subject='user',attribute='dislikes',value='fish',memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.9,source_event_id='e2')
    assert r.classify(_mem(),obs2).value=='preference_drift'
    obs3=Observation(subject='user',attribute='avoids',value='fish',memory_type=MemoryType.CONSTRAINT,source_type=SourceType.EXPLICIT,confidence=.9,source_event_id='e2')
    assert r.classify(_mem(),obs3).value=='apparent_conflict'
    old4=_mem(pred='lives_in',value='NYC',typ=MemoryType.FACT)
    obs4=Observation(subject='user',attribute='lives_in',value='Paris',memory_type=MemoryType.FACT,source_type=SourceType.EXPLICIT,confidence=.9,source_event_id='e2')
    assert r.classify(old4,obs4).value=='temporal_update'
