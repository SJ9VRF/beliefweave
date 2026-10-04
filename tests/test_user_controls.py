from pwm.engine import PersonalMemoryEngine

def test_delete_removes_from_state_and_recall(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'u.db'); out=e.ingest('u','I love sushi.')
    mid=out['actions'][0]['memory'].id
    e.memories.delete(mid)
    assert e.current_state('u')=={}
    assert e.recall('u','sushi')==[]

def test_correction_is_user_verified(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'u.db'); out=e.ingest('u','I love sushi.')
    mid=out['actions'][0]['memory'].id
    e.memories.correct(mid,'ramen')
    m=e.memories.get(mid)
    assert m.value=='ramen' and m.user_verified and m.correction_count==1

def test_contextual_preferences_coexist(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'u.db')
    e.ingest('u','I prefer formal tone.',context='work')
    e.ingest('u','I prefer casual tone.',context='friends')
    active=e.memories.list_active('u')
    assert len(active)==2

def test_dont_remember_is_not_written(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'u.db')
    out=e.ingest('u',"Don't remember that I like sushi.")
    assert not out['actions'] and e.memories.list_all('u')==[]

def test_hard_forget_can_delete_source_event(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'u.db')
    out=e.ingest('u','I love sushi.')
    mid=out['actions'][0]['memory'].id
    eid=out['event'].id
    assert e.forget_memory(mid,delete_source_events=True)
    assert all(ev.id!=eid for ev in e.events.list_for_user('u'))


def test_engine_correction_preserves_history_and_provenance(tmp_path):
    e = PersonalMemoryEngine(tmp_path / 'correction-history.db')
    out = e.ingest('u', 'I love sushi.')
    old = out['actions'][0]['memory']

    corrected = e.correct_memory(old.id, 'ramen', timestamp='2026-01-02T03:00:00Z')
    assert corrected is not None
    assert corrected.id != old.id
    assert corrected.value == 'ramen'
    assert corrected.user_verified is True
    assert corrected.correction_count == old.correction_count + 1
    assert corrected.supersedes == old.id
    assert corrected.valid_from == '2026-01-02T03:00:00+00:00'

    old_after = e.memories.get(old.id)
    assert old_after.status.value == 'superseded'
    assert len(corrected.source_event_ids) == 1
    event = e.events.get(corrected.source_event_ids[0])
    assert event is not None
    assert event.metadata['kind'] == 'memory_correction'
    assert event.metadata['target_memory_id'] == old.id

    replay = e.correct_memory(old.id, 'ramen')
    assert replay.id == corrected.id
    assert len(e.events.list_for_user('u', limit=None)) == 2


def test_correction_rejects_divergent_update_against_stale_version(tmp_path):
    from pwm.engine import MemoryStateConflictError

    e = PersonalMemoryEngine(tmp_path / 'stale-correction.db')
    out = e.ingest('u', 'I love sushi.')
    old = out['actions'][0]['memory']
    e.correct_memory(old.id, 'ramen')
    import pytest
    with pytest.raises(MemoryStateConflictError):
        e.correct_memory(old.id, 'udon')


def test_empty_correction_value_is_rejected(tmp_path):
    from pwm.engine import PersonalMemoryEngine

    engine = PersonalMemoryEngine(tmp_path / "empty-correction.db")
    out = engine.ingest("u", "I like sushi.")
    memory = next(action["memory"] for action in out["actions"] if action["memory"])
    try:
        engine.correct_memory(memory.id, "   ")
    except ValueError as exc:
        assert "must not be empty" in str(exc)
    else:
        raise AssertionError("blank corrections must fail")
