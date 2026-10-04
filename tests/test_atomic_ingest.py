from __future__ import annotations

import pytest

from pwm.engine import PersonalMemoryEngine
from pwm.memory.schema import MemoryStatus
from pwm.integrity import audit_database


def test_ingest_rolls_back_event_and_memory_if_memory_write_fails(tmp_path, monkeypatch):
    db = tmp_path / "atomic.db"
    e = PersonalMemoryEngine(db)
    original = e.memories.add

    def insert_then_fail(memory, *, conn=None):
        original(memory, conn=conn)
        raise RuntimeError("injected failure after memory insert")

    monkeypatch.setattr(e.memories, "add", insert_then_fail)
    with pytest.raises(RuntimeError, match="injected failure"):
        e.ingest("u", "I love sushi.", context="food")

    assert e.events.list_for_user("u", limit=None) == []
    assert e.memories.list_all("u") == []
    assert audit_database(db)["ok"] is True


def test_ingest_rolls_back_conflict_updates_and_preserves_prior_state(tmp_path, monkeypatch):
    db = tmp_path / "conflict.db"
    e = PersonalMemoryEngine(db)
    first = e.ingest("u", "I love sushi.", context="food")
    old_id = next(a["memory"].id for a in first["actions"] if a["memory"])
    before_events = [x.id for x in e.events.list_for_user("u", limit=None)]
    before_memories = [(m.id, m.status, m.value, tuple(m.conflicts_with)) for m in e.memories.list_all("u")]

    original_classify = e.conflicts.classify
    calls = {"n": 0}

    def fail_after_conflict_read(old, obs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("injected conflict failure")
        return original_classify(old, obs)

    monkeypatch.setattr(e.conflicts, "classify", fail_after_conflict_read)
    with pytest.raises(RuntimeError, match="conflict failure"):
        e.ingest("u", "I dislike sushi.", context="food")

    after_events = [x.id for x in e.events.list_for_user("u", limit=None)]
    after_memories = [(m.id, m.status, m.value, tuple(m.conflicts_with)) for m in e.memories.list_all("u")]
    assert after_events == before_events
    assert after_memories == before_memories
    assert e.memories.get(old_id).status == MemoryStatus.ACTIVE
    assert audit_database(db)["ok"] is True
