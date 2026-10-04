import sqlite3
from contextlib import closing
from pathlib import Path
import pytest

from pwm.engine import PersonalMemoryEngine
from pwm.schema_version import CURRENT_SCHEMA_VERSION, read_schema_version


def test_new_database_records_schema_version(tmp_path: Path):
    db = tmp_path / "schema.db"
    PersonalMemoryEngine(db)
    with closing(sqlite3.connect(db)) as conn:
        assert read_schema_version(conn) == CURRENT_SCHEMA_VERSION


def test_newer_database_schema_is_rejected(tmp_path: Path):
    db = tmp_path / "future.db"
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("CREATE TABLE pwm_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        conn.execute("INSERT INTO pwm_meta(key,value) VALUES('schema_version','999')")
        conn.commit()
    with pytest.raises(RuntimeError, match="newer than supported"):
        PersonalMemoryEngine(db)


def test_v1_database_is_migrated_to_v2_with_receipts(tmp_path: Path):
    db = tmp_path / "legacy-v1.db"
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("CREATE TABLE pwm_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        conn.execute("INSERT INTO pwm_meta(key,value) VALUES('schema_version','1')")
        conn.commit()
    PersonalMemoryEngine(db)
    with closing(sqlite3.connect(db)) as conn:
        assert read_schema_version(conn) == CURRENT_SCHEMA_VERSION == 4
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert 'ingest_receipts' in tables
        row = conn.execute("SELECT name FROM pwm_schema_migrations WHERE version=2").fetchone()
        assert row == ('ingest_idempotency_receipts',)


def test_migration_is_idempotent(tmp_path: Path):
    db = tmp_path / "migrate-twice.db"
    PersonalMemoryEngine(db)
    PersonalMemoryEngine(db)
    with closing(sqlite3.connect(db)) as conn:
        assert read_schema_version(conn) == 4
        assert conn.execute("SELECT COUNT(*) FROM pwm_schema_migrations WHERE version IN (2,3,4)").fetchone()[0] == 3


def test_v3_receipts_are_migrated_to_hashed_keys(tmp_path: Path):
    import hashlib
    db = tmp_path / "legacy-v3.db"
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("CREATE TABLE pwm_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        conn.execute("INSERT INTO pwm_meta(key,value) VALUES('schema_version','3')")
        conn.execute("CREATE TABLE pwm_schema_migrations(version INTEGER PRIMARY KEY,name TEXT NOT NULL)")
        conn.execute(
            """CREATE TABLE ingest_receipts(
            user_id TEXT NOT NULL,idempotency_key TEXT NOT NULL,request_hash TEXT NOT NULL,
            event_id TEXT NOT NULL,tombstoned INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(user_id,idempotency_key))"""
        )
        conn.execute(
            "INSERT INTO ingest_receipts VALUES(?,?,?,?,?)",
            ('u','legacy-raw-key','f'*64,'evt_missing',1),
        )
        conn.commit()
    PersonalMemoryEngine(db)
    with closing(sqlite3.connect(db)) as conn:
        assert read_schema_version(conn) == 4
        stored = conn.execute('SELECT idempotency_key FROM ingest_receipts').fetchone()[0]
        assert stored == hashlib.sha256(b'legacy-raw-key').hexdigest()
        row = conn.execute('SELECT name FROM pwm_schema_migrations WHERE version=4').fetchone()
        assert row == ('hashed_idempotency_keys',)
