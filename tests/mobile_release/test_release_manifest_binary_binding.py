from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts/mobile"


def load_validator():
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "verify_release_manifest_test", SCRIPTS / "verify_release_manifest.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manifest_verification_fails_when_binary_hash_changes(tmp_path: Path) -> None:
    validator = load_validator()
    apk = tmp_path / "rider.apk"
    apk.write_bytes(b"first binary")
    manifest = {
        "release": "test",
        "ga_allowed": False,
        "real_payments_enabled": False,
        "artifacts": {
            "rider": {
                "file": apk.name,
                "sha256": validator.sha256(apk),
                "byte_size": apk.stat().st_size,
                "package_id": "com.novatech.novaride.rider",
                "version_name": "test",
                "version_code": 1,
            },
            "driver": {
                "file": apk.name,
                "sha256": validator.sha256(apk),
                "byte_size": apk.stat().st_size,
                "package_id": "com.novatech.novaride.driver",
                "version_name": "test",
                "version_code": 1,
            },
        },
    }
    (tmp_path / "release-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    apk.write_bytes(b"second binary")

    with pytest.raises(SystemExit, match="byte-size mismatch|SHA-256 mismatch"):
        validator.verify("test", tmp_path, require_apk_tools=False)
