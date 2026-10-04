from concurrent.futures import ThreadPoolExecutor

from benchmark.authority_modelcheck import run as run_modelcheck
from pwm.belief_governance import DecisionAwareBeliefGateV3, PersonalizationAction
from pwm.engine import PersonalMemoryEngine
from pwm.integrity import audit_database
from pwm.memory.schema import Event, MemoryRecord, MemoryType, SourceType


def _mem(user, value, source_ids):
    return MemoryRecord(
        user_id=user,
        subject='user',
        predicate='preference.food',
        value=value,
        memory_type=MemoryType.PREFERENCE,
        source_type=SourceType.EXPLICIT,
        confidence=.95,
        source_event_ids=list(source_ids),
    )


def test_production_engine_defaults_to_v3(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'g.db')
    assert e.belief_gate_version=='v3'
    assert isinstance(e.belief_gate,DecisionAwareBeliefGateV3)
    # Missing provenance is a conservative ASK in V3, never USE.
    m=_mem('u','sushi',[])
    assert e.belief_gate.decide(m,context='food',now='2000-06-15T00:00:00+00:00').action==PersonalizationAction.ASK


def test_gate_version_can_reproduce_frozen_variants(tmp_path):
    assert PersonalMemoryEngine(tmp_path/'v1.db',gate_version='v1').belief_gate_version=='v1'
    assert PersonalMemoryEngine(tmp_path/'v2.db',gate_version='v2').belief_gate_version=='v2'


def test_exhaustive_modelcheck_production_has_no_declared_property_violations():
    r=run_modelcheck()
    assert r['n_states_per_gate']==9600
    assert r['production_all_properties_hold'] is True
    prod=next(x for x in r['systems'] if x['gate']=='DecisionAwareBeliefGateV3')
    assert prod['n_property_violations']==0
    assert all(prod['properties'].values())


def test_hard_forget_is_provenance_safe_and_atomic(tmp_path):
    db=tmp_path/'privacy.db'; e=PersonalMemoryEngine(db)
    ev_shared=Event(user_id='u',raw_text='I like sushi and tea.')
    ev_extra=Event(user_id='u',raw_text='Tea is especially important.')
    e.events.add(ev_shared); e.events.add(ev_extra)
    target=_mem('u','sushi',[ev_shared.id])
    sibling_only=_mem('u','tea',[ev_shared.id])
    sibling_multi=_mem('u','green tea',[ev_shared.id,ev_extra.id])
    for m in (target,sibling_only,sibling_multi): e.memories.add(m)

    assert e.forget_memory(target.id,delete_source_events=True)
    assert e.events.get(ev_shared.id) is None
    assert e.memories.get(target.id) is None
    assert e.memories.get(sibling_only.id) is None
    kept=e.memories.get(sibling_multi.id)
    assert kept is not None and kept.source_event_ids==[ev_extra.id]
    assert audit_database(db)['ok'] is True


def test_complete_user_export_contains_events_memories_state_and_gate(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'export.db')
    e.ingest('alice','I love sushi.')
    out=e.export_user_data('alice')
    assert out['user_id']=='alice'
    assert out['gate_version']=='v3'
    assert len(out['events'])==1
    assert len(out['memories'])>=1
    assert isinstance(out['state'],dict)
    assert all(x['user_id']=='alice' for x in out['events'])
    assert all(x['user_id']=='alice' for x in out['memories'])


def test_concurrent_ingest_preserves_isolation_and_integrity(tmp_path):
    db=tmp_path/'concurrent.db'; e=PersonalMemoryEngine(db)
    users=[f'u{i}' for i in range(8)]
    def work(user):
        for j in range(20):
            e.ingest(user,f'I prefer concise answers number {j}.')
        return user
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert set(pool.map(work,users))==set(users)
    for u in users:
        assert all(m.user_id==u for m in e.memories.list_all(u))
        assert all(ev.user_id==u for ev in e.events.list_for_user(u,limit=None))
    assert audit_database(db)['ok'] is True


def test_hard_forget_repairs_conflicts_and_supersedes_relations(tmp_path):
    db=tmp_path/'relation-delete.db'; e=PersonalMemoryEngine(db)
    ev1=Event(user_id='u',raw_text='source one'); ev2=Event(user_id='u',raw_text='source two'); ev3=Event(user_id='u',raw_text='source three')
    for ev in (ev1,ev2,ev3): e.events.add(ev)
    target=_mem('u','sushi',[ev1.id])
    conflict=_mem('u','ramen',[ev2.id]); conflict.conflicts_with=[target.id]
    target.conflicts_with=[conflict.id]
    successor=_mem('u','udon',[ev3.id]); successor.supersedes=target.id
    for m in (target,conflict,successor): e.memories.add(m)
    assert e.forget_memory(target.id,delete_source_events=True)
    conflict2=e.memories.get(conflict.id); successor2=e.memories.get(successor.id)
    assert conflict2 is not None and target.id not in conflict2.conflicts_with
    assert successor2 is not None and successor2.supersedes is None
    assert audit_database(db)['ok'] is True
