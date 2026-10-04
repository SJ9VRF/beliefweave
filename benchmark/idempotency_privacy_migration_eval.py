from __future__ import annotations
import json, sqlite3, tempfile
from contextlib import closing
from pathlib import Path
from pwm.engine import (
    IdempotencyTombstonedError,
    MemoryStateConflictError,
    PersonalMemoryEngine,
)
from pwm.integrity import audit_database
from pwm.memory.schema import Event, MemoryRecord, MemoryType, SourceType
from pwm.schema_version import CURRENT_SCHEMA_VERSION, read_schema_version


def _mem(user, value, sources):
    return MemoryRecord(user_id=user,subject='user',predicate='preference.food',value=value,
        memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.95,source_event_ids=list(sources))


def run():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        # Legacy schema -> current migration.
        legacy=root/'legacy.db'
        with closing(sqlite3.connect(legacy)) as c:
            c.execute("CREATE TABLE pwm_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
            c.execute("INSERT INTO pwm_meta(key,value) VALUES('schema_version','1')")
        PersonalMemoryEngine(legacy)
        with closing(sqlite3.connect(legacy)) as c:
            migrated=read_schema_version(c)
            migrations=c.execute("SELECT version,name FROM pwm_schema_migrations ORDER BY version").fetchall()

        # Retry safety and mismatch rejection.
        db=root/'idem.db'; e=PersonalMemoryEngine(db)
        first=e.ingest('u','I love sushi.',context='food',idempotency_key='request-1')
        replay=e.ingest('u','I love sushi.',context='food',idempotency_key='request-1')
        mismatch_rejected=False
        try: e.ingest('u','I love ramen.',context='food',idempotency_key='request-1')
        except ValueError: mismatch_rejected=True
        with closing(sqlite3.connect(db)) as c:
            persisted_key = c.execute(
                'SELECT idempotency_key FROM ingest_receipts WHERE user_id=?', ('u',)
            ).fetchone()[0]
        raw_key_not_persisted = persisted_key != 'request-1' and len(persisted_key) == 64
        before_forget=(len(e.events.list_for_user('u',limit=None)),len(e.memories.list_all('u')))
        mid=first['actions'][0]['memory'].id
        deleted_event_id = first['event'].id
        e.forget_memory(mid,delete_source_events=True)
        with closing(sqlite3.connect(db)) as c:
            tombstone = c.execute(
                'SELECT idempotency_key,request_hash,event_id,tombstoned FROM ingest_receipts WHERE user_id=?', ('u',)
            ).fetchone()
        tombstone_scrubbed = (
            tombstone is not None and len(tombstone[0]) == 64
            and tombstone[1] == '' and tombstone[2] == '' and tombstone[3] == 1
            and deleted_event_id not in repr(tombstone)
        )
        resurrection_blocked=False
        try: e.ingest('u','I love sushi.',context='food',idempotency_key='request-1')
        except IdempotencyTombstonedError: resurrection_blocked=True
        after_forget=(len(e.events.list_for_user('u',limit=None)),len(e.memories.list_all('u')))

        # Relation repair under privacy deletion.
        db2=root/'relations.db'; r=PersonalMemoryEngine(db2)
        ev1,ev2,ev3=[Event(user_id='u',raw_text=f'e{i}') for i in range(3)]
        for ev in (ev1,ev2,ev3): r.events.add(ev)
        target=_mem('u','sushi',[ev1.id]); other=_mem('u','ramen',[ev2.id]); successor=_mem('u','udon',[ev3.id])
        target.conflicts_with=[other.id]; other.conflicts_with=[target.id]; successor.supersedes=target.id
        for m in (target,other,successor): r.memories.add(m)
        r.forget_memory(target.id,delete_source_events=True)
        other2=r.memories.get(other.id); successor2=r.memories.get(successor.id)
        integrity=audit_database(db2)

        # User correction must preserve version/provenance instead of mutating in place.
        db3=root/'correction.db'; cengine=PersonalMemoryEngine(db3)
        original=cengine.ingest('u','I love sushi.')['actions'][0]['memory']
        corrected=cengine.correct_memory(original.id,'ramen',timestamp='2000-01-02T03:00:00Z')
        corrected_event=cengine.events.get(corrected.source_event_ids[0]) if corrected else None
        correction_replay=cengine.correct_memory(original.id,'ramen')
        divergent_rejected=False
        try:
            cengine.correct_memory(original.id,'udon')
        except MemoryStateConflictError:
            divergent_rejected=True
        correction_provenance_preserved=bool(
            corrected
            and corrected.supersedes==original.id
            and corrected.user_verified
            and corrected_event
            and corrected_event.metadata.get('kind')=='memory_correction'
            and correction_replay
            and correction_replay.id==corrected.id
            and divergent_rejected
            and audit_database(db3)['ok']
        )

        result={
            'schema_current':CURRENT_SCHEMA_VERSION,
            'legacy_migrated_to':migrated,
            'migrations':[{'version':v,'name':n} for v,n in migrations],
            'same_key_replay_write_free': replay['idempotent_replay'] and first['event'].id==replay['event'].id and replay['actions']==[],
            'mismatched_payload_rejected':mismatch_rejected,
            'counts_before_forget':{'events':before_forget[0],'memories':before_forget[1]},
            'counts_after_forget':{'events':after_forget[0],'memories':after_forget[1]},
            'hard_forget_retry_resurrection_blocked':resurrection_blocked,
            'raw_idempotency_key_not_persisted':raw_key_not_persisted,
            'tombstone_sensitive_metadata_scrubbed':tombstone_scrubbed,
            'conflict_reference_repaired':other2 is not None and target.id not in other2.conflicts_with,
            'supersedes_reference_repaired':successor2 is not None and successor2.supersedes is None,
            'integrity_ok':integrity['ok'],
            'correction_provenance_preserved':correction_provenance_preserved,
        }
        result['all_pass']=all([
            migrated==CURRENT_SCHEMA_VERSION,
            result['same_key_replay_write_free'],mismatch_rejected,resurrection_blocked,
            raw_key_not_persisted,tombstone_scrubbed,
            after_forget==(0,0),result['conflict_reference_repaired'],result['supersedes_reference_repaired'],integrity['ok'],
            correction_provenance_preserved
        ])
        return result

if __name__=='__main__':
    out=run(); p=Path(__file__).resolve().parents[1]/'results'/'idempotency_privacy_migration.json'; p.write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
