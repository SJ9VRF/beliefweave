from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pwm.schema_version import CURRENT_SCHEMA_VERSION, read_schema_version
from pwm.temporal import is_expired


@dataclass(slots=True)
class IntegrityIssue:
    severity: str
    code: str
    message: str
    entity_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_database(db_path: str | Path, *, now: str | None = None) -> dict[str, Any]:
    """Audit relational and lifecycle invariants without mutating the database.

    This is intentionally conservative: it checks provenance references, same-user
    relationships, schema compatibility, and lifecycle consistency. It is not a
    substitute for a security/privacy review.
    """
    path = str(db_path)
    issues: list[IntegrityIssue] = []
    with closing(sqlite3.connect(path)) as conn:
        conn.row_factory = sqlite3.Row
        version = read_schema_version(conn)
        if version != CURRENT_SCHEMA_VERSION:
            issues.append(IntegrityIssue(
                "error", "schema_version_mismatch",
                f"database schema={version}, supported={CURRENT_SCHEMA_VERSION}",
            ))

        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required={"events","memories","pwm_meta","pwm_schema_migrations","ingest_receipts"}
        if not required.issubset(tables):
            missing = sorted(required - tables)
            issues.append(IntegrityIssue("error", "missing_tables", f"missing tables: {missing}"))
            return _result(path, version, issues, 0, 0)

        events = {r["id"]: r for r in conn.execute("SELECT id,user_id FROM events")}
        memories = {r["id"]: r for r in conn.execute(
            "SELECT id,user_id,status,valid_until,supersedes,source_event_ids_json,conflicts_with_json FROM memories"
        )}
        receipts = list(conn.execute("SELECT user_id,idempotency_key,event_id,request_hash,tombstoned FROM ingest_receipts"))

        import json
        for mid, m in memories.items():
            try:
                source_ids = json.loads(m["source_event_ids_json"])
            except Exception:
                issues.append(IntegrityIssue("error", "invalid_source_json", "source_event_ids_json is invalid", mid))
                source_ids = []
            for eid in source_ids:
                ev = events.get(eid)
                if ev is None:
                    issues.append(IntegrityIssue("error", "orphan_source_event", f"missing source event {eid}", mid))
                elif ev["user_id"] != m["user_id"]:
                    issues.append(IntegrityIssue("error", "cross_user_provenance", f"source event {eid} belongs to another user", mid))

            sid = m["supersedes"]
            if sid:
                target = memories.get(sid)
                if target is None:
                    issues.append(IntegrityIssue("error", "orphan_supersedes", f"missing superseded memory {sid}", mid))
                elif target["user_id"] != m["user_id"]:
                    issues.append(IntegrityIssue("error", "cross_user_supersedes", f"superseded memory {sid} belongs to another user", mid))

            try:
                conflict_ids = json.loads(m["conflicts_with_json"])
            except Exception:
                issues.append(IntegrityIssue("error", "invalid_conflict_json", "conflicts_with_json is invalid", mid))
                conflict_ids = []
            for cid in conflict_ids:
                target = memories.get(cid)
                if target is None:
                    issues.append(IntegrityIssue("error", "orphan_conflict", f"missing conflicting memory {cid}", mid))
                elif target["user_id"] != m["user_id"]:
                    issues.append(IntegrityIssue("error", "cross_user_conflict", f"conflicting memory {cid} belongs to another user", mid))

            if m["status"] == "active" and is_expired(m["valid_until"], now):
                issues.append(IntegrityIssue("warning", "active_but_expired", "active memory is past valid_until; list_active() will expire it lazily", mid))

            for cid in conflict_ids:
                target = memories.get(cid)
                if target is not None:
                    try:
                        reverse = json.loads(target["conflicts_with_json"])
                    except Exception:
                        reverse = []
                    if mid not in reverse:
                        issues.append(IntegrityIssue("error", "asymmetric_conflict", f"conflict relation with {cid} is not symmetric", mid))

        seen_receipts=set()
        for r in receipts:
            key=(r["user_id"],r["idempotency_key"])
            if key in seen_receipts:
                issues.append(IntegrityIssue("error","duplicate_idempotency_key",f"duplicate receipt {key}"))
            seen_receipts.add(key)
            if len(r["idempotency_key"]) != 64:
                issues.append(IntegrityIssue(
                    "error",
                    "unhashed_idempotency_key",
                    "persisted idempotency key is not a SHA-256 digest",
                    r["event_id"],
                ))
            ev=events.get(r["event_id"]) if r["event_id"] else None
            if r["tombstoned"]:
                if ev is not None:
                    issues.append(IntegrityIssue("error","tombstone_event_still_present",f"tombstoned receipt still has live event {r['event_id']}"))
                if r["event_id"] or r["request_hash"]:
                    issues.append(IntegrityIssue(
                        "error",
                        "tombstone_not_scrubbed",
                        "tombstoned receipt retains event/request metadata",
                    ))
            elif ev is None:
                issues.append(IntegrityIssue("error","orphan_idempotency_receipt",f"missing event {r['event_id']}"))
            elif ev["user_id"] != r["user_id"]:
                issues.append(IntegrityIssue("error","cross_user_idempotency_receipt",f"event {r['event_id']} belongs to another user"))
            if not r["tombstoned"] and len(r["request_hash"]) != 64:
                issues.append(IntegrityIssue("error","invalid_request_hash","idempotency request hash is not SHA-256",r["event_id"]))

    return _result(path, version, issues, len(events), len(memories))


def _result(path: str, version: int | None, issues: list[IntegrityIssue], events: int, memories: int) -> dict[str, Any]:
    errors = sum(i.severity == "error" for i in issues)
    warnings = sum(i.severity == "warning" for i in issues)
    return {
        "db_path": path,
        "schema_version": version,
        "supported_schema_version": CURRENT_SCHEMA_VERSION,
        "events": events,
        "memories": memories,
        "ok": errors == 0,
        "error_count": errors,
        "warning_count": warnings,
        "issues": [i.to_dict() for i in issues],
    }
