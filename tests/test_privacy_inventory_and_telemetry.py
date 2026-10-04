from pathlib import Path

from beliefweave import PersonalMemoryEngine
from pwm.integrity import audit_database


def test_export_includes_persisted_control_metadata(tmp_path: Path):
    engine = PersonalMemoryEngine(tmp_path / "export-control.db")
    engine.ingest("alice", "I like tea.", idempotency_key="request-1")
    out = engine.export_user_data("alice")

    receipts = out["control_metadata"]["ingest_receipts"]
    assert len(receipts) == 1
    assert receipts[0]["idempotency_key_digest"] != "request-1"
    assert len(receipts[0]["idempotency_key_digest"]) == 64
    assert receipts[0]["tombstoned"] is False


def test_full_user_purge_leaves_no_persisted_rows(tmp_path: Path):
    engine = PersonalMemoryEngine(tmp_path / "full-purge.db")
    engine.ingest("alice", "I like tea.", idempotency_key="request-1")
    engine.ingest("bob", "I like jazz.", idempotency_key="request-bob")

    result = engine.purge_user_data("alice")
    assert result["complete_erasure"] is True
    assert result["purged_events"] == 1
    assert result["purged_receipts"] == 1

    exported = engine.export_user_data("alice")
    assert exported["events"] == []
    assert exported["memories"] == []
    assert exported["control_metadata"]["ingest_receipts"] == []
    assert engine.export_user_data("bob")["events"]
    assert audit_database(tmp_path / "full-purge.db")["ok"] is True


def test_user_purge_can_retain_minimal_replay_guards(tmp_path: Path):
    engine = PersonalMemoryEngine(tmp_path / "guarded-purge.db")
    engine.ingest("alice", "I like tea.", idempotency_key="request-1")

    result = engine.purge_user_data("alice", retain_replay_guard=True)
    assert result["complete_erasure"] is False
    assert result["retained_replay_guards"] == 1

    exported = engine.export_user_data("alice")
    assert exported["events"] == []
    assert exported["memories"] == []
    receipt = exported["control_metadata"]["ingest_receipts"][0]
    assert receipt["tombstoned"] is True
    assert receipt["request_hash"] == ""
    assert receipt["event_id"] == ""
    assert audit_database(tmp_path / "guarded-purge.db")["ok"] is True


def test_observer_identifiers_are_keyed_not_plain_sha256(tmp_path: Path):
    user_id = "alice@example.com"
    events_a = []
    events_b = []
    engine_a = PersonalMemoryEngine(
        tmp_path / "a.db",
        observer=events_a.append,
        observer_hmac_key=b"a" * 32,
    )
    engine_b = PersonalMemoryEngine(
        tmp_path / "b.db",
        observer=events_b.append,
        observer_hmac_key=b"b" * 32,
    )

    engine_a.ingest(user_id, "I like tea.")
    engine_a.recall(user_id, "tea")
    engine_b.ingest(user_id, "I like tea.")

    keys_a = {e["user_key"] for e in events_a if "user_key" in e}
    keys_b = {e["user_key"] for e in events_b if "user_key" in e}
    assert len(keys_a) == 1
    assert len(next(iter(keys_a))) == 16
    assert keys_a.isdisjoint(keys_b)
    assert user_id not in repr(events_a)


def test_observer_accepts_string_hmac_key_and_stable_process_correlation(tmp_path: Path):
    events = []
    engine = PersonalMemoryEngine(
        tmp_path / "string-key.db",
        observer=events.append,
        observer_hmac_key="stable-secret-for-tests",
    )
    engine.ingest("alice", "I like tea.")
    engine.recall("alice", "tea")
    keys = [event["user_key"] for event in events if "user_key" in event]
    assert len(keys) >= 2
    assert len(set(keys)) == 1


def test_observer_event_without_user_id_is_supported(tmp_path: Path):
    events = []
    engine = PersonalMemoryEngine(
        tmp_path / "observer-no-user.db",
        observer=events.append,
    )
    engine._emit("maintenance_tick", count=3)
    assert events == [
        {
            "event": "maintenance_tick",
            "gate_version": engine.belief_gate_version,
            "ml_enabled": False,
            "count": 3,
        }
    ]
