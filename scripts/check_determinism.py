from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import hashlib, json
from pathlib import Path
from pwm.simulation import LongitudinalUserGenerator

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'determinism.json'

def digest(rows):
    payload = '\n'.join(json.dumps(r, sort_keys=True, separators=(',', ':')) for r in rows).encode()
    return hashlib.sha256(payload).hexdigest()

def main():
    kwargs = dict(n_users=50, n_turns=40)
    a = LongitudinalUserGenerator(seed=17).generate(**kwargs)
    b = LongitudinalUserGenerator(seed=17).generate(**kwargs)
    c = LongitudinalUserGenerator(seed=18).generate(**kwargs)
    da, db, dc = digest(a), digest(b), digest(c)
    result = {
        'seed': 17,
        'n_users': kwargs['n_users'],
        'n_turns': kwargs['n_turns'],
        'n_records': len(a),
        'run_a_sha256': da,
        'run_b_sha256': db,
        'different_seed_sha256': dc,
        'same_seed_identical': da == db,
        'different_seed_changes_output': da != dc,
    }
    OUT.write_text(json.dumps(result, indent=2) + '\n')
    if not result['same_seed_identical'] or not result['different_seed_changes_output']:
        raise SystemExit('determinism check failed')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
