# AfriTech Safe Import Rules Checklist

Status: AFRITECH SAFE IMPORT RULES CHECKLIST

Classification: BOUNDED STARTUP SAFETY CHECKLIST

Purpose: provide a practical checklist for engineers changing startup-critical
runtime paths so FastAPI imports remain safe and Django state initialization
remains explicit.

## Use This Checklist Before Merging

- Does the changed module sit on the `afritech.api.app` import path?
- Does the module import `django.*` or `rest_framework.*`?
- Does the module define or import `models.Model` subclasses?
- Does the module touch `settings`, `apps`, or ORM managers at import time?
- Does the module execute I/O, queue setup, or state reads during import?
- Does the module assume environment variables already exist?
- Does the module assume signing keys already exist?
- Does the module assume traces or receipts exist on disk?

## Safe Import Rules

- Keep FastAPI startup modules pure-Python where possible.
- Prefer function-level imports for Django-bound code.
- Prefer lazy service loaders over top-level ORM imports.
- Guard optional dependencies with fallback behavior where possible.
- Keep route registration import-safe.
- Keep `uvicorn afritech.api.app:app` startup side effects minimal.
- Make health endpoints lightweight and self-contained.
- Do not bind production truth to dashboard startup.

## Unsafe Import Smells

- `from django.db import models` in a startup-critical module
- `from rest_framework.response import Response` in a FastAPI startup path
- model manager calls at module level
- app-registry access during import
- top-level filesystem scanning for large directories
- top-level network calls
- top-level environment mutation with hidden side effects

## Required Patterns

- `DJANGO_SETTINGS_MODULE` must be set before `django.setup()`
- `django.setup()` must run only when needed
- Django model import must happen after setup in mixed runtime paths
- startup-safe auth helpers must not require DRF to exist
- public verification endpoints must remain bounded and read-only

## Review Questions

- If this module were imported in an empty container, would it crash?
- If Django settings were missing, would import still succeed?
- If DRF were not installed, would FastAPI startup still succeed?
- If the dashboard build were absent, would the API still boot?
- If traces directory were empty, would trace APIs degrade safely?

## Release Checklist

- Run targeted startup tests.
- Rebuild the API image with `--no-cache` when dependency metadata changes.
- Verify `/health` returns `{"status":"ok"}`.
- Verify startup logs do not show `ImproperlyConfigured`.
- Verify startup logs do not show `ModuleNotFoundError`.
- Verify public verifier routes still boot.
- Verify dashboard builds against the current API URL.

## Stop-Ship Conditions

- FastAPI import path requires Django settings at module import time.
- API image depends on undeclared packages.
- `.env.production` is being overwritten by sync tooling.
- startup health probe fails due to import-time side effects.
- a legacy Django/DRF module shadows a newer package path without guardrails.
