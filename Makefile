.PHONY: install test train eval dashboard reproduce demo clean
install:
	python -m pip install -e '.[dev,ml,demo]'
test:
	pytest -q
train:
	python scripts/train_write_policy.py
	python scripts/train_semantic_router.py
	python scripts/train_conflict_model.py
eval:
	PYTHONPATH=. python benchmark/run_benchmark.py
	PYTHONPATH=. python benchmark/evaluate_hard_scenarios.py
	PYTHONPATH=. python benchmark/evaluate_ood.py
	PYTHONPATH=. python experiments/run_ablations.py
dashboard:
	python scripts/generate_dashboard.py
reproduce: train test eval dashboard
demo:
	PYTHONPATH=. uvicorn demo.app:app --host 127.0.0.1 --port 8000
clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -f demo/demo.db
