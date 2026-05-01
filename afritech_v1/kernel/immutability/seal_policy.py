# afritech_v1/kernel/immutability/seal_policy.py

import os
from dataclasses import dataclass
from typing import Dict, List


# =========================================================
# 🔐 SEAL GOVERNANCE MODEL (v1)
# =========================================================
# This file defines WHEN kernel changes are allowed
# and HOW seal regeneration must be interpreted.
# =========================================================


@dataclass(frozen=True)
class SealPolicy:
    """
    Defines immutable rules governing kernel seal updates.
    """

    # Directories allowed to evolve without being considered tampering
    allowed_evolution_paths: List[str]

    # Whether kernel structural expansion is permitted
    allow_structural_growth: bool = True

    # Whether seal regeneration requires explicit command (rebase mode)
    require_explicit_rebase: bool = True

    # Whether unknown changes should always fail the system
    strict_mode: bool = True


# =========================================================
# 🧠 DEFAULT AFRITECH POLICY (v1)
# =========================================================

DEFAULT_POLICY = SealPolicy(
    allowed_evolution_paths=[
        "afritech_v1/kernel/immutability/",  # self-extension allowed
    ],
    allow_structural_growth=True,
    require_explicit_rebase=True,
    strict_mode=True,
)


# =========================================================
# 🔍 CHANGE CLASSIFICATION ENGINE
# =========================================================

class ChangeType:
    STABLE = "STABLE"          # no change
    EVOLUTION = "EVOLUTION"    # allowed structural change
    TAMPERING = "TAMPERING"    # illegal modification
    UNKNOWN = "UNKNOWN"


def classify_change(file_path: str, policy: SealPolicy = DEFAULT_POLICY) -> str:
    """
    Classifies whether a kernel file change is:
    - safe evolution
    - tampering
    - unknown anomaly
    """

    normalized = file_path.replace("\\", "/")

    # 1. Allowed structural evolution
    for allowed_path in policy.allowed_evolution_paths:
        if normalized.startswith(allowed_path):
            return ChangeType.EVOLUTION

    # 2. Kernel core protection rule
    if "kernel/" in normalized:
        return ChangeType.TAMPERING

    # 3. Default fallback
    return ChangeType.UNKNOWN


# =========================================================
# 🔐 SEAL REGENERATION RULE
# =========================================================

def can_regenerate_seal(trigger: str, policy: SealPolicy = DEFAULT_POLICY) -> bool:
    """
    Controls whether seal regeneration is permitted.
    """

    if policy.require_explicit_rebase:
        return trigger == "rebase"

    return True


# =========================================================
# 🧾 POLICY DEBUG VIEW
# =========================================================

def print_policy():
    print("\n🔐 AFRITECH SEAL POLICY (v1)")
    print("--------------------------------")
    print(f"Strict mode: {DEFAULT_POLICY.strict_mode}")
    print(f"Require rebase: {DEFAULT_POLICY.require_explicit_rebase}")
    print(f"Allowed evolution paths:")
    for p in DEFAULT_POLICY.allowed_evolution_paths:
        print(f"  - {p}")