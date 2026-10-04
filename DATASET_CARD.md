# MemWorldBench Dataset Card

**Purpose:** regression and controlled research evaluation for temporally evolving personal memory.

**Components:**
- `benchmark/data/memworldbench_1000x100.jsonl`: 100,000 synthetic interactions from 1,000 generated user trajectories.
- `benchmark/data/hard_scenarios_360.jsonl`: 360 controlled hard scenarios across six categories.

**Ground truth:** simulator-internal current state and scenario-specific expected memory lifecycle behavior.

**Intended use:** engineering validation, ablation, benchmark development, failure discovery.

**Not intended for:** claims about human preferences, demographic behavior, production readiness, or real-world safety.

**Known biases/limitations:** templated language, narrow domain vocabulary, simplified temporal dynamics, no representative human population, limited multilingual surface forms.
