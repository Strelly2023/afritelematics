from __future__ import annotations

import importlib.util
import stat
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/provision_novaid_production_security.py"
SPEC = importlib.util.spec_from_file_location("novaid_security_provisioning", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_provisioning_is_atomic_complete_and_non_overwriting(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.production"
    env_file.write_text("AFRITECH_DOMAIN=identity.example\n", encoding="utf-8")
    env_file.chmod(0o600)

    backup = module.provision(env_file)
    values = dict(
        line.split("=", 1)
        for line in env_file.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    )
    assert set(module.MANAGED_KEYS) <= values.keys()
    assert values["NOVAID_JWT_ISSUER"] == "https://identity.example/novaid"
    assert values["NOVAID_ACTIVE_SIGNING_KEY_ID"] in values["NOVAID_SIGNING_KEYS_JSON"]
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600
    assert stat.S_IMODE(backup.stat().st_mode) == 0o600

    with pytest.raises(module.ProvisioningError, match="already exists"):
        module.provision(env_file)
