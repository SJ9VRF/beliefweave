from __future__ import annotations
import json, sys, tomllib, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pwm.schema_version import CURRENT_SCHEMA_VERSION
errors = []
VERSION = tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']
WHEEL = f'dist/beliefweave-{VERSION}-py3-none-any.whl'
expected_wheel=f'beliefweave-{VERSION}-py3-none-any.whl'
for folder in [ROOT/'dist', ROOT/'site'/'downloads']:
    if folder.exists():
        wheels=sorted(x.name for x in folder.glob('beliefweave-*-py3-none-any.whl'))
        stale=[x for x in wheels if x != expected_wheel]
        if stale: errors.append(f'stale wheel(s) in {folder.relative_to(ROOT)}: {stale}')

dist_wheel = ROOT / WHEEL
site_wheel = ROOT / 'site' / 'downloads' / expected_wheel
if dist_wheel.exists() and site_wheel.exists():
    if hashlib.sha256(dist_wheel.read_bytes()).hexdigest() != hashlib.sha256(site_wheel.read_bytes()).hexdigest():
        errors.append('site wheel bytes differ from the validated dist wheel')
required = [
    'README.md','FINAL_VALIDATION.md','ARTIFACT_MANIFEST.md','paper/TECHNICAL_REPORT.md',
    'paper/RESULTS_TABLES.md','paper/REPRODUCIBLE_SUMMARY.md','results/benchmark.json',
    'results/retrieval_eval.json','results/ood_robustness.json','results/calibration.json',
    'results/coverage.json','results/determinism.json','results/release_smoke.json','results/package_smoke.json','results/dependency_snapshot.json','scripts/reproduce_all.sh','BENCHMARK_CARD.md','CONTRIBUTING.md','DEVELOPER_GUIDE.md','RELEASE_CHECKLIST.md','DEPENDENCY_SNAPSHOT.md','ARTIFACT_INDEX.md','CITATION.cff','LICENSE',WHEEL,'results/data_contract.json','results/wheel_cli_validation.json','SBOM.json','paper/BELIEFWEAVE.pdf','paper/BELIEFWEAVE.tex','scripts/generate_paper.sh','scripts/generate_site.py','site/paper.pdf','site/dashboard.html','.zenodo.json','codemeta.json','pwm/cli.py','pwm/schema_version.py','pwm/integrity.py','scripts/reviewer_demo.sh','results/test_summary.json','results/openapi.json','results/static_security.json','results/runtime_profile.json','results/beliefshift_bench.json','results/authority_ablation.json','NOVELTY_AUDIT.md','docs/OPENAPI_CONTRACT.md','docs/INTEGRITY.md','docs/PERFORMANCE.md','site/demo.html','site/benchmark.html','site/technical.html','site/blog.html','site/beliefweave-demo.mp4','site/downloads/beliefweave-code.zip','site/downloads/beliefweave-github-ready.zip','site/downloads/GITHUB_PUBLISHING.md','site/downloads/memworldbench_1000x100.jsonl.gz','results/site_contract.json','results/paper_grade_eval.json','results/behavior_intervention.json','results/error_propagation.json','results/horizon_scaling.json','results/unseen_composition.json','results/stochastic_stability.json','results/sensitivity_summary.json','results/power_analysis.json','submission/NEURIPS_CHECKLIST.md','submission/HUMAN_EVAL_POWER.md','submission/EXTERNAL_EVIDENCE_REQUIRED.md','submission/CROISSANT_STATUS.md','scripts/validate_croissant_local.py','benchmark/beliefshift_v2_test_manifest.json','benchmark/croissant.json','benchmark/external/README.md','benchmark/external/longmemeval_adapter.py','benchmark/external/personamem_adapter.py','human_eval/PROTOCOL.md','human_eval/annotation_schema.json','human_eval/analyze.py','results/sealed_spec_challenge.json','results/metamorphic_authority.json','results/mutation_adequacy.json','benchmark/sealed_spec_manifest.json','benchmark/sealed_spec_manifest.sha256','benchmark/external/public_benchmark_registry.json','benchmark/external/status.json','results/neurips_submission_readiness.json','submission/NEURIPS_FORMAT_STATUS.md','results/authority_modelcheck.json','results/concurrency_integrity.json','results/privacy_erasure.json','benchmark/authority_modelcheck.py','benchmark/concurrency_integrity_eval.py','benchmark/privacy_erasure_eval.py','benchmark/atomicity_fault_injection_eval.py','benchmark/external/locomo_adapter.py','scripts/fetch_external_benchmarks.py','results/atomicity_fault_injection.json','results/experiment_lineage.json','results/repro_environment.json','constraints/reproducible.txt','scripts/generate_experiment_lineage.py','scripts/check_repro_environment.py','results/idempotency_privacy_migration.json','benchmark/idempotency_privacy_migration_eval.py','project_metadata.json','scripts/sync_release_docs.py','docs/ARCHITECTURE_DECISIONS.md','docs/adr/0007-user-data-inventory-and-process-resilience.md','results/database_resilience.json','results/privacy_inventory.json','benchmark/database_resilience.py','benchmark/privacy_inventory_eval.py'
]
for x in required:
    if not (ROOT / x).exists(): errors.append(f'missing required artifact: {x}')
try:
    cal = json.loads((ROOT/'results/calibration.json').read_text())
    total = sum(b['n'] for b in cal['bins'])
    if total != cal['n']: errors.append(f'calibration bins sum to {total}, expected {cal["n"]}')
    if not (0 <= cal['ece'] <= 1): errors.append('ECE outside [0,1]')
    ret = json.loads((ROOT/'results/retrieval_eval.json').read_text())
    aggregates = [v for v in ret.values() if isinstance(v, dict) and 'hit_at_1' in v]
    if len(aggregates) < 2: errors.append('retrieval result missing two aggregate systems')
    elif any(x.get('stale_leaks', 0) != 0 for x in aggregates[:2]): errors.append('retrieval stale leak detected')
    cov = json.loads((ROOT/'results/coverage.json').read_text())['totals']['percent_covered']
    if cov < 90: errors.append(f'coverage below release gate: {cov:.2f}%')
    det = json.loads((ROOT/'results/determinism.json').read_text())
    if not det.get('same_seed_identical'): errors.append('same-seed determinism check failed')
    if not det.get('different_seed_changes_output'): errors.append('different-seed sensitivity check failed')
    smoke=json.loads((ROOT/'results/release_smoke.json').read_text())
    if not smoke.get('passed'): errors.append('release/API smoke test failed')
    pkg=json.loads((ROOT/'results/package_smoke.json').read_text())
    if not pkg.get('passed'): errors.append('wheel/package smoke test failed')
    if not pkg.get('contains_observation_router') or not pkg.get('contains_conflict_model'): errors.append('wheel missing learned model assets')
    wcli=json.loads((ROOT/'results/wheel_cli_validation.json').read_text())
    if not wcli.get('ok'): errors.append('wheel CLI validation failed')
    contract=json.loads((ROOT/'results/data_contract.json').read_text())
    if contract.get('schema_version') != CURRENT_SCHEMA_VERSION or contract.get('supported_schema_version') != CURRENT_SCHEMA_VERSION: errors.append('schema/data contract version mismatch')
    tests=json.loads((ROOT/'results/test_summary.json').read_text())
    if not tests.get('ok') or tests.get('passed') != tests.get('tests'): errors.append('test summary is not fully passing')
    sec=json.loads((ROOT/'results/static_security.json').read_text())
    if not sec.get('ok'): errors.append('lightweight static security audit failed')
    api=json.loads((ROOT/'results/openapi.json').read_text())
    required_paths={'/health','/api/ingest','/api/recall','/api/governed-recall','/api/state/{user_id}','/api/memories/{user_id}','/api/export/{user_id}','/api/user/{user_id}','/api/memory/{memory_id}'}
    if not required_paths.issubset(set(api.get('paths',{}))): errors.append('OpenAPI contract missing required routes')
    schemes=api.get('components',{}).get('securitySchemes',{})
    if 'BearerAuth' not in schemes or 'DemoApiKey' not in schemes:
        errors.append('OpenAPI contract missing demo security schemes')
    for path, ops in api.get('paths',{}).items():
        if not path.startswith('/api/'):
            continue
        for op in ops.values():
            if isinstance(op,dict) and 'responses' in op and not op.get('security'):
                errors.append(f'OpenAPI API operation missing security metadata: {path}')
    prof=json.loads((ROOT/'results/runtime_profile.json').read_text())
    if prof.get('interactions',0) < 100 or prof.get('ingest_ms',{}).get('p95',0) <= 0: errors.append('runtime profile missing/invalid')
    site_contract=json.loads((ROOT/'results/site_contract.json').read_text())
    if not site_contract.get('ok') or site_contract.get('sections') != 14 or site_contract.get('hero_ctas') != 5:
        errors.append('standalone project-page contract failed')
    sealed=json.loads((ROOT/'results/sealed_spec_challenge.json').read_text())
    if sealed.get('n') != 480 or abs(sealed.get('exact_action_accuracy',-1)-0.5333333333333333) > 1e-12:
        errors.append('sealed specification challenge missing or inconsistent')
    if sealed.get('challenge_informed_v3_accuracy') != 1.0:
        errors.append('V3 sealed-spec regression is not fully passing')
    meta=json.loads((ROOT/'results/metamorphic_authority.json').read_text())
    if not meta.get('all_pass') or any(g.get('n_failed') != 0 for g in meta.get('gates',[])):
        errors.append('metamorphic authority invariants failed')
    mut=json.loads((ROOT/'results/mutation_adequacy.json').read_text())
    if mut.get('mutation_score') != 1.0 or mut.get('mutants_killed') != mut.get('n_mutants'):
        errors.append('benchmark mutation adequacy is incomplete')
    mf=ROOT/'benchmark/sealed_spec_manifest.json'
    expected=(ROOT/'benchmark/sealed_spec_manifest.sha256').read_text().split()[0]
    actual=hashlib.sha256(mf.read_bytes()).hexdigest()
    if actual != expected:
        errors.append('sealed specification manifest checksum mismatch')
    fmt=json.loads((ROOT/'results/neurips_submission_readiness.json').read_text())
    if fmt.get('ready_for_official_neurips_template_submission'):
        if not fmt.get('official_style_file_present') or not fmt.get('source_loads_official_style') or fmt.get('custom_geometry_detected'):
            errors.append('NeurIPS readiness claims ready despite format blockers')
    else:
        if not fmt.get('blockers'):
            errors.append('NeurIPS format is not ready but blocker list is empty')

    modelcheck=json.loads((ROOT/'results/authority_modelcheck.json').read_text())
    if modelcheck.get('n_states_per_gate') != 9600 or not modelcheck.get('production_all_properties_hold'):
        errors.append('production authority model-check missing or failed')
    systems={x.get('gate'):x for x in modelcheck.get('systems',[])}
    if systems.get('DecisionAwareBeliefGateV3',{}).get('n_property_violations') != 0:
        errors.append('production V3 authority gate has declared property violations')
    conc=json.loads((ROOT/'results/concurrency_integrity.json').read_text())
    if conc.get('expected_ingests') != 480 or conc.get('observed_ingests') != 480 or conc.get('error_count') != 0:
        errors.append('concurrency integrity workload incomplete or failed')
    if not conc.get('integrity_ok'):
        errors.append('concurrency integrity check failed')
    priv=json.loads((ROOT/'results/privacy_erasure.json').read_text())
    if priv.get('users') != 50 or priv.get('exports_with_deleted_event_leakage') != 0 or not priv.get('integrity_ok'):
        errors.append('privacy erasure evaluation failed')
    if priv.get('multi_source_siblings_repaired') != 50:
        errors.append('privacy provenance repair incomplete')
    atomic=json.loads((ROOT/'results/atomicity_fault_injection.json').read_text())
    if not atomic.get('all_pass') or atomic.get('passed_faults') != atomic.get('n_faults') or atomic.get('n_faults') < 2:
        errors.append('atomic ingest fault-injection regression failed')
    
    for rel in ['results/database_resilience.json','results/privacy_inventory.json']:
        payload=json.loads((ROOT/rel).read_text())
        if not payload.get('pass'):
            errors.append(f'{rel} did not pass')

    lineage=json.loads((ROOT/'results/experiment_lineage.json').read_text())
    if lineage.get('schema') != 'beliefweave.experiment-lineage.v1' or len(lineage.get('experiments',[])) < 11:
        errors.append('experiment lineage is missing or incomplete')
    for exp in lineage.get('experiments',[]):
        rp=ROOT/exp['result']
        if not rp.exists() or hashlib.sha256(rp.read_bytes()).hexdigest() != exp.get('result_sha256'):
            errors.append(f"experiment lineage result hash mismatch: {exp.get('name')}")
        for item in exp.get('code',[])+exp.get('inputs',[]):
            fp=ROOT/item['path']
            if not fp.exists() or hashlib.sha256(fp.read_bytes()).hexdigest() != item.get('sha256'):
                errors.append(f"experiment lineage dependency hash mismatch: {exp.get('name')}:{item.get('path')}")
    repro=json.loads((ROOT/'results/repro_environment.json').read_text())
    if not repro.get('match'):
        errors.append('release was not validated in the checked reference environment')
    core_install=json.loads((ROOT/'results/core_install.json').read_text())
    if (
        core_install.get('status') != 'PASS'
        or not core_install.get('installed_with_no_dependencies')
        or not core_install.get('core_runtime_without_ml')
    ):
        errors.append('dependency-free core wheel validation failed')
    registry=json.loads((ROOT/'benchmark/external/public_benchmark_registry.json').read_text())
    for k in ['longmemeval_v1','longmemeval_v2','personamem_v1','personamem_v3','claim_policy']:
        if k not in registry: errors.append(f'external registry missing {k}')

except Exception as e:
    errors.append(f'result integrity error: {e}')
tests = json.loads((ROOT/'results/test_summary.json').read_text())
count = tests['passed']
checks = {
    'FINAL_VALIDATION.md':[f'{count}/{count}'],
    'ARTIFACT_MANIFEST.md':[str(count)],
}
for fn, needles in checks.items():
    text = (ROOT/fn).read_text()
    for n in needles:
        if n not in text: errors.append(f'{fn} missing expected text: {n}')
for fn in ['README.md','FINAL_VALIDATION.md','ARTIFACT_MANIFEST.md','RELEASE_NOTES.md','paper/TECHNICAL_REPORT.md','site/index.html']:
    s = (ROOT/fn).read_text()
    for stale in ['0.0571','28/28 regression','28 regression/safety/API tests','36/36','38/38','93.02%','personal_world_model-0.1.0','personal_world_model-0.2.0','47/47 tests','95.82% line coverage','36 regression/safety/API/invariant tests','22/22','release candidate 1.0','confidence is not calibrated;','~562 interactions/s','~570 interactions/s']:
        if stale in s: errors.append(f'{fn} contains stale claim: {stale}')

# Public/release surfaces must not carry a project/release date. Scientific reference years
# and synthetic temporal benchmark timestamps are intentionally outside this check.
date_free_files = [
    'README.md','FINAL_VALIDATION.md','RELEASE_NOTES.md','NOVELTY_AUDIT.md',
    'CITATION.cff','LICENSE','paper/BELIEFWEAVE.tex','site/README.md','site/index.html'
]
for fn in date_free_files:
    fp=ROOT/fn
    if not fp.exists():
        continue
    text=fp.read_text()
    forbidden=[r'date-released:',r'\\date\{[^}]+\}',r'Copyright \(c\) \d{4}',r'Validated[^\n]* on \d{4}[-/]',r'Novelty Audit \([^)]*\d{4}[^)]*\)',r'\blate \d{4}\b',r'\b\d{4} landscape\b',r'\b[A-Z][a-z]+ \d{4} prior-art audit\b']
    for pat in forbidden:
        if __import__('re').search(pat,text): errors.append(f'{fn} contains project/release date pattern: {pat}')
# Generated evidence must not retain wall-clock execution metadata.
try:
    cov_meta=json.loads((ROOT/'results/coverage.json').read_text()).get('meta',{})
    if 'timestamp' in cov_meta: errors.append('coverage.json retains a wall-clock timestamp')
    xml=(ROOT/'results/pytest.xml').read_text()
    if ' timestamp=' in xml: errors.append('pytest.xml retains a wall-clock timestamp')
except Exception as e:
    errors.append(f'date-free evidence audit error: {e}')

try:
    idem=json.loads((ROOT/'results/idempotency_privacy_migration.json').read_text())
    if (
        not idem.get('all_pass')
        or idem.get('schema_current') != CURRENT_SCHEMA_VERSION
        or not idem.get('hard_forget_retry_resurrection_blocked')
        or not idem.get('raw_idempotency_key_not_persisted')
        or not idem.get('tombstone_sensitive_metadata_scrubbed')
        or not idem.get('correction_provenance_preserved')
    ):
        errors.append('idempotency/privacy/migration assurance failed')
except Exception as e:
    errors.append(f'idempotency/privacy/migration result error: {e}')

# Public package identity and review artifacts are part of the release contract.
for required_path in [
    ROOT / 'beliefweave' / '__init__.py',
    ROOT / 'beliefweave' / 'py.typed',
    ROOT / 'scripts' / 'check_core_style.py',
    ROOT / 'docs' / 'adr' / '0001-behavioral-authority.md',
    ROOT / 'docs' / 'adr' / '0002-frozen-evaluation-policies.md',
    ROOT / 'docs' / 'adr' / '0003-idempotency-tombstones.md',
    ROOT / 'docs' / 'adr' / '0004-reference-storage-scope.md',
    ROOT / 'docs' / 'adr' / '0005-core-runtime-and-observability.md',
    ROOT / 'docs' / 'adr' / '0006-deterministic-runtime-and-temporal-contract.md',
    ROOT / 'docker-compose.yml',
    ROOT / 'scripts' / 'validate_core_install.py',
]:
    if not required_path.exists():
        errors.append(f'missing review artifact: {required_path.relative_to(ROOT)}')

try:
    import beliefweave
    if beliefweave.__version__ != VERSION:
        errors.append(
            f'public API version {beliefweave.__version__} != package version {VERSION}'
        )
except Exception as e:
    errors.append(f'public API import failed: {e}')


try:
    compose=(ROOT/'docker-compose.yml').read_text()
    if 'BELIEFWEAVE_DEMO_TOKEN' not in compose or ':?Set BELIEFWEAVE_DEMO_TOKEN' not in compose:
        errors.append('docker-compose demo does not fail closed without an explicit token')
except Exception as e:
    errors.append(f'docker demo access audit error: {e}')

if errors:
    print('RELEASE AUDIT FAILED')
    for e in errors: print('-', e)
    sys.exit(1)
print('RELEASE AUDIT PASSED')
