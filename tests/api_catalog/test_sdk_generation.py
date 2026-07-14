from __future__ import annotations

import subprocess
import json
from pathlib import Path

from scripts.api.verify_generated_sdks import verify_generated_sdks


def test_sdk_generation_and_verification_scripts_pass() -> None:
    generated = subprocess.run(["python3", "scripts/api/generate_sdk_artifacts.py"], capture_output=True, text=True, check=False)
    assert generated.returncode == 0, generated.stdout + generated.stderr
    verified = subprocess.run(["python3", "scripts/api/verify_generated_sdks.py"], capture_output=True, text=True, check=False)
    assert verified.returncode == 0, verified.stdout + verified.stderr


def test_sdk_version_mismatch_fails_verification() -> None:
    metadata_path = Path("sdk/novapay/python/sdk-metadata.json")
    original = metadata_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["contract_version"] = "1900.01.0"
        metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        assert any(issue.startswith("contract_version_mismatch:novapay:python") for issue in verify_generated_sdks())
    finally:
        metadata_path.write_text(original, encoding="utf-8")
