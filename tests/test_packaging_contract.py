from pathlib import Path
import tomllib
import pwm
from pwm.engine import PersonalMemoryEngine
from pwm.observations.hybrid import HybridObservationExtractor
from pwm.world_model.hybrid_conflict import HybridConflictResolver

ROOT = Path(__file__).resolve().parents[1]

def test_package_assets_and_runtime_profiles_are_explicit(tmp_path):
    assets = Path(pwm.__file__).resolve().parent / 'assets'
    assert (assets / 'observation_router.joblib').exists()
    assert (assets / 'conflict_model.joblib').exists()

    core = PersonalMemoryEngine(tmp_path / 'core.db')
    assert core.ml_enabled is False

    ml = PersonalMemoryEngine(tmp_path / 'ml.db', enable_ml=True)
    assert isinstance(ml.extractor, HybridObservationExtractor)
    assert isinstance(ml.conflicts, HybridConflictResolver)
    assert ml.ml_enabled is True


def test_pyproject_declares_core_runtime_dependencies_and_explicit_package_discovery():
    data = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    deps = set(data['project']['dependencies'])
    assert deps == set()
    ml = set(data['project']['optional-dependencies']['ml'])
    assert any(x.startswith('scikit-learn') for x in ml)
    assert any(x.startswith('joblib') for x in ml)
    include = data['tool']['setuptools']['packages']['find']['include']
    assert include == ['pwm*', 'beliefweave*']
    assert data['tool']['setuptools']['package-data']['pwm'] == ['assets/*.joblib']
