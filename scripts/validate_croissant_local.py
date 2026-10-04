import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'benchmark'/'croissant.json'; d=json.loads(p.read_text())
required=['@context','@type','name','url','license','conformsTo','distribution','rai:dataLimitations','rai:dataBiases','rai:personalSensitiveInformation','rai:dataUseCases','rai:dataSocialImpact','rai:hasSyntheticData','prov:wasGeneratedBy']
missing=[k for k in required if k not in d or d[k] in ('',None,[]) ]
if missing: raise SystemExit('missing Croissant fields: '+', '.join(missing))
assert d['@type']=='sc:Dataset'
assert d['rai:hasSyntheticData'] is True
print(f'local Croissant structural check PASS ({len(required)}/{len(required)} required fields present)')
print('NOTE: official NeurIPS/Croissant network validator and public dataset URL remain submission-time external checks.')
