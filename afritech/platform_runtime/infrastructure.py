"""Infrastructure planning primitives for NovaTech product runtimes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .models import InfrastructureKind, InfrastructureRequirement, ProvisioningPlan, ProvisioningResult, RollbackResult, VerificationResult


class InfrastructureOwnership(StrEnum):
    PLATFORM = "platform"
    PRODUCT = "product"
    SHARED = "shared"


@dataclass(frozen=True, slots=True)
class InfrastructurePlanStep:
    requirement: InfrastructureRequirement
    action: str
    destructive: bool = False
    details: Mapping[str, Any] = field(default_factory=dict)


__all__ = [
    "InfrastructureKind",
    "InfrastructureOwnership",
    "InfrastructurePlanStep",
    "InfrastructureRequirement",
    "ProvisioningPlan",
    "ProvisioningResult",
    "RollbackResult",
    "VerificationResult",
]
