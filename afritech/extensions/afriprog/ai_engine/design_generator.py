from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.ai_engine.design_output_validator import (
    DesignOutputValidator,
)
from afritech.extensions.afriprog.design_generator.design_orchestrator import (
    DesignOrchestrator,
)


class StructuredDesignGeneratorError(Exception):
    """Raised when structured design output cannot be generated."""


@dataclass(frozen=True)
class StructuredDesignOutput:
    """
    Schema-first design output for AI-engine consumers.

    This adapter deliberately emits dictionaries and lists only. It is not a
    prose/markdown response surface, and it does not grant write authority.
    """

    intent: str
    domain: dict[str, Any]
    requirements: dict[str, Any]
    architecture: dict[str, Any]
    contracts: dict[str, Any]
    implementation_plan: dict[str, Any]
    evidence: dict[str, Any]
    review: dict[str, Any]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afriprog.design_output.v1",
            "format": "structured",
            "intent": self.intent,
            "domain": self.domain,
            "requirements": self.requirements,
            "architecture": self.architecture,
            "contracts": self.contracts,
            "implementation_plan": self.implementation_plan,
            "evidence": self.evidence,
            "review": self.review,
            "write_enabled": False,
            "authority": "proposal_only",
        }


class DesignGenerator:
    """Generate governed design output as structured data, never free text."""

    def __init__(
        self,
        orchestrator: DesignOrchestrator | None = None,
        validator: DesignOutputValidator | None = None,
    ) -> None:
        self.orchestrator = orchestrator or DesignOrchestrator()
        self.validator = validator or DesignOutputValidator()

    def generate(self, intent: str) -> StructuredDesignOutput:
        if not isinstance(intent, str) or not intent.strip():
            raise StructuredDesignGeneratorError("intent must be a non-empty string")

        proposal = self.orchestrator.generate(intent)
        payload = proposal.canonical_dict()

        output = StructuredDesignOutput(
            intent=payload["intent"],
            domain=payload["domain"],
            requirements=payload["requirements"],
            architecture=payload["architecture"],
            contracts={
                "database": payload["database"],
                "api": payload["api"],
                "events": payload["events"],
            },
            implementation_plan=payload["implementation_plan"],
            evidence=payload["evidence"],
            review=payload["review"],
        )
        validation = self.validator.validate(output)
        if not validation.admitted:
            raise StructuredDesignGeneratorError(
                "structured design output failed validation: "
                + "; ".join(validation.violations)
            )
        return output
