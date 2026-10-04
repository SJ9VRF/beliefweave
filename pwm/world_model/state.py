from __future__ import annotations
from collections import defaultdict
from pwm.memory.schema import StateBelief
from pwm.memory.store import MemoryStore

class UserStateMaterializer:
    def __init__(self, store:MemoryStore): self.store=store
    def current(self,user_id:str,now:str|None=None)->dict[str,list[StateBelief]]:
        out=defaultdict(list)
        for m in self.store.list_active(user_id,now=now):
            key=f"{m.memory_type.value}.{m.predicate}"
            out[key].append(StateBelief(key=key,value=m.value,confidence=m.confidence,memory_id=m.id,valid_from=m.valid_from,valid_until=m.valid_until,context_scope=m.context_scope,provenance=m.source_event_ids))
        for k in out: out[k].sort(key=lambda x:x.confidence, reverse=True)
        return dict(out)
