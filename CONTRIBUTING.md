# Contributing

This repository is organized as a research artifact: changes should preserve reproducibility, provenance, and explicit scientific boundaries.

## Development setup
```bash
python -m pip install -e '.[dev,ml,demo]'
pytest -q
```

## Before opening a pull request
Run:
```bash
./scripts/reproduce_all.sh
```

A release-quality change must keep these gates green:
- all tests pass
- line coverage ≥ 90%
- release audit passes
- no stale-memory leakage in the controlled retrieval benchmark
- generated paper/dashboard artifacts are synchronized with result JSON

## Adding a new memory behavior
1. Add or update a controlled scenario.
2. Add a regression test that would fail before the code change.
3. Preserve provenance and temporal semantics.
4. Avoid destructive state updates unless explicit evidence supports supersession.
5. Document any new failure mode or limitation.

## Reporting benchmark changes
Never hand-edit reported result numbers. Update executable evaluation code, rerun reproduction, and let the publication synchronization scripts regenerate derived artifacts.

## Scientific claims
Synthetic benchmark results must remain labeled as synthetic/controlled. Human or production claims require separately documented evidence.
