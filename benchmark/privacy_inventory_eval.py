"""Focused assurance checks for user-scoped data inventory and erasure semantics."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from pwm.engine import PersonalMemoryEngine
from pwm.integrity import audit_database


def run(output: Path | None = None) -> dict:
    with tempfile.TemporaryDirectory(prefix="beliefweave-privacy-inventory-") as tmp:
        root = Path(tmp)

        events_a: list[dict] = []
        events_b: list[dict] = []
        engine_a = PersonalMemoryEngine(
            root / "telemetry-a.db",
            observer=events_a.append,
            observer_hmac_key=b"A" * 32,
        )
        engine_b = PersonalMemoryEngine(
            root / "telemetry-b.db",
            observer=events_b.append,
            observer_hmac_key=b"B" * 32,
        )
        user = "user@example.com"
        engine_a.ingest(user, "I like tea.", idempotency_key="inventory-1")
        engine_b.ingest(user, "I like tea.")
        key_a = next(item["user_key"] for item in events_a if "user_key" in item)
        key_b = next(item["user_key"] for item in events_b if "user_key" in item)

        exported = engine_a.export_user_data(user)
        receipt = exported["control_metadata"]["ingest_receipts"][0]
        export_complete = (
            bool(exported["events"])
            and bool(exported["memories"])
            and len(receipt["idempotency_key_digest"]) == 64
        )

        full = engine_a.purge_user_data(user)
        after_full = engine_a.export_user_data(user)
        full_erasure = (
            full["complete_erasure"]
            and not after_full["events"]
            and not after_full["memories"]
            and not after_full["control_metadata"]["ingest_receipts"]
            and audit_database(root / "telemetry-a.db")["ok"]
        )

        guarded = PersonalMemoryEngine(root / "guarded.db")
        guarded.ingest(user, "I prefer short answers.", idempotency_key="guard-1")
        guard_result = guarded.purge_user_data(user, retain_replay_guard=True)
        guard_export = guarded.export_user_data(user)
        guard_receipt = guard_export["control_metadata"]["ingest_receipts"][0]
        guarded_erasure = (
            not guard_result["complete_erasure"]
            and not guard_export["events"]
            and not guard_export["memories"]
            and guard_receipt["tombstoned"]
            and guard_receipt["request_hash"] == ""
            and guard_receipt["event_id"] == ""
            and audit_database(root / "guarded.db")["ok"]
        )

        telemetry_keyed = (
            key_a != key_b
            and user not in repr(events_a)
            and user not in repr(events_b)
            and len(key_a) == 16
            and len(key_b) == 16
        )

        result = {
            "scope": (
                "Local reference-runtime privacy controls. This is not a legal "
                "compliance certification or proof of deletion from backups or "
                "external systems."
            ),
            "export_includes_control_metadata": export_complete,
            "full_user_erasure_leaves_no_user_rows": full_erasure,
            "guarded_erasure_retains_only_scrubbed_replay_markers": guarded_erasure,
            "telemetry_identifiers_are_keyed_and_content_free": telemetry_keyed,
            "pass": all(
                (export_complete, full_erasure, guarded_erasure, telemetry_keyed)
            ),
        }

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/privacy_inventory.json"))
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
