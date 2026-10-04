from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from pwm.memory.schema import (
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    SourceType,
    utcnow_iso,
)
from pwm.schema_version import ensure_schema_version
from pwm.temporal import is_expired


class MemoryStore:
    """SQLite-backed reference store for typed memory records."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=30000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def transaction(self, *, immediate: bool = True) -> Iterator[sqlite3.Connection]:
        """Open a caller-owned transaction spanning event and memory writes."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=30000")
        try:
            conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            ensure_schema_version(conn)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    value TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source_event_ids_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    valid_from TEXT,
                    valid_until TEXT,
                    stability REAL NOT NULL,
                    importance REAL NOT NULL,
                    context_scope TEXT,
                    status TEXT NOT NULL,
                    supersedes TEXT,
                    conflicts_with_json TEXT NOT NULL,
                    retrieval_count INTEGER NOT NULL,
                    last_used_at TEXT,
                    user_verified INTEGER NOT NULL,
                    privacy_level TEXT NOT NULL,
                    correction_count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(memories)").fetchall()
            }
            if "correction_count" not in columns:
                conn.execute(
                    "ALTER TABLE memories ADD COLUMN correction_count "
                    "INTEGER NOT NULL DEFAULT 0"
                )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mem_user_status "
                "ON memories(user_id, status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mem_pred "
                "ON memories(user_id, predicate, status)"
            )

    @staticmethod
    def _insert(conn: sqlite3.Connection, memory: MemoryRecord) -> None:
        conn.execute(
            """
            INSERT INTO memories (
                id, user_id, subject, predicate, value, memory_type, source_type,
                confidence, source_event_ids_json, created_at, updated_at,
                valid_from, valid_until, stability, importance, context_scope,
                status, supersedes, conflicts_with_json, retrieval_count,
                last_used_at, user_verified, privacy_level, correction_count
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                memory.id,
                memory.user_id,
                memory.subject,
                memory.predicate,
                memory.value,
                memory.memory_type.value,
                memory.source_type.value,
                memory.confidence,
                json.dumps(memory.source_event_ids),
                memory.created_at,
                memory.updated_at,
                memory.valid_from,
                memory.valid_until,
                memory.stability,
                memory.importance,
                memory.context_scope,
                memory.status.value,
                memory.supersedes,
                json.dumps(memory.conflicts_with),
                memory.retrieval_count,
                memory.last_used_at,
                int(memory.user_verified),
                memory.privacy_level,
                memory.correction_count,
            ),
        )

    def add(
        self,
        memory: MemoryRecord,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> MemoryRecord:
        if conn is not None:
            self._insert(conn, memory)
            return memory
        with self._connect() as local:
            self._insert(local, memory)
        return memory

    def get(
        self,
        memory_id: str,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> MemoryRecord | None:
        if conn is not None:
            row = conn.execute(
                "SELECT * FROM memories WHERE id=?", (memory_id,)
            ).fetchone()
            return self._row(row) if row else None
        with self._connect() as local:
            row = local.execute(
                "SELECT * FROM memories WHERE id=?", (memory_id,)
            ).fetchone()
        return self._row(row) if row else None

    def list_all(
        self,
        user_id: str,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> list[MemoryRecord]:
        query = "SELECT * FROM memories WHERE user_id=? ORDER BY created_at"
        if conn is not None:
            rows = conn.execute(query, (user_id,)).fetchall()
            return [self._row(row) for row in rows]
        with self._connect() as local:
            rows = local.execute(query, (user_id,)).fetchall()
        return [self._row(row) for row in rows]

    def expire_due(
        self,
        user_id: str,
        now: str | None = None,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> int:
        changed = 0
        for memory in self.list_all(user_id, conn=conn):
            if memory.status == MemoryStatus.ACTIVE and is_expired(
                memory.valid_until, now
            ):
                self.set_status(memory.id, MemoryStatus.EXPIRED, conn=conn)
                changed += 1
        return changed

    def list_active(
        self,
        user_id: str,
        now: str | None = None,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> list[MemoryRecord]:
        self.expire_due(user_id, now, conn=conn)
        query = (
            "SELECT * FROM memories WHERE user_id=? AND status=? "
            "ORDER BY updated_at DESC"
        )
        params = (user_id, MemoryStatus.ACTIVE.value)
        if conn is not None:
            rows = conn.execute(query, params).fetchall()
            return [self._row(row) for row in rows]
        with self._connect() as local:
            rows = local.execute(query, params).fetchall()
        return [self._row(row) for row in rows]

    def set_status(
        self,
        memory_id: str,
        status: MemoryStatus,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> None:
        params = (status.value, utcnow_iso(), memory_id)
        if conn is not None:
            conn.execute(
                "UPDATE memories SET status=?, updated_at=? WHERE id=?", params
            )
            return
        with self._connect() as local:
            local.execute(
                "UPDATE memories SET status=?, updated_at=? WHERE id=?", params
            )

    def supersede(
        self,
        old_id: str,
        new_id: str,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> None:
        def apply(local: sqlite3.Connection) -> None:
            now = utcnow_iso()
            local.execute(
                "UPDATE memories SET status=?, updated_at=? WHERE id=?",
                (MemoryStatus.SUPERSEDED.value, now, old_id),
            )
            local.execute(
                "UPDATE memories SET supersedes=?, updated_at=? WHERE id=?",
                (old_id, now, new_id),
            )

        if conn is not None:
            apply(conn)
            return
        with self._connect() as local:
            apply(local)

    def add_conflict(
        self,
        first_id: str,
        second_id: str,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> None:
        def apply(local: sqlite3.Connection) -> None:
            for memory_id, other_id in (
                (first_id, second_id),
                (second_id, first_id),
            ):
                memory = self.get(memory_id, conn=local)
                if memory is None or other_id in memory.conflicts_with:
                    continue
                conflicts = memory.conflicts_with + [other_id]
                local.execute(
                    """
                    UPDATE memories
                    SET conflicts_with_json=?, updated_at=?
                    WHERE id=?
                    """,
                    (json.dumps(conflicts), utcnow_iso(), memory_id),
                )

        if conn is not None:
            apply(conn)
            return
        with self._connect() as local:
            apply(local)

    def delete(self, memory_id: str) -> None:
        self.set_status(memory_id, MemoryStatus.DELETED)

    def purge(self, memory_id: str) -> None:
        """Irreversibly remove a row; explicit hard-forget flows only."""
        with self._connect() as conn:
            conn.execute("DELETE FROM memories WHERE id=?", (memory_id,))

    def set_source_event_ids(self, memory_id: str, event_ids: list[str]) -> None:
        """Replace provenance links after an explicit source purge."""
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE memories
                SET source_event_ids_json=?, updated_at=?
                WHERE id=?
                """,
                (json.dumps(event_ids), utcnow_iso(), memory_id),
            )

    def correct(
        self,
        memory_id: str,
        new_value: str,
        confidence: float = 1.0,
    ) -> None:
        """Low-level in-place correction retained for frozen experiments.

        New application code should call PersonalMemoryEngine.correct_memory()
        so corrections retain source-event provenance and version history.
        """
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE memories
                SET value=?, confidence=?, user_verified=1,
                    correction_count=correction_count+1, updated_at=?
                WHERE id=?
                """,
                (new_value, confidence, utcnow_iso(), memory_id),
            )

    def touch_retrieved(self, memory_id: str) -> None:
        now = utcnow_iso()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE memories
                SET retrieval_count=retrieval_count+1,
                    last_used_at=?, updated_at=?
                WHERE id=?
                """,
                (now, now, memory_id),
            )

    @staticmethod
    def _row(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            user_id=row["user_id"],
            subject=row["subject"],
            predicate=row["predicate"],
            value=row["value"],
            memory_type=MemoryType(row["memory_type"]),
            source_type=SourceType(row["source_type"]),
            confidence=row["confidence"],
            source_event_ids=json.loads(row["source_event_ids_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            valid_from=row["valid_from"],
            valid_until=row["valid_until"],
            stability=row["stability"],
            importance=row["importance"],
            context_scope=row["context_scope"],
            status=MemoryStatus(row["status"]),
            supersedes=row["supersedes"],
            conflicts_with=json.loads(row["conflicts_with_json"]),
            retrieval_count=row["retrieval_count"],
            last_used_at=row["last_used_at"],
            user_verified=bool(row["user_verified"]),
            privacy_level=row["privacy_level"],
            correction_count=row["correction_count"],
        )
