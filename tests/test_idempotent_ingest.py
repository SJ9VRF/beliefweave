import sqlite3
from contextlib import closing

import pytest

from pwm.engine import PersonalMemoryEngine, IdempotencyTombstonedError
from pwm.integrity import audit_database


def test_same_idempotency_key_replays_without_duplicate_writes(tmp_path):
    db=tmp_path/'idem.db'; e=PersonalMemoryEngine(db)
    first=e.ingest('u','I love sushi.',idempotency_key='req-1')
    second=e.ingest('u','I love sushi.',idempotency_key='req-1')
    assert first['idempotent_replay'] is False
    assert second['idempotent_replay'] is True
    assert second['event'].id == first['event'].id
    assert second['actions'] == []
    assert len(e.events.list_for_user('u',limit=None)) == 1
    assert len(e.memories.list_all('u')) == 1
    with closing(sqlite3.connect(db)) as conn:
        assert conn.execute('SELECT COUNT(*) FROM ingest_receipts').fetchone()[0] == 1
    assert audit_database(db)['ok'] is True


def test_idempotency_key_reuse_with_different_payload_fails_closed(tmp_path):
    db=tmp_path/'idem-mismatch.db'; e=PersonalMemoryEngine(db)
    e.ingest('u','I love sushi.',idempotency_key='req-1')
    with pytest.raises(ValueError,match='different request payload'):
        e.ingest('u','I love ramen.',idempotency_key='req-1')
    assert len(e.events.list_for_user('u',limit=None)) == 1
    assert len(e.memories.list_all('u')) == 1


def test_hard_forget_tombstones_idempotency_receipt(tmp_path):
    db=tmp_path/'idem-forget.db'; e=PersonalMemoryEngine(db)
    out=e.ingest('u','I love sushi.',idempotency_key='req-1')
    mid=out['actions'][0]['memory'].id
    assert e.forget_memory(mid,delete_source_events=True)
    with closing(sqlite3.connect(db)) as conn:
        row=conn.execute('SELECT COUNT(*),MAX(tombstoned) FROM ingest_receipts').fetchone()
        assert row == (1,1)
    with pytest.raises(IdempotencyTombstonedError):
        e.ingest('u','I love sushi.',idempotency_key='req-1')
    assert len(e.events.list_for_user('u',limit=None)) == 0
    assert len(e.memories.list_all('u')) == 0
    assert audit_database(db)['ok'] is True


def test_idempotency_key_is_never_persisted_in_plaintext(tmp_path):
    db = tmp_path / 'hashed-key.db'
    e = PersonalMemoryEngine(db)
    raw_key = 'customer-visible-retry-token-123'
    e.ingest('u', 'I love sushi.', idempotency_key=raw_key)
    with closing(sqlite3.connect(db)) as conn:
        stored = conn.execute('SELECT idempotency_key FROM ingest_receipts').fetchone()[0]
    assert stored != raw_key
    assert len(stored) == 64
    int(stored, 16)


def test_hard_forget_scrubs_tombstone_request_metadata(tmp_path):
    db = tmp_path / 'scrubbed-tombstone.db'
    e = PersonalMemoryEngine(db)
    out = e.ingest('u', 'I love sushi.', idempotency_key='req-sensitive')
    original_event_id = out['event'].id
    mid = out['actions'][0]['memory'].id
    assert e.forget_memory(mid, delete_source_events=True)
    with closing(sqlite3.connect(db)) as conn:
        row = conn.execute(
            'SELECT idempotency_key,request_hash,event_id,tombstoned FROM ingest_receipts'
        ).fetchone()
    assert len(row[0]) == 64
    assert row[1] == ''
    assert row[2] == ''
    assert row[3] == 1
    assert original_event_id not in repr(row)
    with pytest.raises(IdempotencyTombstonedError):
        e.ingest('u', 'a completely different payload', idempotency_key='req-sensitive')


def test_corrupt_idempotency_receipt_missing_event_fails_closed(tmp_path):
    import sqlite3
    from pwm.engine import PersonalMemoryEngine

    db = tmp_path / "missing-receipt-event.db"
    engine = PersonalMemoryEngine(db)
    engine.ingest("u", "I like tea.", idempotency_key="same-key")
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("DELETE FROM events WHERE user_id='u'")
        conn.commit()
    try:
        engine.ingest("u", "I like tea.", idempotency_key="same-key")
    except RuntimeError as exc:
        assert "missing event" in str(exc)
    else:
        raise AssertionError("corrupt receipt must fail closed")
