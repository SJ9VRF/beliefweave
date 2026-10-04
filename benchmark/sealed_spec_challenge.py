from __future__ import annotations
import json, hashlib, sys
from dataclasses import dataclass
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_MANIFEST_SHA256='893522caff65ea4eed3fcad64af2f343bb941540a261f57ff78b94276de0435a'
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from pwm.belief_governance import DecisionAwareBeliefGateV2,DecisionAwareBeliefGateV3,PersonalizationAction
from pwm.memory.schema import MemoryRecord,MemoryType,SourceType,MemoryStatus
NOW='2000-06-01T12:00:00+00:00'
@dataclass(frozen=True)
class Case:
    id:str; family:str; memory:MemoryRecord; context:str|None; conflict:bool; gold:PersonalizationAction; note:str

def rec(i,**kw):
    defaults=dict(user_id='u',subject='user',predicate='preference',value=f'value-{i%7}',memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.9,source_event_ids=['evt'],status=MemoryStatus.ACTIVE)
    defaults.update(kw); return MemoryRecord(**defaults)

def build(per=32):
    C=[]
    def add(f, maker, gold, note):
        for i in range(per):
            m,ctx,conf=maker(i); C.append(Case(f'{f}-{i:03d}',f,m,ctx,conf,gold,note))
    add('deleted_scoped_unknown',lambda i:(rec(i,status=MemoryStatus.DELETED,context_scope='work'),None,False),PersonalizationAction.ABSTAIN,'Lifecycle invalidity should dominate missing-context clarification.')
    add('archived_scoped_unknown',lambda i:(rec(i,status=MemoryStatus.ARCHIVED,context_scope='work'),None,False),PersonalizationAction.ABSTAIN,'Archived evidence should not trigger clarification.')
    add('expired_scoped_unknown',lambda i:(rec(i,valid_until='1999-01-01T00:00:00+00:00',context_scope='work'),None,False),PersonalizationAction.ABSTAIN,'Expiry should dominate missing-context clarification.')
    add('malformed_valid_until',lambda i:(rec(i,valid_until='not-a-date'), 'dining',False),PersonalizationAction.ASK,'Malformed temporal metadata should fail closed to clarification rather than personalize.')
    add('malformed_valid_from',lambda i:(rec(i,valid_from='not-a-date'), 'dining',False),PersonalizationAction.ASK,'Malformed temporal metadata should fail closed to clarification rather than personalize.')
    add('missing_provenance_high_conf',lambda i:(rec(i,source_event_ids=[]), 'dining',False),PersonalizationAction.ASK,'High-confidence memory with no provenance should not immediately personalize.')
    add('sensitive_unverified',lambda i:(rec(i,privacy_level='sensitive',user_verified=False), 'dining',False),PersonalizationAction.ASK,'Sensitive unverified memory warrants confirmation before use.')
    add('sensitive_verified',lambda i:(rec(i,privacy_level='sensitive',user_verified=True), 'dining',False),PersonalizationAction.USE,'User verification can authorize use of otherwise sensitive memory in this contract.')
    add('context_exact_match',lambda i:(rec(i,context_scope='travel'), 'travel',False),PersonalizationAction.USE,'Exact scoped context match with strong explicit evidence is usable.')
    add('context_case_match',lambda i:(rec(i,context_scope='Travel'), 'travel',False),PersonalizationAction.USE,'Context matching is case-insensitive.')
    add('exact_validity_boundary',lambda i:(rec(i,valid_from=NOW,valid_until=NOW), 'dining',False),PersonalizationAction.USE,'Validity intervals are inclusive at exact boundary.')
    add('inferred_verified_high',lambda i:(rec(i,source_type=SourceType.INFERRED,confidence=.9,user_verified=True), 'dining',False),PersonalizationAction.USE,'Verified inferred evidence can cross the use threshold.')
    add('implicit_verified_high',lambda i:(rec(i,source_type=SourceType.IMPLICIT,confidence=.82,user_verified=True), 'dining',False),PersonalizationAction.USE,'Verified implicit evidence can be used when authority is high.')
    add('synthetic_verified',lambda i:(rec(i,source_type=SourceType.SYNTHETIC,confidence=.99,user_verified=True), 'dining',False),PersonalizationAction.ABSTAIN,'Synthetic provenance is not user-grounded authority even when marked verified.')
    add('conflict_plus_deleted',lambda i:(rec(i,status=MemoryStatus.DELETED), 'dining',True),PersonalizationAction.ABSTAIN,'Deleted evidence should be ignored rather than clarified despite conflict flag.')
    return C

def manifest(cases):
    rows=[{'id':c.id,'family':c.family,'gold':c.gold.value,'note':c.note} for c in cases]
    raw=json.dumps(rows,sort_keys=True,separators=(',',':')).encode(); return rows,hashlib.sha256(raw).hexdigest()

def main():
    cases=build(); rows,h=manifest(cases)
    manifest_path=ROOT/'benchmark'/'sealed_spec_manifest.json'
    actual_file_hash=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if actual_file_hash != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError(f'sealed manifest bytes changed: {actual_file_hash}')
    frozen=json.loads(manifest_path.read_text())
    expected={'suite':'BeliefWeave Sealed Specification Challenge','status':'frozen before execution','n':len(cases),'sha256_of_id_family_gold_note':h,'cases':rows}
    if frozen != expected:
        raise RuntimeError('sealed manifest content no longer matches generated specification')
    g=DecisionAwareBeliefGateV2(); pred=[]
    for c in cases: pred.append(g.decide(c.memory,context=c.context,now=NOW,unresolved_conflict=c.conflict).action)
    g3=DecisionAwareBeliefGateV3(); pred3=[g3.decide(c.memory,context=c.context,now=NOW,unresolved_conflict=c.conflict).action for c in cases]
    fam={}
    for f in sorted({c.family for c in cases}):
        idx=[i for i,c in enumerate(cases) if c.family==f]; fam[f]={'n':len(idx),'accuracy':sum(pred[i]==cases[i].gold for i in idx)/len(idx),'gold':cases[idx[0]].gold.value,'predicted_counts':{a.value:sum(pred[i]==a for i in idx) for a in PersonalizationAction},'note':cases[idx[0]].note}
    acc=sum(a==c.gold for a,c in zip(pred,cases))/len(cases)
    out={'suite':'BeliefWeave Sealed Specification Challenge','gate':'DecisionAwareBeliefGateV2','manifest_sha256':h,'n':len(cases),'exact_action_accuracy':acc,'challenge_informed_v3_accuracy':sum(a==c.gold for a,c in zip(pred3,cases))/len(cases),'challenge_informed_v3_note':'V3 was written after inspecting this suite; its score is regression evidence, not independent generalization evidence.','family_breakdown':fam,
         'scientific_boundary':'Designed after V2 was frozen and executed without tuning V2 on this suite. It is still author-designed and therefore complements, rather than replaces, independent external or human evaluation.'}
    (ROOT/'results'/'sealed_spec_challenge.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
