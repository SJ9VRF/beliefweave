#!/usr/bin/env python3
"""Lightweight static guardrail audit. Not a substitute for Bandit/SAST or a formal review."""
from __future__ import annotations
import ast, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TARGETS=[ROOT/'beliefweave', ROOT/'pwm', ROOT/'demo', ROOT/'scripts']
findings=[]
secret_re=re.compile(r'(?i)(api[_-]?key|secret|password|token)\s*=\s*["\'][^"\']{8,}["\']')
for base in TARGETS:
  for p in base.rglob('*.py'):
    text=p.read_text(errors='replace')
    rel=str(p.relative_to(ROOT))
    try: tree=ast.parse(text)
    except SyntaxError as e:
      findings.append({'severity':'error','code':'syntax_error','file':rel,'line':e.lineno}); continue
    for node in ast.walk(tree):
      if isinstance(node, ast.Call):
        name=''
        if isinstance(node.func, ast.Name): name=node.func.id
        elif isinstance(node.func, ast.Attribute): name=node.func.attr
        if name in {'eval','exec'}:
          findings.append({'severity':'error','code':f'unsafe_{name}','file':rel,'line':node.lineno})
        if name in {'system','popen'}:
          findings.append({'severity':'warning','code':'shell_process_call','file':rel,'line':node.lineno})
        for kw in node.keywords:
          if kw.arg=='shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            findings.append({'severity':'error','code':'subprocess_shell_true','file':rel,'line':node.lineno})
    for i,line in enumerate(text.splitlines(),1):
      if secret_re.search(line) and 'Field(' not in line:
        findings.append({'severity':'warning','code':'possible_hardcoded_secret','file':rel,'line':i})
errors=sum(x['severity']=='error' for x in findings)
result={'scope':['beliefweave','pwm','demo','scripts'],'ok':errors==0,'error_count':errors,'finding_count':len(findings),'findings':findings,'boundary':'Lightweight AST/regex guardrail; not a formal security audit.'}
out=ROOT/'results'/'static_security.json'; out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['ok'] else 1)
