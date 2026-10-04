from pathlib import Path

from beliefweave import PersonalMemoryEngine


def test_observer_emits_no_raw_user_content(tmp_path: Path):
    events = []
    engine = PersonalMemoryEngine(tmp_path / "obs.db", enable_ml=False, observer=events.append)
    secret = "I love saffron risotto and my secret code is ALPHA-42"
    engine.ingest("private-user@example.com", secret, idempotency_key="obs-1")
    engine.recall("private-user@example.com", "food")

    assert events
    serialized = repr(events)
    assert secret not in serialized
    assert "private-user@example.com" not in serialized
    assert "ALPHA-42" not in serialized
    assert any(event["event"] == "ingest_committed" for event in events)
    assert all(len(event.get("user_key", "")) in {0, 16} for event in events)


def test_observer_failure_cannot_break_memory_semantics(tmp_path: Path):
    def broken_observer(_event):
        raise RuntimeError("telemetry backend unavailable")

    engine = PersonalMemoryEngine(
        tmp_path / "observer-failure.db",
        enable_ml=False,
        observer=broken_observer,
    )
    out = engine.ingest("u", "I love sushi.")
    assert out["event"].user_id == "u"
    assert engine.current_state("u")


def test_core_runtime_capabilities_are_explicit(tmp_path: Path):
    engine = PersonalMemoryEngine(tmp_path / "core.db", enable_ml=False)
    caps = engine.runtime_capabilities()
    assert caps == {
        "gate_version": engine.belief_gate_version,
        "ml_enabled": False,
        "retriever": "MemoryRetriever",
        "extractor": "RuleBasedObservationExtractor",
        "conflict_resolver": "ConflictResolver",
    }
