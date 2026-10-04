from __future__ import annotations
from dataclasses import dataclass,asdict
@dataclass
class Counts:
 tp:int=0; fp:int=0; fn:int=0
 def precision(self): return self.tp/max(1,self.tp+self.fp)
 def recall(self): return self.tp/max(1,self.tp+self.fn)
 def f1(self):
  p,r=self.precision(),self.recall(); return 2*p*r/max(1e-12,p+r)

def exact_contains(memories,predicate,value):
 return any(m.predicate==predicate and m.value.lower()==value.lower() for m in memories)
