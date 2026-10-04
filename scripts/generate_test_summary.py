#!/usr/bin/env python3
from __future__ import annotations
import json, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
xml=ROOT/'results'/'pytest.xml'
root=ET.parse(xml).getroot()
# pytest may emit <testsuites><testsuite ...> or a single testsuite.
suites=[root] if root.tag=='testsuite' else list(root.findall('testsuite'))
def n(attr): return sum(int(float(s.attrib.get(attr,0))) for s in suites)
summary={'tests':n('tests'),'failures':n('failures'),'errors':n('errors'),'skipped':n('skipped'),'passed':n('tests')-n('failures')-n('errors')-n('skipped')}
summary['ok']=summary['failures']==0 and summary['errors']==0
(ROOT/'results'/'test_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2))
