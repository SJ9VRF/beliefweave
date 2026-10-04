from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pwm.engine import PersonalMemoryEngine
from pwm.integrity import audit_database


def main() -> None:
    results = []
    with tempfile.TemporaryDirectory(prefix="beliefweave-atomicity-") as td:
        root = Path(td)

        # Failure after a memory row has been inserted into the caller-owned transaction.
        db = root / "memory-write.db"
        engine = PersonalMemoryEngine(db)
        original_add = engine.memories.add

        def insert_then_fail(memory, *, conn=None):
            original_add(memory, conn=conn)
            raise RuntimeError("fault after memory insert")

        engine.memories.add = insert_then_fail  # type: ignore[method-assign]
        try:
            engine.ingest("u", "I love sushi.", context="food")
        except RuntimeError:
            pass
        events = engine.events.list_for_user("u", limit=None)
        memories = engine.memories.list_all("u")
        results.append({
            "fault": "after_memory_insert",
            "events_after_rollback": len(events),
            "memories_after_rollback": len(memories),
            "integrity_ok": audit_database(db)["ok"],
            "passed": len(events) == 0 and len(memories) == 0 and audit_database(db)["ok"],
        })

        # Failure after a pre-existing state exists and a second ingest has begun.
        db2 = root / "conflict.db"
        engine2 = PersonalMemoryEngine(db2)
        first = engine2.ingest("u", "I love sushi.", context="food")
        old_id = next(a["memory"].id for a in first["actions"] if a["memory"])
        before_events = [e.id for e in engine2.events.list_for_user("u", limit=None)]
        before_memories = [(m.id, m.status.value, m.value, tuple(m.conflicts_with)) for m in engine2.memories.list_all("u")]

        def fail_conflict(old, obs):
            raise RuntimeError("fault during conflict resolution")

        engine2.conflicts.classify = fail_conflict  # type: ignore[method-assign]
        try:
            engine2.ingest("u", "I dislike sushi.", context="food")
        except RuntimeError:
            pass
        after_events = [e.id for e in engine2.events.list_for_user("u", limit=None)]
        after_memories = [(m.id, m.status.value, m.value, tuple(m.conflicts_with)) for m in engine2.memories.list_all("u")]
        old = engine2.memories.get(old_id)
        results.append({
            "fault": "during_conflict_resolution",
            "event_state_unchanged": after_events == before_events,
            "memory_state_unchanged": after_memories == before_memories,
            "prior_memory_still_active": bool(old and old.status.value == "active"),
            "integrity_ok": audit_database(db2)["ok"],
            "passed": after_events == before_events and after_memories == before_memories and bool(old and old.status.value == "active") and audit_database(db2)["ok"],
        })

    payload = {
        "n_faults": len(results),
        "passed_faults": sum(r["passed"] for r in results),
        "all_pass": all(r["passed"] for r in results),
        "guarantee": "event, memory, conflict, and supersession writes are committed atomically per ingest",
        "faults": results,
    }
    out = Path(__file__).resolve().parents[1] / "results" / "atomicity_fault_injection.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
