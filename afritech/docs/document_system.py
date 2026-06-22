from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from textwrap import dedent
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = ROOT / "docs"
GOVERNANCE_ROOT = DOCS_ROOT / "governance"
REGISTRY_ROOT = DOCS_ROOT / "registry"
CERT_ROOT = REGISTRY_ROOT / "certificates"
LINEAGE_ROOT = REGISTRY_ROOT / "lineage"
COMPLIANCE_REGISTRY_PATH = REGISTRY_ROOT / "DOCUMENTATION_COMPLIANCE_REGISTRY.yaml"
VALIDATOR_VERSION = "novatech-doc-system-v1"


def block(text: str) -> str:
    return dedent(text).strip("\n")


def sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def ensure_dirs() -> None:
    for path in (REGISTRY_ROOT, CERT_ROOT, LINEAGE_ROOT):
        path.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def table_header() -> str:
    return "| Field | Value |\n|---|---|"


def source_table(paths: Iterable[Path]) -> str:
    lines = [
        "## Document Lineage",
        "",
        "| Source Document | SHA256 |",
        "|---|---|",
    ]
    for path in paths:
        lines.append(f"| `{rel(path)}` | `{sha256_file(path)}` |")
    return "\n".join(lines)


def short_lineage_note(source_manifest: Path, certificate: Path) -> str:
    return block(
        f"""
        ## Documentation Certification

        This document is certified through the NovaTech documentation system.

        - Source manifest: `{rel(source_manifest)}`
        - Certificate: `{rel(certificate)}`
        - Validator version: `{VALIDATOR_VERSION}`
        """
    )


def discovered_governed_sources() -> list[Path]:
    source_dirs = [
        DOCS_ROOT / "api",
        DOCS_ROOT / "adoption",
        DOCS_ROOT / "business",
        DOCS_ROOT / "certification",
        DOCS_ROOT / "governance",
        DOCS_ROOT / "operations",
        DOCS_ROOT / "partners",
        DOCS_ROOT / "pilot",
        DOCS_ROOT / "proof",
        DOCS_ROOT / "roadmap",
        DOCS_ROOT / "standards",
        DOCS_ROOT / "strategy",
        DOCS_ROOT / "vision",
        DOCS_ROOT / "whitepaper",
        DOCS_ROOT / "mobile",
    ]
    excluded = {
        GOVERNANCE_ROOT / "NOVATECH_PLATFORM_ADMINISTRATOR_AND_STAFF_MANUAL_V2.md",
        GOVERNANCE_ROOT / "NOVATECH_EXECUTIVE_MANUAL.md",
        GOVERNANCE_ROOT / "NOVATECH_OPERATOR_MANUAL.md",
        GOVERNANCE_ROOT / "NOVATECH_AUDITOR_MANUAL.md",
        GOVERNANCE_ROOT / "NOVATECH_DEVELOPER_MANUAL.md",
        GOVERNANCE_ROOT / "NOVATECH_PARTNER_MANUAL.md",
        GOVERNANCE_ROOT / "NOVATECH_INVESTOR_MANUAL.md",
    }
    docs: list[Path] = []
    for base in source_dirs:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            if path in excluded:
                continue
            docs.append(path)
    return docs


def _section(title: str, body: str) -> str:
    return block(
        f"""
        ## {title}

        {body}
        """
    )


def _bullets(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _sources_source_docs(paths: Iterable[Path]) -> list[dict[str, str]]:
    return [{"path": rel(path), "sha256": sha256_file(path)} for path in paths]


SECTION_MAP: dict[str, list[str]] = {
    "executive": [
        "1. Platform Architecture",
        "5. Governance and Constitution",
        "10. NovaScript, Analytics, and Decision Intelligence",
        "11. NovaPay, Finance, and Billing",
        "12. Organization OS",
        "13. Multi-Tenant SaaS Operations",
        "14. Controlled Execution and Safety",
        "15. Outcome Intelligence and Learning",
        "16. Federated Trust Network and Marketplace",
        "20. Change, Release, and Deployment Management",
        "22. Operational Cadence",
        "24. Manual Maintenance Rules",
        "25. Appendix Pack Overview",
        "26. Documentation Certification and Compliance Product",
    ],
    "operator": [
        "4. Dashboard Map and Navigation",
        "6. Runtime Operations",
        "7. Proof and Verification",
        "8. Trust Management",
        "12. Organization OS",
        "14. Controlled Execution and Safety",
        "18. Security, Privacy, and Records",
        "19. Incident Management and Escalation",
        "21. Onboarding, Training, and Support",
        "22. Operational Cadence",
        "26. Documentation Certification and Compliance Product",
    ],
    "auditor": [
        "5. Governance and Constitution",
        "7. Proof and Verification",
        "8. Trust Management",
        "14. Controlled Execution and Safety",
        "18. Security, Privacy, and Records",
        "24. Manual Maintenance Rules",
        "25. Appendix Pack Overview",
        "26. Documentation Certification and Compliance Product",
    ],
    "developer": [
        "2. Roles and Access Model",
        "5. Governance and Constitution",
        "6. Runtime Operations",
        "9. NovaProgramming Operations",
        "14. Controlled Execution and Safety",
        "19. Incident Management and Escalation",
        "20. Change, Release, and Deployment Management",
        "23. Appendix Templates and Forms",
        "24. Manual Maintenance Rules",
        "26. Documentation Certification and Compliance Product",
    ],
    "partner": [
        "12. Organization OS",
        "13. Multi-Tenant SaaS Operations",
        "15. Outcome Intelligence and Learning",
        "16. Federated Trust Network and Marketplace",
        "17. Product Operations",
        "18. Security, Privacy, and Records",
        "21. Onboarding, Training, and Support",
        "24. Manual Maintenance Rules",
        "25. Appendix Pack Overview",
        "26. Documentation Certification and Compliance Product",
    ],
    "investor": [
        "1. Platform Architecture",
        "11. NovaPay, Finance, and Billing",
        "12. Organization OS",
        "13. Multi-Tenant SaaS Operations",
        "15. Outcome Intelligence and Learning",
        "16. Federated Trust Network and Marketplace",
        "17. Product Operations",
        "20. Change, Release, and Deployment Management",
        "22. Operational Cadence",
        "24. Manual Maintenance Rules",
        "25. Appendix Pack Overview",
        "26. Documentation Certification and Compliance Product",
    ],
}


COMMON_ASSURANCE_SECTIONS: list[str] = [
    "Launch Sequence",
    "Required Readiness Sections",
    "Phase 1: Persistence",
    "Phase 2: Authentication",
    "Phase 3: Evidence Durability",
    "Phase 4: Dashboard Contract Alignment",
    "Cross-Cutting Rules",
    "Suggested Delivery Order",
    "Current Blockers",
    "Operational notes",
    "Required Repo-Side Validators",
    "Use This Checklist Before Merging",
    "Safe Import Rules",
    "Required Patterns",
    "Release Checklist",
    "Completion Definition",
]


def extract_sections(reference_text: str, titles: list[str]) -> list[str]:
    sections: list[str] = []
    for title in titles:
        pattern = rf"(?ms)^## {re.escape(title)}\n(.*?)(?=^## |\Z)"
        match = re.search(pattern, reference_text)
        if not match:
            raise ValueError(f"missing section in full reference: {title}")
        sections.append(block(f"## {title}\n\n{match.group(1).strip()}"))
    return sections


def compose_profile_from_reference(
    *,
    profile: str,
    full_reference_path: Path,
    source_paths: list[Path],
) -> str:
    spec = next(item for item in PROFILE_DEFINITIONS if item["profile"] == profile)
    reference_text = full_reference_path.read_text(encoding="utf-8")
    titles = list(dict.fromkeys([*SECTION_MAP[profile], *COMMON_ASSURANCE_SECTIONS]))
    intro = block(
        f"""
        # {spec['title']}

        ## Version 1.0

        **Status:** Official role-specific manual

        **Audience:** { {
            'executive': 'Executives and strategic leaders',
            'operator': 'Operations administrators and support operators',
            'auditor': 'Auditors, trust administrators, and verification staff',
            'developer': 'Developers and release engineers',
            'partner': 'Partners, suppliers, and external operators',
            'investor': 'Investors, board observers, and strategic partners',
        }[profile] }

        **Owner:** {spec['owner']}

        **Purpose:** { {
            'executive': 'Executive operating reference for the NovaTech platform.',
            'operator': 'Operational runbook for live dashboard and incident work.',
            'auditor': 'Verification and evidence review reference.',
            'developer': 'Engineering control reference for governed change delivery.',
            'partner': 'External collaboration and trust exchange reference.',
            'investor': 'Strategic overview of the platform, operating model, and scale controls.',
        }[profile] }

        **Authority boundary:** This manual explains governed operations and role-specific guidance. It does not replace constitutional truth, legal review, production incident authority, or the full reference manual.

        ## Document Control

        {table_header()}
        | Document ID | {spec['document_id']} |
        | Version | 1.0 |
        | Classification | {spec['classification']} |
        | Owner | {spec['owner']} |
        | Minimum Words | {spec['minimum_words']} |
        | Source Count | {len(source_paths)} |
        | Source Manifest | `{rel(LINEAGE_ROOT / f"{spec['document_id']}.sources.json")}` |
        | Certificate | `{rel(CERT_ROOT / f"{spec['document_id']}.json")}` |
        """
    )
    sections = extract_sections(reference_text, titles)
    role_focus = {
        "executive": _section(
            "Executive Focus",
            _bullets(
                [
                    "Review platform health, trust movement, and economic posture.",
                    "Approve or defer controlled execution readiness.",
                    "Require proof before external publication.",
                    "Check outcome learning before changing policy or funding.",
                ]
            ),
        ),
        "operator": _section(
            "Operator Focus",
            _bullets(
                [
                    "Watch live signals before they become incidents.",
                    "Preserve proof whenever the runtime deviates.",
                    "Use the incident ladder and handover rules.",
                    "Treat dashboard state as guidance, not authority.",
                ]
            ),
        ),
        "auditor": _section(
            "Auditor Focus",
            _bullets(
                [
                    "Trace claims back to evidence and registry entries.",
                    "Confirm that certification follows proof.",
                    "Check for unauthorized mutation of evidence.",
                    "Require lineage before publication or escalation closure.",
                ]
            ),
        ),
        "developer": _section(
            "Developer Focus",
            _bullets(
                [
                    "Preserve proof and replay semantics in every change.",
                    "Run validators before release.",
                    "Update documentation when contracts or control surfaces change.",
                    "Keep authority boundaries out of UI and analytics code.",
                ]
            ),
        ),
        "partner": _section(
            "Partner Focus",
            _bullets(
                [
                    "Understand the onboarding and trust exchange path.",
                    "Use only the services your tenancy can consume.",
                    "Provide the evidence required for certification.",
                    "Escalate verification failures through the approved support path.",
                ]
            ),
        ),
        "investor": _section(
            "Investor Focus",
            _bullets(
                [
                    "Track tenant growth, trust posture, and commercial readiness.",
                    "Understand controlled execution and safety gating.",
                    "Review the platform's moat in proof and verification.",
                    "Do not confuse platform readiness with market claims.",
                ]
            ),
        ),
    }[profile]
    lineage = source_table(source_paths)
    cert_note = short_lineage_note(
        LINEAGE_ROOT / f"{spec['document_id']}.sources.json",
        CERT_ROOT / f"{spec['document_id']}.json",
    )
    return "\n\n".join([intro, *sections, role_focus, lineage, cert_note]).rstrip() + "\n"


def _profile_doc(
    *,
    title: str,
    version: str,
    classification: str,
    audience: str,
    owner: str,
    purpose: str,
    source_paths: list[Path],
    sections: list[str],
    minimum_words: int,
) -> str:
    source_manifest = LINEAGE_ROOT / f"{title.replace(' ', '_')}.sources.json"
    certificate = CERT_ROOT / f"{title.replace(' ', '_')}.json"
    intro = block(
        f"""
        # {title}

        ## Version {version}

        **Status:** Official role-specific manual

        **Audience:** {audience}

        **Owner:** {owner}

        **Purpose:** {purpose}

        **Authority boundary:** This manual explains governed operations. It does not replace constitutional truth, legal review, production incident authority, or the full reference manual.

        ## Document Control

        {table_header()}
        | Document ID | {title.replace(' ', '_')} |
        | Version | {version} |
        | Classification | {classification} |
        | Owner | {owner} |
        | Minimum Words | {minimum_words} |
        | Source Count | {len(source_paths)} |
        | Source Manifest | `{rel(source_manifest)}` |
        | Certificate | `{rel(certificate)}` |
        """
    )
    lineage = source_table(source_paths)
    cert_note = short_lineage_note(source_manifest, certificate)
    body = "\n\n".join([intro, *sections, lineage, cert_note])
    return body.rstrip() + "\n"


@dataclass(frozen=True)
class PublishedDocument:
    document_id: str
    profile: str
    title: str
    owner: str
    classification: str
    status: str
    output_path: Path
    source_manifest_path: Path
    certificate_path: Path
    minimum_words: int


PROFILE_DEFINITIONS: list[dict[str, object]] = [
    {
        "document_id": "NOVATECH-FULL-REFERENCE-V2",
        "profile": "full_reference",
        "title": "NOVATECH PLATFORM ADMINISTRATOR & STAFF MANUAL",
        "owner": "NovaTech Platform Operations",
        "classification": "GENERATED_FULL_REFERENCE",
        "status": "ACTIVE",
        "output_path": GOVERNANCE_ROOT / "NOVATECH_PLATFORM_ADMINISTRATOR_AND_STAFF_MANUAL_V2.md",
        "source_paths": tuple(),
        "minimum_words": 100000,
    },
    {
        "document_id": "NOVATECH-EXECUTIVE-MANUAL-V1",
        "profile": "executive",
        "title": "NOVATECH EXECUTIVE MANUAL",
        "owner": "NovaTech Platform Leadership",
        "classification": "GENERATED_ROLE_MANUAL",
        "status": "ACTIVE",
        "output_path": GOVERNANCE_ROOT / "NOVATECH_EXECUTIVE_MANUAL.md",
        "source_paths": (
            GOVERNANCE_ROOT / "NOVASCRIPT_GOVERNANCE_HANDBOOK.md",
            DOCS_ROOT / "roadmap/AfriTech_Operational_Civilization_Platform_Master_Plan.md",
            DOCS_ROOT / "strategy/AFRITECH_ENTERPRISE_READINESS_REVIEW.md",
            DOCS_ROOT / "strategy/AFRITECH_MONETIZATION_AND_ECOSYSTEM_EXPANSION_BLUEPRINT.md",
        ),
        "minimum_words": 3000,
    },
    {
        "document_id": "NOVATECH-OPERATOR-MANUAL-V1",
        "profile": "operator",
        "title": "NOVATECH OPERATOR MANUAL",
        "owner": "NovaTech Operations",
        "classification": "GENERATED_ROLE_MANUAL",
        "status": "ACTIVE",
        "output_path": GOVERNANCE_ROOT / "NOVATECH_OPERATOR_MANUAL.md",
        "source_paths": (
            DOCS_ROOT / "operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md",
            DOCS_ROOT / "operations/AFRITECH_OPERATOR_DECISION_PROTOCOL.md",
            DOCS_ROOT / "operations/AfriRide_Operability_Playbook.md",
            DOCS_ROOT / "operations/AfriRide_First_10_Rides_Runbook.md",
        ),
        "minimum_words": 2800,
    },
    {
        "document_id": "NOVATECH-AUDITOR-MANUAL-V1",
        "profile": "auditor",
        "title": "NOVATECH AUDITOR MANUAL",
        "owner": "NovaTech Trust and Audit",
        "classification": "GENERATED_ROLE_MANUAL",
        "status": "ACTIVE",
        "output_path": GOVERNANCE_ROOT / "NOVATECH_AUDITOR_MANUAL.md",
        "source_paths": (
            GOVERNANCE_ROOT / "NOVASCRIPT_GOVERNANCE_HANDBOOK.md",
            DOCS_ROOT / "standards/AFRICPPT_PROTOCOL_SPEC.md",
            DOCS_ROOT / "standards/AFRIRIDE_TRUST_PROTOCOL_SPEC.md",
            DOCS_ROOT / "operations/AFRITECH_PRODUCTION_TRUST_NODE_RUNBOOK.md",
            DOCS_ROOT / "operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md",
        ),
        "minimum_words": 2600,
    },
    {
        "document_id": "NOVATECH-DEVELOPER-MANUAL-V1",
        "profile": "developer",
        "title": "NOVATECH DEVELOPER MANUAL",
        "owner": "NovaTech Engineering",
        "classification": "GENERATED_ROLE_MANUAL",
        "status": "ACTIVE",
        "output_path": GOVERNANCE_ROOT / "NOVATECH_DEVELOPER_MANUAL.md",
        "source_paths": (
            DOCS_ROOT / "api/AFRIRIDE_NEXT_GEN_MOBILE_API_CONTRACT.md",
            DOCS_ROOT / "mobile/AFRIRIDE_MOBILE_UX_POLISH_GUIDE.md",
            DOCS_ROOT / "operations/AFRITECH_PILOT_EXECUTION_PACK.md",
            DOCS_ROOT / "operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md",
        ),
        "minimum_words": 2600,
    },
    {
        "document_id": "NOVATECH-PARTNER-MANUAL-V1",
        "profile": "partner",
        "title": "NOVATECH PARTNER MANUAL",
        "owner": "NovaTech Platform Partnerships",
        "classification": "GENERATED_ROLE_MANUAL",
        "status": "ACTIVE",
        "output_path": GOVERNANCE_ROOT / "NOVATECH_PARTNER_MANUAL.md",
        "source_paths": (
            DOCS_ROOT / "partners/AFRIRIDE_PARTNER_ONBOARDING_PLAYBOOK.md",
            DOCS_ROOT / "operations/AfriRide_Operability_Playbook.md",
            DOCS_ROOT / "standards/AFRIRIDE_TRUST_PROTOCOL_SPEC.md",
            DOCS_ROOT / "operations/AFRITECH_STAGING_DEPLOYMENT_AND_PARTNER_DEMO_RUNBOOK.md",
        ),
        "minimum_words": 2200,
    },
    {
        "document_id": "NOVATECH-INVESTOR-MANUAL-V1",
        "profile": "investor",
        "title": "NOVATECH INVESTOR MANUAL",
        "owner": "NovaTech Strategy",
        "classification": "GENERATED_ROLE_MANUAL",
        "status": "ACTIVE",
        "output_path": GOVERNANCE_ROOT / "NOVATECH_INVESTOR_MANUAL.md",
        "source_paths": (
            DOCS_ROOT / "strategy/AFRITECH_ENTERPRISE_READINESS_REVIEW.md",
            DOCS_ROOT / "strategy/AFRITECH_MONETIZATION_AND_ECOSYSTEM_EXPANSION_BLUEPRINT.md",
            DOCS_ROOT / "roadmap/AfriTech_Operational_Civilization_Platform_Master_Plan.md",
            DOCS_ROOT / "vision/Nova_Ecosystem_Naming_Strategy.md",
        ),
        "minimum_words": 2200,
    },
]


def build_full_reference_source_paths() -> list[Path]:
    paths = discovered_governed_sources()
    extra = [
        GOV_SOURCE
        for GOV_SOURCE in [
            DOCS_ROOT / "governance/NOVASCRIPT_GOVERNANCE_HANDBOOK.md",
            DOCS_ROOT / "operations/AfriRide_Operability_Playbook.md",
            DOCS_ROOT / "operations/AfriRide_City_Level_Pilot_Deployment_Playbook.md",
            DOCS_ROOT / "operations/AfriRide_First_10_Rides_Runbook.md",
            DOCS_ROOT / "operations/AfriRide_Week_1_4_Launch_Execution_Plan.md",
            DOCS_ROOT / "operations/AFRITECH_PILOT_EXECUTION_PACK.md",
            DOCS_ROOT / "operations/AFRITECH_LIVE_PILOT_EXECUTION_CHECKLIST.md",
            DOCS_ROOT / "operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md",
            DOCS_ROOT / "operations/AFRITECH_PRODUCTION_TRUST_NODE_RUNBOOK.md",
            DOCS_ROOT / "operations/AFRITECH_OPERATOR_DECISION_PROTOCOL.md",
            DOCS_ROOT / "operations/AFRITECH_STAGING_DEPLOYMENT_AND_PARTNER_DEMO_RUNBOOK.md",
            DOCS_ROOT / "pilot/AFRIRIDE_REAL_WORLD_ACTIVATION_PLAYBOOK.md",
            DOCS_ROOT / "pilot/AFRIRIDE_PHASE1_SETUP_RUNBOOK.md",
            DOCS_ROOT / "pilot/AFRIRIDE_POSTGRES_CUTOVER_RUNBOOK.md",
            DOCS_ROOT / "pilot/AFRIRIDE_MULTI_NODE_PRODUCTION_PILOT_PREP.md",
            DOCS_ROOT / "pilot/AFRIRIDE_MELBOURNE_FIRST_REAL_PILOT_LAUNCH_PLAN.md",
            DOCS_ROOT / "proof/AFRIRIDE_CONTROLLED_PILOT_RUNBOOK.md",
            DOCS_ROOT / "proof/AFRIRIDE_CONTROLLED_PILOT_EVIDENCE_AUTOMATION.md",
            DOCS_ROOT / "proof/AFRIRIDE_CONTROLLED_PILOT_SCENARIO_MATRIX.md",
            DOCS_ROOT / "proof/AFRIRIDE_TRUST_PROTOCOL_SPEC.md",
            DOCS_ROOT / "partners/AFRIRIDE_PARTNER_ONBOARDING_PLAYBOOK.md",
            DOCS_ROOT / "roadmap/AfriTech_Operational_Civilization_Platform_Master_Plan.md",
            DOCS_ROOT / "strategy/AFRITECH_MONETIZATION_AND_ECOSYSTEM_EXPANSION_BLUEPRINT.md",
            DOCS_ROOT / "strategy/AFRITECH_ENTERPRISE_READINESS_REVIEW.md",
            DOCS_ROOT / "whitepaper/AFRIRIDE_PARTNER_ARCHITECTURE_WHITEPAPER.md",
            DOCS_ROOT / "vision/Nova_Ecosystem_Naming_Strategy.md",
            DOCS_ROOT / "vision/AfriRide_GA_Elite_MVP.md",
            DOCS_ROOT / "business/AFRIRIDE_PRICING_AND_PACKAGING_REFINEMENT.md",
            DOCS_ROOT / "standards/AFRICPPT_PROTOCOL_SPEC.md",
            DOCS_ROOT / "standards/AFRIRIDE_TRUST_PROTOCOL_SPEC.md",
            DOCS_ROOT / "adoption/NOVASCRIPT_ADOPTION_GUIDE.md",
            DOCS_ROOT / "mobile/AFRIRIDE_MOBILE_UX_POLISH_GUIDE.md",
            DOCS_ROOT / "api/AFRIRIDE_NEXT_GEN_MOBILE_API_CONTRACT.md",
        ]
        if GOV_SOURCE.exists()
    ]
    unique = []
    seen = set()
    for path in [*paths, *extra]:
        if path in seen or not path.exists():
            continue
        seen.add(path)
        unique.append(path)
    return unique


def _profile_sources_and_content(profile: str) -> tuple[list[Path], str, dict[str, str]]:
    spec = next(item for item in PROFILE_DEFINITIONS if item["profile"] == profile)
    sources = list(spec["source_paths"]) if spec["source_paths"] else build_full_reference_source_paths()
    source_manifest = LINEAGE_ROOT / f"{spec['document_id']}.sources.json"
    certificate = CERT_ROOT / f"{spec['document_id']}.json"
    if profile == "full_reference":
        content = ""
    else:  # pragma: no cover
        content = compose_profile_from_reference(
            profile=profile,
            full_reference_path=GOVERNANCE_ROOT / "NOVATECH_PLATFORM_ADMINISTRATOR_AND_STAFF_MANUAL_V2.md",
            source_paths=sources,
        )
    return sources, content, {"source_manifest": rel(source_manifest), "certificate": rel(certificate)}


def build_documentation_compliance_registry(
    *,
    registry_entries: list[dict[str, object]],
    full_reference_path: Path,
) -> dict[str, Any]:
    source_documents = _sources_source_docs(
        [
            full_reference_path,
            DOCS_ROOT / "governance/NOVASCRIPT_GOVERNANCE_HANDBOOK.md",
            DOCS_ROOT / "certification/NOVATECH_DOCUMENTATION_CERTIFICATION_PROGRAM.md",
            DOCS_ROOT / "certification/NOVASCRIPT_CERTIFICATION_PROGRAM.md",
            DOCS_ROOT / "strategy/NOVATECH_DOCUMENTATION_COMPLIANCE_AND_MARKETPLACE_STRATEGY.md",
            DOCS_ROOT / "standards/AFRICPPT_PROTOCOL_SPEC.md",
            DOCS_ROOT / "standards/AFRIRIDE_TRUST_PROTOCOL_SPEC.md",
            DOCS_ROOT / "operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md",
            DOCS_ROOT / "operations/AFRITECH_OPERATOR_DECISION_PROTOCOL.md",
        ]
    )
    return {
        "registry_id": "NOVATECH_DOCUMENTATION_COMPLIANCE_REGISTRY_V1",
        "status": "ACTIVE",
        "validator_version": VALIDATOR_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "DOCUMENTATION_COMPLIANCE_PRODUCT",
        "positioning": {
            "certification_layer": "ISO-style certification layer",
            "government_compliance": "Government compliance positioning",
            "monetization": "Trust-as-a-service",
            "marketplace": "Global partner marketplace",
        },
        "standard_protocol": {
            "name": "AfriCPPT",
            "expansion": "Global standard protocol for proof, compliance, and trust portability",
            "publication_surface": "/v1/novatech/documentation/standard",
        },
        "source_documents": source_documents,
        "linked_surfaces": {
            "document_registry": {
                "path": rel(REGISTRY_ROOT / "DOCUMENT_REGISTRY.yaml"),
                "document_count": len(registry_entries),
                "certificate_count": len(registry_entries),
                "lineage_root": rel(LINEAGE_ROOT),
                "certificate_root": rel(CERT_ROOT),
            },
            "organization_os": {
                "api_surface": "/v1/novatech/intranet/platform",
                "directory_surface": "/v1/novatech/organizations",
                "description": "Organization OS surfaces for tenant directory, internal operations, and governed workspace visibility.",
            },
            "tenant_governance": {
                "api_surface": "/v1/novatech/organizations/{organization_id}",
                "billing_surface": "/v1/novatech/organizations/{organization_id}/billing",
                "execution_surface": "/v1/novatech/organizations/{organization_id}/execution",
                "execution_activation_surface": "/v1/novatech/organizations/{organization_id}/execution/activation",
                "onboarding_surface": "/v1/novatech/organizations/onboard",
                "description": "Tenant governance surfaces for organization lifecycle, billing, and controlled execution readiness.",
            },
            "policy_registry": {
                "api_surface": "/v1/novatech/documentation/policy",
                "source_surface": "/v1/novaprogramming/policy",
                "description": "Policy registry and decision review for documentation governance.",
            },
            "certification_registry": {
                "api_surface": "/v1/novatech/documentation/certification",
                "issuance_surface": "/v1/novatech/documentation/certification/issue",
                "source_surface": "/v1/novaprogramming/certification",
                "description": "Certification registry and issuance for manuals and compliance packs.",
            },
            "certification_issuance": {
                "api_surface": "/v1/novatech/documentation/certification/issue",
                "registry_surface": "/v1/novatech/documentation/certification",
                "source_surface": "/v1/novaprogramming/certification",
                "description": "Certification issuance surface for document compliance certificates and public verification readiness.",
            },
            "trust_registry": {
                "api_surface": "/v1/novatech/documentation/trust",
                "source_surface": "/v1/novaprogramming/trust",
                "description": "Trust registry, risk, and verification surfaces for documentation artifacts.",
            },
            "operator_training_records": {
                "api_surface": "/v1/novatech/documentation/training",
                "storage_table": "operator_training_records",
                "description": "Training acknowledgements and completion records for manuals and staff.",
            },
            "continuous_assurance_reports": {
                "api_surface": "/v1/novatech/documentation/assurance",
                "report_surface": "/v1/novatech/documentation/assurance/report",
                "history_surface": "/v1/novatech/documentation/assurance/history",
                "description": "Continuous assurance status, history, and report generation surfaces.",
            },
            "public_verification_portal": {
                "portal_surface": "/public/verify/portal",
                "documentation_portal_surface": "/public/documentation/portal",
                "verification_surface": "/public/documentation/{organization_id}",
                "description": "Public verification portal surfaces for external documentation and trust review.",
            },
            "marketplace": {
                "api_surface": "/v1/novatech/documentation/marketplace",
                "onboarding_surface": "/v1/novatech/documentation/onboarding",
                "trust_marketplace_surface": "/v1/novatech/marketplace/status",
                "description": "Trust marketplace, partner onboarding, and certification service listing.",
            },
        },
        "product_categories": [
            "Document certification",
            "Organization OS",
            "Tenant governance",
            "Policy registry",
            "Trust registry",
            "Operator training records",
            "Continuous assurance reports",
            "Certification issuance",
            "Public verification portal",
            "Trust-as-a-service",
            "Marketplace onboarding",
        ],
        "marketplace_services": [
            "Verification Services",
            "Certification Services",
            "Replay Services",
            "Trust Services",
        ],
        "partner_onboarding_strategy": {
            "surface": "/v1/novatech/documentation/onboarding",
            "phases": [
                "verify the partner use case",
                "attach the partner to the registry and trust surfaces",
                "publish the role-specific manual set",
                "complete operator training and acknowledgement",
                "issue the first compliance and certification record",
                "list the partner in the trust marketplace",
                "continue assurance and renewal",
            ],
        },
        "assurance_model": {
            "status_surface": "/v1/novatech/documentation/assurance",
            "report_surface": "/v1/novatech/documentation/assurance/report",
            "history_surface": "/v1/novatech/documentation/assurance/history",
            "roles": ["operator", "trust", "finance", "developer", "partner", "investor"],
        },
    }


def write_documentation_compliance_registry(
    *,
    registry_entries: list[dict[str, object]],
    full_reference_path: Path,
) -> dict[str, Any]:
    compliance_registry = build_documentation_compliance_registry(
        registry_entries=registry_entries,
        full_reference_path=full_reference_path,
    )
    COMPLIANCE_REGISTRY_PATH.write_text(
        yaml.safe_dump(compliance_registry, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return compliance_registry


def load_documentation_compliance_registry() -> dict[str, Any]:
    if not COMPLIANCE_REGISTRY_PATH.exists():
        raise FileNotFoundError(COMPLIANCE_REGISTRY_PATH)
    return yaml.safe_load(COMPLIANCE_REGISTRY_PATH.read_text(encoding="utf-8"))


def write_role_documents(full_reference_path: Path) -> list[dict[str, object]]:
    ensure_dirs()
    registry_entries: list[dict[str, object]] = []
    for spec in PROFILE_DEFINITIONS:
        sources, content, _ = _profile_sources_and_content(str(spec["profile"]))
        output_path: Path = spec["output_path"]  # type: ignore[assignment]
        if spec["profile"] == "full_reference":
            output_path = full_reference_path
            content = full_reference_path.read_text(encoding="utf-8")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if spec["profile"] != "full_reference":
            output_path.write_text(content, encoding="utf-8")
        if spec["profile"] == "full_reference":
            # Ensure registry/certification still reflect the authoritative file.
            content = output_path.read_text(encoding="utf-8")
        source_manifest_path = LINEAGE_ROOT / f"{spec['document_id']}.sources.json"
        certificate_path = CERT_ROOT / f"{spec['document_id']}.json"
        lineage_payload = {
            "document_id": spec["document_id"],
            "profile": spec["profile"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_documents": _sources_source_docs(sources),
        }
        source_manifest_path.write_text(
            json.dumps(lineage_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        certificate_payload = {
            "document_id": spec["document_id"],
            "profile": spec["profile"],
            "title": spec["title"],
            "owner": spec["owner"],
            "classification": spec["classification"],
            "status": spec["status"],
            "document_hash": sha256_text(content),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_count": len(sources),
            "validator_version": VALIDATOR_VERSION,
            "source_manifest": rel(source_manifest_path),
        }
        certificate_path.write_text(
            json.dumps(certificate_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        registry_entries.append(
            {
                "id": spec["document_id"],
                "profile": spec["profile"],
                "title": spec["title"],
                "owner": spec["owner"],
                "classification": spec["classification"],
                "status": spec["status"],
                "output": rel(output_path),
                "source_manifest": rel(source_manifest_path),
                "certificate": rel(certificate_path),
                "minimum_words": spec["minimum_words"],
            }
        )
        if spec["profile"] == "full_reference":
            # Add certification note to the main file through a small footer appendix.
            # The main generator is responsible for the human-readable content;
            # certification remains external in the registry for stability.
            pass
    registry_path = REGISTRY_ROOT / "DOCUMENT_REGISTRY.yaml"
    registry = {
        "registry_id": "NOVATECH_DOCUMENT_REGISTRY_V1",
        "status": "ACTIVE",
        "validator_version": VALIDATOR_VERSION,
        "documents": registry_entries,
    }
    registry_path.write_text(
        yaml.safe_dump(registry, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    write_documentation_compliance_registry(
        registry_entries=registry_entries,
        full_reference_path=full_reference_path,
    )
    return registry_entries


def validate_document_system() -> list[str]:
    registry_path = REGISTRY_ROOT / "DOCUMENT_REGISTRY.yaml"
    if not registry_path.exists():
        raise FileNotFoundError(registry_path)
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    documents = registry.get("documents", [])
    failures: list[str] = []
    for item in documents:
        output = ROOT / item["output"]
        certificate = ROOT / item["certificate"]
        source_manifest = ROOT / item["source_manifest"]
        if not output.exists():
            failures.append(f"missing output: {output}")
            continue
        if not certificate.exists():
            failures.append(f"missing certificate: {certificate}")
            continue
        if not source_manifest.exists():
            failures.append(f"missing source manifest: {source_manifest}")
            continue
        cert = json.loads(certificate.read_text(encoding="utf-8"))
        manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
        output_hash = sha256_file(output)
        if cert["document_hash"] != output_hash:
            failures.append(f"hash mismatch: {item['id']}")
        if cert["source_count"] != len(manifest.get("source_documents", [])):
            failures.append(f"source count mismatch: {item['id']}")
        if output.read_text(encoding="utf-8").count("Document Lineage") == 0:
            failures.append(f"missing lineage section: {item['id']}")
        if output.read_text(encoding="utf-8").count("Authority boundary") == 0:
            failures.append(f"missing authority boundary: {item['id']}")
        word_count = len(output.read_text(encoding="utf-8").split())
        if word_count < int(item["minimum_words"]):
            failures.append(
                f"word count below minimum for {item['id']}: {word_count} < {item['minimum_words']}"
            )
    if not COMPLIANCE_REGISTRY_PATH.exists():
        failures.append(f"missing compliance registry: {COMPLIANCE_REGISTRY_PATH}")
    else:
        compliance = yaml.safe_load(COMPLIANCE_REGISTRY_PATH.read_text(encoding="utf-8")) or {}
        if compliance.get("registry_id") != "NOVATECH_DOCUMENTATION_COMPLIANCE_REGISTRY_V1":
            failures.append("invalid compliance registry id")
        if compliance.get("status") != "ACTIVE":
            failures.append("compliance registry is not active")
        linked_surfaces = compliance.get("linked_surfaces", {})
        document_registry = linked_surfaces.get("document_registry", {})
        if int(document_registry.get("document_count", -1)) != len(documents):
            failures.append("document registry count mismatch in compliance registry")
        standard_protocol = compliance.get("standard_protocol", {})
        if standard_protocol.get("name") != "AfriCPPT":
            failures.append("missing AfriCPPT standard protocol binding")
        for required in (
            "policy_registry",
            "certification_registry",
            "trust_registry",
            "operator_training_records",
            "continuous_assurance_reports",
            "organization_os",
            "tenant_governance",
            "certification_issuance",
            "public_verification_portal",
        ):
            if required not in linked_surfaces:
                failures.append(f"missing {required} binding in compliance registry")
    return failures
