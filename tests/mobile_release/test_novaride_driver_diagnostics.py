from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_driver_startup_diagnostics_are_implemented() -> None:
    diagnostics_dir = ROOT / "driver_app/core/diagnostics"
    for name in [
        "startupDiagnostics.ts",
        "networkDiagnostics.ts",
        "apiDiagnostics.ts",
        "locationDiagnostics.ts",
        "buildDiagnostics.ts",
        "diagnosticTypes.ts",
        "index.ts",
    ]:
        assert (diagnostics_dir / name).exists()
    source = (diagnostics_dir / "diagnosticTypes.ts").read_text(encoding="utf-8")
    for action in ["Retry", "Open network settings", "Re-authenticate", "Continue offline when safe"]:
        assert action in source

