from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def test_actual_app_has_one_platform_product_registration_authority(
    tmp_path: Path,
) -> None:
    env = os.environ.copy()

    env.update(
        {
            "NOVATECH_RUNTIME_CONTROL_SQLITE_PATH": str(
                tmp_path / "runtime-control.sqlite3"
            ),
            "NOVATECH_EVIDENCE_ROOT": str(
                tmp_path / "runtime-evidence"
            ),
            "AFRIRIDE_DB_PATH": str(
                tmp_path / "pilot-state.sqlite3"
            ),
            "AFRITECH_RUNTIME_ENVIRONMENT": "staging",
            "AFRITECH_ENV": "staging",
            "NOVARIDE_ENVIRONMENT": "staging",
        }
    )

    code = r'''
from afritech.api.app import app

matches = [
    route
    for route in app.routes
    if (
        getattr(route, "path", None)
        == "/v1/platform/products"
        and "POST"
        in getattr(
            route,
            "methods",
            set(),
        )
    )
]

assert len(matches) == 1, [
    (
        getattr(route.endpoint, "__module__", None),
        getattr(route.endpoint, "__qualname__", None),
    )
    for route in matches
]

endpoint = matches[0].endpoint

assert (
    endpoint.__module__
    == "afritech.api.platform_runtime_api"
)

assert (
    endpoint.__qualname__
    == "build_platform_runtime_router.<locals>.register_product"
)
'''

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
        ],
        cwd=Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
    )

    assert result.returncode == 0, (
        result.stdout
        + "\n"
        + result.stderr
    )
