from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from pwm.memory.schema import Event
from pwm.schema_version import ensure_schema_version


class EventStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA busy_timeout=30000")
        try:
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
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    conversation_id TEXT,
                    modality TEXT NOT NULL,
                    context TEXT,
                    raw_text TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_user_time ON events(user_id, timestamp)")

    @staticmethod
    def _insert(conn: sqlite3.Connection, event: Event) -> None:
        conn.execute(
            """INSERT INTO events
            (id, user_id, timestamp, conversation_id, modality, context, raw_text, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event.id,
                event.user_id,
                event.timestamp,
                event.conversation_id,
                event.modality,
                event.context,
                event.raw_text,
                json.dumps(event.metadata, ensure_ascii=False),
            ),
        )

    def add(self, event: Event, *, conn: sqlite3.Connection | None = None) -> Event:
        """Persist an event, optionally participating in a caller-owned transaction."""
        if conn is not None:
            self._insert(conn, event)
            return event
        with self._connect() as local:
            self._insert(local, event)
        return event

    def get(self, event_id: str) -> Event | None:
        with self._connect() as conn:
            r = conn.execute(
                """SELECT id, user_id, timestamp, conversation_id, modality, context, raw_text, metadata_json
                FROM events WHERE id=?""",
                (event_id,),
            ).fetchone()
        if not r:
            return None
        return Event(
            id=r[0], user_id=r[1], timestamp=r[2], conversation_id=r[3], modality=r[4],
            context=r[5], raw_text=r[6], metadata=json.loads(r[7])
        )

    def list_for_user(self, user_id: str, limit: int | None = 100) -> list[Event]:
        with self._connect() as conn:
            if limit is None:
                rows = conn.execute(
                    """SELECT id, user_id, timestamp, conversation_id, modality, context, raw_text, metadata_json
                    FROM events WHERE user_id=? ORDER BY timestamp DESC""",
                    (user_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT id, user_id, timestamp, conversation_id, modality, context, raw_text, metadata_json
                    FROM events WHERE user_id=? ORDER BY timestamp DESC LIMIT ?""",
                    (user_id, limit),
                ).fetchall()
        return [
            Event(
                id=r[0], user_id=r[1], timestamp=r[2], conversation_id=r[3], modality=r[4],
                context=r[5], raw_text=r[6], metadata=json.loads(r[7])
            )
            for r in rows
        ]

    def delete(self, event_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM events WHERE id=?", (event_id,))
