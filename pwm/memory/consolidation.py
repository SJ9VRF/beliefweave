from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from pwm.memory.store import MemoryStore
@dataclass
class ConsolidatedSection:
 category:str; facts:list[str]; source_memory_ids:list[str]
class MemoryConsolidator:
 """Loss-aware deterministic Level-2/3 consolidation. Raw memories stay as provenance."""
 def __init__(self,store:MemoryStore): self.store=store
 def consolidate(self,user_id:str,now:str|None=None):
  groups=defaultdict(list)
  for m in self.store.list_active(user_id,now=now): groups[m.memory_type.value].append(m)
  out=[]
  for cat,ms in sorted(groups.items()):
   facts=[f"{m.predicate}: {m.value}" + (f" [{m.context_scope}]" if m.context_scope else '') for m in ms]
   out.append(ConsolidatedSection(cat,facts,[m.id for m in ms]))
  return out
