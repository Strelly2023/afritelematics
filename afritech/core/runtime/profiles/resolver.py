from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[4]
PROFILES_PATH = ROOT / "afritech/constitution/profiles.yaml"


class ProfileResolutionError(RuntimeError):
    pass


def _load_profiles() -> dict[str, dict[str, Any]]:
    payload = yaml.safe_load(PROFILES_PATH.read_text(encoding="utf-8"))
    profiles = payload.get("profiles") if isinstance(payload, dict) else None

    if not isinstance(profiles, dict):
        raise ProfileResolutionError("profiles_not_declared")

    return profiles


def resolve_profile(profile_name: str) -> dict[str, Any]:
    profiles = _load_profiles()

    if profile_name not in profiles:
        raise ProfileResolutionError(f"unknown_profile:{profile_name}")

    profile = profiles[profile_name]
    return {
        "profile": profile_name,
        "requires": tuple(profile["requires"]),
        "forbids": tuple(profile["forbids"]),
        "runtime_constraints": dict(profile["runtime_constraints"]),
    }


def validate_operation(
    operation: Mapping[str, Any],
    constraint_set: Mapping[str, Any],
) -> bool:
    constraints = constraint_set.get("runtime_constraints", {})

    if constraints.get("deterministic_only") is True:
        if operation.get("deterministic") is not True:
            return False

    if constraints.get("allow_side_effects") is False:
        if operation.get("side_effects"):
            return False

    if constraints.get("replay_required") is True:
        if operation.get("replayable") is not True:
            return False

    if constraints.get("proof_required") is True:
        if operation.get("proof") is not True:
            return False

    return True
