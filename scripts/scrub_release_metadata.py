from __future__ import annotations
import json, re, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Coverage.py writes wall-clock time into its JSON. It is not analytically meaningful.
p=ROOT/'results'/'coverage.json'
if p.exists():
    d=json.loads(p.read_text())
    d.get('meta',{}).pop('timestamp',None)
    p.write_text(json.dumps(d,separators=(',',':')))
# pytest's JUnit output includes wall-clock timestamp and ephemeral host name.
p=ROOT/'results'/'pytest.xml'
if p.exists():
    tree=ET.parse(p); root=tree.getroot()
    for node in root.iter('testsuite'):
        node.attrib.pop('timestamp',None); node.attrib.pop('hostname',None)
    tree.write(p,encoding='utf-8',xml_declaration=True)
# Guard against accidental wall-clock timestamps in static robustness evidence.
p=ROOT/'results'/'ood_robustness.json'
if p.exists():
    s=p.read_text()
    s=re.sub(r'20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?\+00:00','synthetic-time',s)
    p.write_text(s)
