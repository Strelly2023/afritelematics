from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_production_runtime_map_doc_covers_active_runtime_and_non_claims() -> None:
    text = _read("docs/architecture/AFRITECH_PRODUCTION_RUNTIME_MAP.md")

    for item in (
        "Status: AFRITECH PRODUCTION RUNTIME MAP",
        "Classification: BOUNDED PRODUCTION RUNTIME COORDINATION SURFACE",
        "afritech/api/app.py",
        "deploy/production/docker-compose.production.yml",
        "Incoming request/event",
        "-> FastAPI auth gate",
        "-> Edge adaptation",
        "-> Django-backed state access where required",
        "Trace / replay / evidence / receipt",
        "Public verification routes must remain bounded to `/public/*`.",
    ):
        assert item in text


def test_fastapi_django_boundary_contract_defines_allowed_and_forbidden_paths() -> None:
    text = _read("docs/architecture/AFRITECH_FASTAPI_DJANGO_BOUNDARY_CONTRACT.md")

    for item in (
        "Status: AFRITECH FASTAPI VS DJANGO BOUNDARY CONTRACT",
        "FastAPI import time must not require Django settings.",
        "Allowed FastAPI -> Django Paths",
        "Forbidden FastAPI -> Django Paths",
        "DJANGO_SETTINGS_MODULE",
        "django.setup()",
        "FastAPI and Django may coexist",
        "import-time coupling is the primary thing to prevent",
    ):
        assert item in text


def test_safe_import_rules_checklist_preserves_startup_safety_focus() -> None:
    text = _read("docs/operations/AFRITECH_SAFE_IMPORT_RULES_CHECKLIST.md")

    for item in (
        "Status: AFRITECH SAFE IMPORT RULES CHECKLIST",
        "Does the changed module sit on the `afritech.api.app` import path?",
        "Unsafe Import Smells",
        "from django.db import models",
        "from rest_framework.response import Response",
        "Stop-Ship Conditions",
        "legacy Django/DRF module shadows a newer package path without guardrails",
    ):
        assert item in text


def test_production_api_image_includes_public_proof_documents() -> None:
    compose = _read("deploy/production/docker-compose.production.yml")
    dockerfile_path = "deploy/staging/Dockerfile.api"
    dockerfile = _read(dockerfile_path)

    assert f"dockerfile: {dockerfile_path}" in compose
    assert "COPY docs /app/docs" in dockerfile


def test_partner_live_demo_script_preserves_runtime_truth_positioning() -> None:
    text = _read("docs/pitch/AFRITECH_PARTNER_LIVE_DEMO_SCRIPT_RUNTIME_BOUNDARY.md")

    for item in (
        "Status: AFRITECH PARTNER LIVE DEMO SCRIPT",
        "FastAPI orchestrates.",
        "Django stores state.",
        "Replay proves.",
        "Dashboard observes.",
        "/public/verify/health",
        "The dashboard is intentionally an observation surface.",
        "It is a runtime-first trust claim.",
    ):
        assert item in text
