#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from demo.app import app

out=ROOT/'results'/'openapi.json'
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True)+"\n")
print(out)
