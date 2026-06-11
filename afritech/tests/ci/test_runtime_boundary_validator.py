from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from afritech.ci.runtime_boundary_validator import BoundaryReport, RuntimeBoundaryValidator, coerce_boundary_report


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_runtime_boundary_validator_detects_transitive_startup_violation(tmp_path):
    _write(tmp_path / "sample/__init__.py", "")
    _write(tmp_path / "sample/api/__init__.py", "")
    _write(
        tmp_path / "sample/api/app.py",
        "from sample.api.auth.jwt_device_auth import build_router\n",
    )
    _write(
        tmp_path / "sample/api/auth.py",
        "from django.conf import settings\n__path__ = []\n",
    )
    _write(
        tmp_path / "sample/api/auth/__init__.py",
        "",
    )
    _write(
        tmp_path / "sample/api/auth/jwt_device_auth.py",
        "def build_router():\n    return None\n",
    )

    report = RuntimeBoundaryValidator(
        root=tmp_path,
        startup_module="sample.api.app",
        scan_prefixes=("sample.api",),
    ).build_report()

    assert any(v.code == "RBV-001" and v.module == "sample.api.auth" for v in report.violations)
    assert any("sample.api.app" in v.import_chain for v in report.violations)


def test_runtime_boundary_validator_passes_safe_startup_sample(tmp_path):
    _write(tmp_path / "sample/__init__.py", "")
    _write(tmp_path / "sample/api/__init__.py", "")
    _write(
        tmp_path / "sample/api/app.py",
        "from sample.api.auth.jwt_device_auth import build_router\n",
    )
    _write(tmp_path / "sample/api/auth/__init__.py", "")
    _write(
        tmp_path / "sample/api/auth/jwt_device_auth.py",
        "def build_router():\n    return None\n",
    )

    report = RuntimeBoundaryValidator(
        root=tmp_path,
        startup_module="sample.api.app",
        scan_prefixes=("sample.api",),
    ).build_report()

    assert report.violations == ()


def test_runtime_boundary_validator_cli_emits_markdown_report(tmp_path):
    output = tmp_path / "runtime-boundary.md"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "afritech.ci.runtime_boundary_validator",
            "--markdown-out",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "# AfriTech Runtime Boundary Scan" in text
    assert "Violations" in text


def test_boundary_report_coercion_accepts_attribute_fallback_report():
    class FallbackReport:
        startup_module = "afritech.api.app"
        scanned_modules = 7
        startup_modules = ["afritech.api.app"]
        violations = []

    report = coerce_boundary_report(FallbackReport())

    assert report.startup_module == "afritech.api.app"
    assert report.scanned_modules == 7
    assert report.startup_modules == ("afritech.api.app",)
    assert report.declared_django_modules == ()
    assert report.to_markdown().startswith("# AfriTech Runtime Boundary Scan")


def test_boundary_report_coercion_accepts_attribute_violations():
    class FallbackViolation:
        code = "RBV-999"
        severity = "high"
        module = "afritech.api.bad"
        path = "afritech/api/bad.py"
        detail = "fallback object violation"
        import_chain = ["afritech.api.app", "afritech.api.bad"]

    class FallbackReport:
        startup_module = "afritech.api.app"
        scanned_modules = 1
        startup_modules = ["afritech.api.app"]
        declared_django_modules = []
        violations = [FallbackViolation()]

    report = coerce_boundary_report(FallbackReport())

    assert report.violations[0].code == "RBV-999"
    assert report.violations[0].import_chain == ("afritech.api.app", "afritech.api.bad")


def test_boundary_report_coercion_rebuilds_boundary_report_subclass_missing_fields():
    fallback = object.__new__(BoundaryReport)
    object.__setattr__(fallback, "startup_module", "afritech.api.app")
    object.__setattr__(fallback, "scanned_modules", 3)
    object.__setattr__(fallback, "startup_modules", ["afritech.api.app"])
    object.__setattr__(fallback, "violations", [])

    report = coerce_boundary_report(fallback)

    assert type(report) is BoundaryReport
    assert report.declared_django_modules == ()
    assert report.to_markdown().startswith("# AfriTech Runtime Boundary Scan")
