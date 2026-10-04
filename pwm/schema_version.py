"""SQLite schema versioning and forward-only migrations for BeliefWeave.

Migrations are intentionally small, transactional, and idempotent.  Store-specific
CREATE TABLE statements remain close to their stores; cross-cutting schema features
that must be available before a store is initialized live here.
"""
from __future__ import annotations

import hashlib
import sqlite3

CURRENT_SCHEMA_VERSION = 4
META_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pwm_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""
MIGRATION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pwm_schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL
)
"""


def _migration_2(conn: sqlite3.Connection) -> None:
    """Add request-idempotency receipts shared by API/engine ingest paths."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ingest_receipts (
            user_id TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            request_hash TEXT NOT NULL,
            event_id TEXT NOT NULL,
            PRIMARY KEY (user_id, idempotency_key)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_ingest_receipts_event ON ingest_receipts(event_id)"
    )


def _migration_3(conn: sqlite3.Connection) -> None:
    """Prevent replay resurrection after privacy deletion via receipt tombstones."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(ingest_receipts)").fetchall()}
    if "tombstoned" not in cols:
        conn.execute("ALTER TABLE ingest_receipts ADD COLUMN tombstoned INTEGER NOT NULL DEFAULT 0")




def _migration_4(conn: sqlite3.Connection) -> None:
    """Replace plaintext idempotency keys with deterministic SHA-256 digests."""
    rows = conn.execute(
        "SELECT user_id, idempotency_key FROM ingest_receipts"
    ).fetchall()
    for user_id, key in rows:
        digest = hashlib.sha256(str(key).encode("utf-8")).hexdigest()
        conn.execute(
            """
            UPDATE ingest_receipts
            SET idempotency_key=?
            WHERE user_id=? AND idempotency_key=?
            """,
            (digest, user_id, key),
        )

_MIGRATIONS: dict[int, tuple[str, callable]] = {
    2: ("ingest_idempotency_receipts", _migration_2),
    3: ("idempotency_tombstones", _migration_3),
    4: ("hashed_idempotency_keys", _migration_4),
}


def ensure_schema_version(conn: sqlite3.Connection) -> int:
    """Bring a database to the current schema version in the caller transaction."""
    conn.execute(META_TABLE_SQL)
    conn.execute(MIGRATION_TABLE_SQL)
    row = conn.execute("SELECT value FROM pwm_meta WHERE key='schema_version'").fetchone()
    if row is None:
        # New databases start at v1 semantics, then run the same forward migrations
        # as legacy databases.  This keeps migration paths exercised in normal use.
        conn.execute(
            "INSERT INTO pwm_meta(key,value) VALUES('schema_version','1')"
        )
        version = 1
    else:
        version = int(row[0])

    if version > CURRENT_SCHEMA_VERSION:
        raise RuntimeError(
            f"Database schema {version} is newer than supported schema {CURRENT_SCHEMA_VERSION}."
        )

    while version < CURRENT_SCHEMA_VERSION:
        target = version + 1
        try:
            name, migration = _MIGRATIONS[target]
        except KeyError as exc:  # defensive: never silently skip a migration
            raise RuntimeError(f"No migration registered for schema {version}->{target}") from exc
        migration(conn)
        conn.execute(
            "INSERT OR IGNORE INTO pwm_schema_migrations(version,name) VALUES(?,?)",
            (target, name),
        )
        conn.execute(
            "UPDATE pwm_meta SET value=? WHERE key='schema_version'",
            (str(target),),
        )
        version = target
    return version


def read_schema_version(conn: sqlite3.Connection) -> int | None:
    try:
        row = conn.execute("SELECT value FROM pwm_meta WHERE key='schema_version'").fetchone()
    except sqlite3.OperationalError:
        return None
    return int(row[0]) if row else None
