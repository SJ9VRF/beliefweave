from __future__ import annotations

import argparse
import json
import os
import platform
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any

from pwm.engine import PersonalMemoryEngine
from pwm.schema_version import read_schema_version, CURRENT_SCHEMA_VERSION
from pwm.integrity import audit_database


def _json(obj: Any) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True))


def _state_to_dict(state):
    return {
        k: [
            {
                "value": x.value,
                "confidence": x.confidence,
                "memory_id": x.memory_id,
                "valid_until": x.valid_until,
                "context": x.context_scope,
                "provenance": x.provenance,
            }
            for x in v
        ]
        for k, v in state.items()
    }


def _default_db() -> str:
    root = Path(os.environ.get("PWM_HOME", Path.home() / ".pwm"))
    root.mkdir(parents=True, exist_ok=True)
    return str(root / "memory.db")


def _demo_payload() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="pwm-demo-") as td:
        db = Path(td) / "demo.db"
        e = PersonalMemoryEngine(db)
        user = "demo-user"
        first = e.ingest(user, "I love sushi.")
        second = e.ingest(user, "Actually, I dislike sushi.")
        recall = e.recall(user, "What food do I like?", limit=3)
        before_forget = [m.to_dict() for m in e.memories.list_all(user)]
        active = e.memories.list_active(user)
        target = active[0] if active else None
        forgotten = False
        if target:
            forgotten = e.forget_memory(target.id, delete_source_events=True)
        after_forget = [m.to_dict() for m in e.memories.list_all(user)]
        return {
            "scenario": "preference reversal + retrieval + hard forget",
            "first_actions": len(first["actions"]),
            "second_actions": len(second["actions"]),
            "state_after_reversal": _state_to_dict(second["state"]),
            "recall": [
                {"score": r.score, "value": r.memory.value, "reasons": r.reasons}
                for r in recall
            ],
            "memory_count_before_forget": len(before_forget),
            "hard_forget_ok": forgotten,
            "memory_count_after_forget": len(after_forget),
        }


def _benchmark_payload() -> dict[str, Any]:
    """Small deterministic installed-package benchmark; intentionally not the full research suite."""
    cases = [
        ("I love sushi.", "Actually, I dislike sushi.", "dislikes sushi"),
        ("I like running.", "Actually, I dislike running.", "dislikes running"),
        ("I love coffee.", "Actually, I dislike coffee.", "dislikes coffee"),
        ("I like jazz.", "Actually, I dislike jazz.", "dislikes jazz"),
    ]
    passed = 0
    details = []
    with tempfile.TemporaryDirectory(prefix="pwm-bench-") as td:
        for i, (a, b, expected) in enumerate(cases):
            e = PersonalMemoryEngine(Path(td) / f"case-{i}.db")
            user = f"u{i}"
            e.ingest(user, a)
            e.ingest(user, b)
            active = e.memories.list_active(user)
            entity = expected.split(" ", 1)[1]
            active_pairs = [(m.predicate, m.value) for m in active]
            ok = ("dislikes", entity) in active_pairs and ("likes", entity) not in active_pairs
            passed += int(ok)
            details.append({"case": i, "entity": entity, "active": active_pairs, "pass": ok})
    return {
        "name": "installed-package smoke benchmark",
        "cases": len(cases),
        "passed": passed,
        "pass_rate": passed / len(cases),
        "details": details,
        "note": "This is a packaging sanity benchmark, not MemWorldBench.",
    }


def _doctor_payload(db_path: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "db_path": str(Path(db_path).expanduser()),
        "checks": {},
    }

    ml_dependencies_available = True
    try:
        import sklearn
        payload["checks"]["scikit_learn"] = {
            "ok": True,
            "required": False,
            "version": sklearn.__version__,
        }
    except Exception as exc:
        ml_dependencies_available = False
        payload["checks"]["scikit_learn"] = {
            "ok": False,
            "required": False,
            "error": str(exc),
        }
    try:
        import joblib
        payload["checks"]["joblib"] = {
            "ok": True,
            "required": False,
            "version": joblib.__version__,
        }
    except Exception as exc:
        ml_dependencies_available = False
        payload["checks"]["joblib"] = {
            "ok": False,
            "required": False,
            "error": str(exc),
        }

    try:
        core = PersonalMemoryEngine(db_path, enable_ml=False)
        payload["checks"]["core_runtime"] = {
            "ok": core.runtime_capabilities()["ml_enabled"] is False,
            "required": True,
            **core.runtime_capabilities(),
        }
        with closing(sqlite3.connect(core.memories.db_path)) as conn:
            mem_cols = {r[1] for r in conn.execute("PRAGMA table_info(memories)").fetchall()}
            event_cols = {r[1] for r in conn.execute("PRAGMA table_info(events)").fetchall()}
            schema_version = read_schema_version(conn)
        payload["checks"]["database"] = {
            "ok": schema_version == CURRENT_SCHEMA_VERSION,
            "required": True,
            "schema_version": schema_version,
            "supported_schema_version": CURRENT_SCHEMA_VERSION,
            "memory_columns": len(mem_cols),
            "event_columns": len(event_cols),
        }

        assets = Path(__file__).resolve().parent / "assets"
        learned_assets_ok = False
        extractor = None
        conflict_resolver = None
        if ml_dependencies_available:
            ml_runtime = PersonalMemoryEngine(db_path, enable_ml=True)
            extractor = ml_runtime.extractor.__class__.__name__
            conflict_resolver = ml_runtime.conflicts.__class__.__name__
            learned_assets_ok = (
                extractor == "HybridObservationExtractor"
                and conflict_resolver == "HybridConflictResolver"
            )
        payload["checks"]["learned_assets"] = {
            "ok": learned_assets_ok,
            "required": False,
            "available": ml_dependencies_available,
            "extractor": extractor,
            "conflict_resolver": conflict_resolver,
        }

        integrity = audit_database(db_path)
        payload["checks"]["integrity"] = {
            "ok": integrity["ok"],
            "required": True,
            "errors": integrity["error_count"],
            "warnings": integrity["warning_count"],
        }
    except Exception as exc:
        payload["checks"]["database"] = {
            "ok": False,
            "required": True,
            "error": str(exc),
        }

    payload["ok"] = all(
        check.get("ok", False)
        for check in payload["checks"].values()
        if check.get("required", True)
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pwm", description="BeliefWeave command line interface")
    p.add_argument("--db", default=_default_db(), help="SQLite database path (default: ~/.pwm/memory.db)")
    p.add_argument("--user", default="demo-user", help="user identifier")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("ingest", help="ingest one user utterance")
    a.add_argument("text")
    a.add_argument("--context")
    a.add_argument("--timestamp")

    a = sub.add_parser("recall", help="retrieve relevant active memories")
    a.add_argument("query")
    a.add_argument("--context")
    a.add_argument("--limit", type=int, default=5)

    sub.add_parser("state", help="materialize current user state")
    sub.add_parser("memories", help="list all memories, including lifecycle state")

    a = sub.add_parser("forget", help="forget a memory")
    a.add_argument("memory_id")
    a.add_argument("--hard", action="store_true", help="purge memory row and source event(s)")

    a = sub.add_parser("correct", help="user-correct a memory value")
    a.add_argument("memory_id")
    a.add_argument("value")

    sub.add_parser("demo", help="run an end-to-end temporary-database demo")
    sub.add_parser("benchmark", help="run a tiny installed-package sanity benchmark")
    sub.add_parser("doctor", help="validate dependencies, DB schema, and packaged learned assets")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "demo":
        _json(_demo_payload())
        return 0
    if args.cmd == "benchmark":
        payload = _benchmark_payload()
        _json(payload)
        return 0 if payload["pass_rate"] == 1.0 else 1
    if args.cmd == "doctor":
        payload = _doctor_payload(args.db)
        _json(payload)
        return 0 if payload["ok"] else 2

    e = PersonalMemoryEngine(args.db)
    if args.cmd == "ingest":
        r = e.ingest(args.user, args.text, context=args.context, timestamp=args.timestamp)
        _json({
            "event": r["event"].to_dict(),
            "actions": [
                {
                    "decision": x["policy"].decision.value,
                    "score": x["policy"].score,
                    "memory": x["memory"].to_dict() if x["memory"] else None,
                    "conflicts": x["conflicts"],
                }
                for x in r["actions"]
            ],
            "state": _state_to_dict(r["state"]),
        })
    elif args.cmd == "recall":
        _json([
            {"score": r.score, "memory": r.memory.to_dict(), "reasons": r.reasons}
            for r in e.recall(args.user, args.query, args.limit, args.context)
        ])
    elif args.cmd == "state":
        _json(_state_to_dict(e.current_state(args.user)))
    elif args.cmd == "memories":
        _json([m.to_dict() for m in e.memories.list_all(args.user)])
    elif args.cmd == "forget":
        ok = e.forget_memory(args.memory_id, delete_source_events=args.hard)
        _json({"ok": ok, "hard": bool(args.hard), "memory_id": args.memory_id})
        return 0 if ok else 1
    elif args.cmd == "correct":
        try:
            corrected = e.correct_memory(args.memory_id, args.value)
        except Exception as exc:
            _json({"ok": False, "memory_id": args.memory_id, "error": str(exc)})
            return 1
        if corrected is None:
            _json({"ok": False, "memory_id": args.memory_id, "error": "memory not found"})
            return 1
        _json({"ok": True, "memory": corrected.to_dict()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
