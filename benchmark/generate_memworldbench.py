from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pwm.simulation import LongitudinalUserGenerator
if __name__=='__main__':
 g=LongitudinalUserGenerator(seed=17)
 rows=g.generate(n_users=1000,n_turns=100,path='benchmark/data/memworldbench_1000x100.jsonl')
 print(f'generated {len(rows):,} interactions')
