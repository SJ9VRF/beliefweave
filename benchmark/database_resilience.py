"""Process-level SQLite resilience checks for the BeliefWeave reference runtime.

These checks deliberately exercise the persistence boundary outside a single
Python process: concurrent writers open independent engine instances, and a
worker is terminated with an uncommitted transaction to verify crash rollback.
They validate the SQLite reference implementation, not distributed production
storage semantics.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from pwm.engine import PersonalMemoryEngine
from pwm.integrity import audit_database


def _writer(db_path: str, worker_id: int, operations: int, queue: mp.Queue) -> None:
    try:
        engine = PersonalMemoryEngine(db_path)
        user = f"worker-{worker_id}"
        for index in range(operations):
            engine.ingest(
                user,
                f"I prefer response style {worker_id}-{index}.",
                idempotency_key=f"worker-{worker_id}-{index}",
            )
        queue.put({"worker": worker_id, "ok": True})
    except Exception as exc:  # pragma: no cover - reported to parent process
        queue.put({"worker": worker_id, "ok": False, "error": repr(exc)})


def multiprocess_check(db_path: Path, workers: int = 4, operations: int = 20) -> dict:
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    processes = [
        ctx.Process(target=_writer, args=(str(db_path), wid, operations, queue))
        for wid in range(workers)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(60)
    reports = [queue.get(timeout=5) for _ in processes]
    exitcodes = [process.exitcode for process in processes]
    queue.close()
    queue.join_thread()
    for process in processes:
        process.close()

    engine = PersonalMemoryEngine(db_path)
    counts = {
        f"worker-{wid}": len(engine.events.list_for_user(f"worker-{wid}", limit=None))
        for wid in range(workers)
    }
    expected = workers * operations
    observed = sum(counts.values())
    integrity = audit_database(str(db_path))
    return {
        "workers": workers,
        "operations_per_worker": operations,
        "expected_events": expected,
        "observed_events": observed,
        "per_user_event_counts": counts,
        "worker_reports": sorted(reports, key=lambda item: item["worker"]),
        "all_processes_exited": all(code == 0 for code in exitcodes),
        "integrity_ok": integrity["ok"],
        "pass": (
            all(code == 0 for code in exitcodes)
            and all(r["ok"] for r in reports)
            and observed == expected
            and all(value == operations for value in counts.values())
            and integrity["ok"]
        ),
    }


def crash_recovery_check(db_path: Path) -> dict:
    # Initialize schema in the parent, then kill a separate interpreter with an
    # open transaction after it has inserted both an event and a memory row.
    PersonalMemoryEngine(db_path)
    code = r'''
import os, sys
from pwm.engine import PersonalMemoryEngine
from pwm.memory.schema import Event, MemoryRecord, MemoryType, SourceType

db = sys.argv[1]
engine = PersonalMemoryEngine(db)
event = Event(user_id="crash-user", raw_text="uncommitted crash payload")
memory = MemoryRecord(
    user_id="crash-user",
    subject="user",
    predicate="preference",
    value="uncommitted",
    memory_type=MemoryType.PREFERENCE,
    source_type=SourceType.EXPLICIT,
    confidence=1.0,
    source_event_ids=[event.id],
)
with engine.memories.transaction(immediate=True) as conn:
    engine.events.add(event, conn=conn)
    engine.memories.add(memory, conn=conn)
    os._exit(86)
'''
    proc = subprocess.run(
        [sys.executable, "-c", code, str(db_path)],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        check=False,
    )
    engine = PersonalMemoryEngine(db_path)
    events = engine.events.list_for_user("crash-user", limit=None)
    memories = engine.memories.list_all("crash-user")
    integrity = audit_database(str(db_path))
    return {
        "crash_exit_code": proc.returncode,
        "events_after_recovery": len(events),
        "memories_after_recovery": len(memories),
        "integrity_ok": integrity["ok"],
        "pass": (
            proc.returncode == 86
            and len(events) == 0
            and len(memories) == 0
            and integrity["ok"]
        ),
    }


def run(output: Path | None = None) -> dict:
    with tempfile.TemporaryDirectory(prefix="beliefweave-resilience-") as tmp:
        root = Path(tmp)
        result = {
            "scope": (
                "SQLite reference-runtime process resilience; this is not a "
                "distributed-database or production durability claim."
            ),
            "multiprocess": multiprocess_check(root / "multi.db"),
            "crash_recovery": crash_recovery_check(root / "crash.db"),
        }
        result["pass"] = all(
            result[name]["pass"] for name in ("multiprocess", "crash_recovery")
        )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/database_resilience.json"))
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
