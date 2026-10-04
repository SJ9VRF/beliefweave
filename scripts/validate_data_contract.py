from __future__ import annotations
import json, sqlite3, tempfile, sys
from contextlib import closing
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from pwm.engine import PersonalMemoryEngine
from pwm.memory.schema import MemoryType, SourceType, MemoryStatus, ConflictType, WriteDecision
from pwm.schema_version import CURRENT_SCHEMA_VERSION, read_schema_version

with tempfile.TemporaryDirectory(prefix='pwm-contract-') as td:
    db=Path(td)/'contract.db'
    PersonalMemoryEngine(db)
    with closing(sqlite3.connect(db)) as conn:
        def cols(table):
            return [r[1] for r in conn.execute(f'PRAGMA table_info({table})').fetchall()]
        payload={
            'schema_version': read_schema_version(conn),
            'supported_schema_version': CURRENT_SCHEMA_VERSION,
            'tables': {
                'events': cols('events'), 'memories': cols('memories'), 'pwm_meta': cols('pwm_meta'),
                'pwm_schema_migrations': cols('pwm_schema_migrations'), 'ingest_receipts': cols('ingest_receipts'),
            },
            'enums': {
                'memory_type':[x.value for x in MemoryType],
                'source_type':[x.value for x in SourceType],
                'memory_status':[x.value for x in MemoryStatus],
                'conflict_type':[x.value for x in ConflictType],
                'write_decision':[x.value for x in WriteDecision],
            },
        }
print(json.dumps(payload,indent=2,sort_keys=True))
