from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pwm.engine import PersonalMemoryEngine
from pwm.integrity import audit_database
from pwm.memory.schema import Event, MemoryRecord, MemoryType, SourceType


def rec(user,value,events):
    return MemoryRecord(user_id=user,subject='user',predicate='preference.food',value=value,memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.95,source_event_ids=list(events))


def run(users:int=50) -> dict:
    with tempfile.TemporaryDirectory() as d:
        db=Path(d)/'erase.sqlite';e=PersonalMemoryEngine(db)
        deleted_events=[]; retained_events=[]; targets=[]; retained_siblings=[]
        for i in range(users):
            u=f'u{i}'
            shared=Event(user_id=u,raw_text='I like sushi and tea.')
            extra=Event(user_id=u,raw_text='Tea remains important.')
            e.events.add(shared);e.events.add(extra)
            target=rec(u,'sushi',[shared.id]); only=rec(u,'tea',[shared.id]); multi=rec(u,'green tea',[shared.id,extra.id])
            for m in (target,only,multi):e.memories.add(m)
            deleted_events.append(shared.id);retained_events.append(extra.id);targets.append(target.id);retained_siblings.append(multi.id)
        for mid in targets:e.forget_memory(mid,delete_source_events=True)
        audit=audit_database(db)
        deleted_absent=all(e.events.get(x) is None for x in deleted_events)
        retained_present=all(e.events.get(x) is not None for x in retained_events)
        targets_absent=all(e.memories.get(x) is None for x in targets)
        sibling_ok=0
        for mid,eid in zip(retained_siblings,retained_events):
            m=e.memories.get(mid)
            sibling_ok += int(m is not None and m.source_event_ids==[eid])
        exports=[e.export_user_data(f'u{i}') for i in range(users)]
        leaked_deleted=sum(any(ev['id'] in set(deleted_events) for ev in x['events']) for x in exports)
        return {
            'suite':'Privacy Erasure / Provenance Cascade Evaluation',
            'users':users,
            'deleted_source_events_absent':deleted_absent,
            'unrelated_source_events_retained':retained_present,
            'target_memories_absent':targets_absent,
            'multi_source_siblings_repaired':sibling_ok,
            'expected_multi_source_siblings':users,
            'exports_with_deleted_event_leakage':leaked_deleted,
            'integrity_ok':audit['ok'],
            'integrity_error_count':audit['error_count'],
            'boundary':'Local deterministic database erasure test; it does not establish legal compliance or deletion guarantees for backups, logs, or external services.'
        }


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--users',type=int,default=50);ap.add_argument('--out',default='results/privacy_erasure.json');a=ap.parse_args()
    r=run(a.users);Path(a.out).write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
if __name__=='__main__':main()
