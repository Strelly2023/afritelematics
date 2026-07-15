from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_generated_sdk_modules_and_release_certificate_remain_honest() -> None:
    subprocess.run(["bash", "scripts/novaride/generate_api_sdk.sh"], check=True)
    subprocess.run(["python3", "scripts/novaride/verify_api_sdk_current.py"], check=True)

    report = json.loads(Path("reports/novaride/deployment/api-sdk-verification.json").read_text())
    assert report["status"] == "PASS"
    assert report["live_openapi_export_verified"] is False
    for module in ["rider", "driver", "operator", "fleet", "logistics", "corporate", "transit", "safety", "diagnostics", "replay", "models"]:
        assert Path(f"packages/novaride-api-sdk/src/generated/{module}.ts").exists()
