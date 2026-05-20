"""Shared orchestration helpers for compressed CI validators."""

from __future__ import annotations

import importlib
from collections.abc import Iterable


def run_validator_modules(modules: Iterable[str]) -> None:
    for module_name in modules:
        module = importlib.import_module(module_name)
        for entrypoint in ("validate", "run", "main"):
            candidate = getattr(module, entrypoint, None)
            if candidate is None:
                continue

            result = candidate()
            if result not in (0, None):
                raise SystemExit(result)
            break
        else:
            raise RuntimeError(f"{module_name} exposes no validator entrypoint")
