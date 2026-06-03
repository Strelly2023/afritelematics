from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.design_generator.architecture.architecture_generator import (
    ArchitectureGenerator,
    ArchitectureProposal,
)
from afritech.extensions.afriprog.design_generator.contracts.api_contract_generator import (
    APIContractGenerator,
    APIContractSet,
)
from afritech.extensions.afriprog.design_generator.contracts.database_contract_generator import (
    DatabaseContractGenerator,
    DatabaseContractSet,
)
from afritech.extensions.afriprog.design_generator.contracts.event_contract_generator import (
    EventContractGenerator,
    EventContractSet,
)
from afritech.extensions.afriprog.design_generator.evidence.design_evidence_generator import (
    DesignEvidenceGenerator,
)
from afritech.extensions.afriprog.design_generator.planning.implementation_plan_generator import (
    ImplementationPlan,
    ImplementationPlanGenerator,
)
from afritech.extensions.afriprog.design_generator.requirements.requirements_extractor import (
    RequirementSet,
    RequirementsExtractor,
)
from afritech.extensions.afriprog.design_generator.requirements.domain_analyzer import (
    DomainAnalysis,
)
from afritech.extensions.afriprog.evidence.evidence_model import EvidenceRecord
from afritech.extensions.afriprog.design_generator.design_reviewer import (
    DesignReview,
    DesignReviewer,
)


@dataclass(frozen=True)
class DesignProposal:
    intent: str
    domain: DomainAnalysis
    requirements: RequirementSet
    architecture: ArchitectureProposal
    database: DatabaseContractSet
    api: APIContractSet
    events: EventContractSet
    implementation_plan: ImplementationPlan
    evidence: EvidenceRecord
    review: DesignReview

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "domain": self.domain.canonical_dict(),
            "requirements": self.requirements.canonical_dict(),
            "architecture": self.architecture.canonical_dict(),
            "database": self.database.canonical_dict(),
            "api": self.api.canonical_dict(),
            "events": self.events.canonical_dict(),
            "implementation_plan": self.implementation_plan.canonical_dict(),
            "evidence": self.evidence.canonical_dict(),
            "review": self.review.canonical_dict(),
            "write_enabled": False,
            "authority": "proposal_only",
        }


class DesignOrchestrator:
    """Generate proposal-only software designs from intent."""

    def __init__(
        self,
        *,
        requirements_extractor: RequirementsExtractor | None = None,
        architecture_generator: ArchitectureGenerator | None = None,
        database_generator: DatabaseContractGenerator | None = None,
        api_generator: APIContractGenerator | None = None,
        event_generator: EventContractGenerator | None = None,
        plan_generator: ImplementationPlanGenerator | None = None,
        evidence_generator: DesignEvidenceGenerator | None = None,
        reviewer: DesignReviewer | None = None,
    ) -> None:
        self.requirements_extractor = requirements_extractor or RequirementsExtractor()
        self.architecture_generator = architecture_generator or ArchitectureGenerator()
        self.database_generator = database_generator or DatabaseContractGenerator()
        self.api_generator = api_generator or APIContractGenerator()
        self.event_generator = event_generator or EventContractGenerator()
        self.plan_generator = plan_generator or ImplementationPlanGenerator()
        self.evidence_generator = evidence_generator or DesignEvidenceGenerator()
        self.reviewer = reviewer or DesignReviewer()

    def generate(self, intent: str) -> DesignProposal:
        domain, requirements = self.requirements_extractor.extract(intent)
        architecture = self.architecture_generator.generate(domain)
        database = self.database_generator.generate(domain)
        api = self.api_generator.generate(domain)
        events = self.event_generator.generate(domain)
        implementation_plan = self.plan_generator.generate(architecture)

        proposal_without_evidence = _DesignProposalPayload(
            intent=domain.intent,
            domain=domain,
            requirements=requirements,
            architecture=architecture,
            database=database,
            api=api,
            events=events,
            implementation_plan=implementation_plan,
        )
        evidence = self.evidence_generator.from_design(proposal_without_evidence)
        review_payload = _DesignProposalPayload(
            intent=domain.intent,
            domain=domain,
            requirements=requirements,
            architecture=architecture,
            database=database,
            api=api,
            events=events,
            implementation_plan=implementation_plan,
        )
        review = self.reviewer.review(review_payload)

        return DesignProposal(
            intent=domain.intent,
            domain=domain,
            requirements=requirements,
            architecture=architecture,
            database=database,
            api=api,
            events=events,
            implementation_plan=implementation_plan,
            evidence=evidence,
            review=review,
        )


@dataclass(frozen=True)
class _DesignProposalPayload:
    intent: str
    domain: DomainAnalysis
    requirements: RequirementSet
    architecture: ArchitectureProposal
    database: DatabaseContractSet
    api: APIContractSet
    events: EventContractSet
    implementation_plan: ImplementationPlan

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "domain": self.domain.canonical_dict(),
            "requirements": self.requirements.canonical_dict(),
            "architecture": self.architecture.canonical_dict(),
            "database": self.database.canonical_dict(),
            "api": self.api.canonical_dict(),
            "events": self.events.canonical_dict(),
            "implementation_plan": self.implementation_plan.canonical_dict(),
            "write_enabled": False,
            "authority": "proposal_only",
        }
