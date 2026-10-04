#!/usr/bin/env bash
set -euo pipefail

python scripts/check_core_style.py
export PYTHONPATH=.
if [[ "${RETRAIN:-0}" == "1" ]]; then
  python scripts/train_write_policy.py
  python scripts/train_semantic_router.py
  python scripts/train_conflict_model.py
fi
pytest --cov=pwm --cov=demo --cov-report=json:results/coverage.json --cov-fail-under=90 --junitxml=results/pytest.xml -q -W error::ResourceWarning
python scripts/generate_test_summary.py
python scripts/scrub_release_metadata.py
python scripts/check_determinism.py
python scripts/check_repro_environment.py
python scripts/smoke_release.py
python scripts/build_and_smoke_wheel.py
python scripts/validate_core_install.py
python scripts/validate_wheel_cli.py > results/wheel_cli_validation.json
python scripts/validate_data_contract.py > results/data_contract.json
python scripts/generate_sbom.py > SBOM.json
python scripts/generate_dependency_snapshot.py
python scripts/generate_openapi.py
python scripts/static_security_audit.py
python scripts/profile_runtime.py
python benchmark/run_benchmark.py
python benchmark/evaluate_hard_scenarios.py
python benchmark/evaluate_ood.py
python benchmark/evaluate_calibration.py
python benchmark/evaluate_retrieval.py
python benchmark/stress_test.py
python benchmark/beliefshift_bench.py
python benchmark/authority_ablation_bench.py
python benchmark/paper_grade_eval.py
python benchmark/behavior_intervention_eval.py
python benchmark/error_propagation_eval.py
python benchmark/horizon_scaling.py
python benchmark/unseen_composition_eval.py
python benchmark/sealed_spec_challenge.py
python benchmark/metamorphic_authority_eval.py
python benchmark/mutation_adequacy_eval.py
python benchmark/stochastic_stability_eval.py
python benchmark/sensitivity_summary.py
python benchmark/power_analysis.py
python benchmark/authority_modelcheck.py
python benchmark/concurrency_integrity_eval.py
python benchmark/privacy_erasure_eval.py
python benchmark/atomicity_fault_injection_eval.py
python benchmark/idempotency_privacy_migration_eval.py
python benchmark/database_resilience.py
python benchmark/privacy_inventory_eval.py
python scripts/validate_croissant_local.py
python scripts/check_neurips_submission_readiness.py
python scripts/generate_experiment_lineage.py
python experiments/run_ablations.py
python scripts/generate_dashboard.py
python scripts/generate_figures.py
python scripts/generate_paper_grade_figures.py
python scripts/generate_results_tables.py
python scripts/sync_publication.py
python scripts/generate_supplement.py
bash scripts/generate_paper.sh
python scripts/check_neurips_submission_readiness.py
python scripts/sync_release_docs.py
python scripts/generate_site.py
python scripts/generate_demo_video.py
python scripts/validate_site_contract.py
python scripts/audit_release.py
printf '\nReproduction complete. Use RETRAIN=1 ./scripts/reproduce_all.sh to retrain serialized local models first.\n'
