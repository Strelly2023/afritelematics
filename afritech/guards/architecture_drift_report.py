"""Report structural drift against the unified AfriTech architecture."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from afritech.guards.document_registry_guard import validate as validate_document_registry


ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE_DOC = ROOT / "docs/architecture/AFRITECH_UNIFIED_ARCHITECTURE.md"
PROTOCOL_DOC = ROOT / "docs/standards/AFRICPPT_PROTOCOL_SPEC.md"
ONE_PAGER_DOC = ROOT / "docs/partners/AFRITECH_PARTNER_ARCHITECTURE_ONE_PAGER.md"
DOCUMENT_REGISTRY = ROOT / "afritech/governance/document_registry.yaml"

TRACKED_MODULES = {
    "afriride_system/api/auth.py",
    "afriride_system/api/compliance_middleware.py",
    "afriride_system/api/dispatcher_adapter.py",
    "afriride_system/api/driver_routes.py",
    "afriride_system/api/idempotency.py",
    "afriride_system/api/logging.py",
    "afriride_system/api/main.py",
    "afriride_system/api/passenger_routes.py",
    "afriride_system/api/responses.py",
    "afriride_system/api/ride_routes.py",
    "afriride_system/api/schemas.py",
    "afriride_system/api/system_routes.py",
    "afriride_system/api/trace_middleware.py",
    "afriride_system/backend/determinism.py",
    "afriride_system/backend/authority_runtime.py",
    "afriride_system/backend/event_ledger.py",
    "afriride_system/backend/event_signatures.py",
    "afriride_system/backend/evidence_engine.py",
    "afriride_system/backend/ledger_receipts.py",
    "afriride_system/backend/proof_material.py",
    "afriride_system/backend/receipt_engine.py",
    "afriride_system/backend/receipt_signing.py",
    "afriride_system/backend/replay_engine.py",
    "afriride_system/backend/state.py",
    "afriride_system/backend/storage.py",
    "afriride_system/backend/trace_enforcement.py",
    "afritech/api/afriride_driver_views.py",
    "afritech/api/afroprog_workspace_api.py",
    "afritech/api/alerts_views.py",
    "afritech/api/app.py",
    "afritech/api/architecture_proof_api.py",
    "afritech/api/auth.py",
    "afritech/api/auth_models.py",
    "afritech/api/cross_proof_views.py",
    "afritech/api/dashboard_gateway_api.py",
    "afritech/api/explain_execution_views.py",
    "afritech/api/governance_impact_views.py",
    "afritech/api/metrics_views.py",
    "afritech/api/ops_governance_api.py",
    "afritech/api/orchestration_views.py",
    "afritech/api/partner_registry_api.py",
    "afritech/api/partner_verification_api.py",
    "afritech/api/public_verification_api.py",
    "afritech/api/semantic_admission.py",
    "afritech/api/system_status.py",
    "afritech/api/trace_api.py",
    "afritech/api/trust_graph_views.py",
    "afritech/api/trust_kernel_views.py",
    "afritech/api/trust_network_api.py",
    "afritech/api/urls.py",
    "afritech/api/verification_views.py",
    "afritech/crypto/anchor_batching.py",
    "afritech/crypto/anchor_publication.py",
    "afritech/crypto/external_anchor.py",
    "afritech/crypto/key_manager.py",
    "afritech/crypto/key_registry.py",
    "afritech/crypto/merkle.py",
    "afritech/crypto/multi_party_verification.py",
    "afritech/crypto/public_chain_anchor.py",
    "afritech/crypto/signature.py",
    "afritech/crypto/signature_utils.py",
    "afritech/crypto/zk_anchor_attestation.py",
    "dashboard/src/App.jsx",
    "dashboard/src/main.jsx",
    "dashboard/src/styles.css",
}

TRACKED_DIRECTORIES = (
    "afriride_system/api",
    "afriride_system/backend",
    "afritech/api",
    "afritech/crypto",
    "dashboard/src",
)

ARCHITECTURE_COMPONENTS = {
    "Trust Explorer and Operator Web UI": {
        "terms": ("Trust Explorer", "Operator Web UI"),
        "evidence": ("dashboard/src/App.jsx",),
    },
    "Execution surfaces and ingress": {
        "terms": (
            "Rider App",
            "Driver App",
            "Shared Mobile Client",
            "AfriRide API",
            "Event Gateway",
        ),
        "evidence": (
            "afriride_system/api/main.py",
            "afriride_system/api/auth.py",
            "afriride_system/api/passenger_routes.py",
            "afriride_system/api/driver_routes.py",
            "afriride_system/backend/api_gateway/gateway.py",
        ),
    },
    "Truth core": {
        "terms": (
            "TRACE LAYER",
            "Replay Engine",
            "Evidence Engine",
            "Receipt Engine",
            "Crypto Layer",
        ),
        "evidence": (
            "afriride_system/backend/trace_enforcement.py",
            "afriride_system/backend/replay_engine.py",
            "afriride_system/backend/evidence_engine.py",
            "afriride_system/backend/receipt_engine.py",
            "afritech/crypto/external_anchor.py",
        ),
    },
    "AFRIPower": {
        "terms": ("AFRIPower",),
        "evidence": ("afritech/afripower",),
    },
    "AfriProgramming": {
        "terms": ("AfriProgramming",),
        "evidence": ("afritech/afriprogramming",),
    },
    "AfriCPPT": {
        "terms": (
            "AfriCPPT",
            "external verification APIs",
            "SDK / integration adapters",
        ),
        "evidence": (
            "afritech/api/partner_verification_api.py",
            "afritech/api/trust_network_api.py",
            "afritech/sdk/partner_verification.py",
            "docs/standards/AFRICPPT_PROTOCOL_SPEC.md",
        ),
    },
    "AFrTPPS": {
        "terms": (
            "AFrTPPS",
            "onboarding models",
            "pilot execution playbooks",
            "performance measurement (KPIs)",
        ),
        "evidence": (
            "afritech/docs/operations/afriride_city_pilot_playbook.md",
            "afritech/docs/operations/afriride_readiness_classification.md",
            "docs/partners/AFRIRIDE_PARTNER_ONBOARDING_PLAYBOOK.md",
        ),
    },
    "Governance": {
        "terms": ("ADR", "INVARIANT", "BIND", "RULE", "GUARD", "CI"),
        "evidence": (
            "afritech/governance/adr/register.yaml",
            "afritech/governance/bindings/BIND-001-phase1-phase2.yaml",
            "afritech/governance/rules/RULE-001-phase1-runbook.yaml",
            "afritech/guards/guard_phase1_runbook.py",
        ),
    },
}

REQUIRED_FLOWS = {
    "Execution to proof": {
        "terms": ("REAL-WORLD ACTION", "-> EXECUTION", "-> TRACE", "-> REPLAY", "-> EVIDENCE", "-> RECEIPT"),
        "evidence": (
            "afriride_system/api/main.py",
            "afriride_system/backend/replay_engine.py",
            "afriride_system/backend/evidence_engine.py",
            "afriride_system/backend/receipt_engine.py",
        ),
    },
    "Governed evolution": {
        "terms": ("-> INSIGHT", "-> PROPOSAL", "-> GOVERNED EVOLUTION"),
        "evidence": (
            "afritech/governance/binding_manifest.yaml",
            "afritech/guards/guard_registry.yaml",
            "afritech/afriprogramming",
        ),
    },
    "External verification": {
        "terms": ("-> EXTERNAL VERIFICATION", "AfriCPPT external verification"),
        "evidence": (
            "afritech/api/partner_verification_api.py",
            "afritech/api/trust_network_api.py",
            "docs/standards/AFRICPPT_PROTOCOL_SPEC.md",
        ),
    },
}


@dataclass(frozen=True)
class ArchitectureDriftReport:
    architecture_doc: str
    protocol_doc: str
    one_pager_doc: str
    document_registry: str
    tracked_module_count: int
    authority_binding_verified: bool
    undocumented_modules: tuple[str, ...]
    orphan_components: tuple[str, ...]
    undocumented_flows: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return not (
            self.undocumented_modules
            or self.orphan_components
            or self.undocumented_flows
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["clean"] = self.clean
        return payload


def validate() -> ArchitectureDriftReport:
    architecture_text = _read_text(ARCHITECTURE_DOC)
    _read_text(PROTOCOL_DOC)
    _read_text(ONE_PAGER_DOC)
    authority_report = validate_document_registry()

    undocumented_modules = tuple(_scan_for_undocumented_modules())
    orphan_components = tuple(_scan_for_orphan_components(architecture_text))
    undocumented_flows = tuple(_scan_for_undocumented_flows(architecture_text))

    return ArchitectureDriftReport(
        architecture_doc="docs/architecture/AFRITECH_UNIFIED_ARCHITECTURE.md",
        protocol_doc="docs/standards/AFRICPPT_PROTOCOL_SPEC.md",
        one_pager_doc="docs/partners/AFRITECH_PARTNER_ARCHITECTURE_ONE_PAGER.md",
        document_registry="afritech/governance/document_registry.yaml",
        tracked_module_count=len(TRACKED_MODULES),
        authority_binding_verified=authority_report.clean,
        undocumented_modules=undocumented_modules,
        orphan_components=orphan_components,
        undocumented_flows=undocumented_flows,
    )


def _scan_for_undocumented_modules() -> list[str]:
    unexpected: list[str] = []
    for directory in TRACKED_DIRECTORIES:
        root = ROOT / directory
        for path in sorted(root.iterdir()):
            if not path.is_file():
                continue
            if path.name == "__init__.py":
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel not in TRACKED_MODULES:
                unexpected.append(rel)
    return unexpected


def _scan_for_orphan_components(architecture_text: str) -> list[str]:
    findings: list[str] = []
    lowered = architecture_text.lower()
    for component, rules in ARCHITECTURE_COMPONENTS.items():
        terms = tuple(term.lower() for term in rules["terms"])
        evidence = tuple(ROOT / str(path) for path in rules["evidence"])
        if not all(term in lowered for term in terms):
            findings.append(f"{component}: missing architecture declaration")
            continue
        if not any(path.exists() for path in evidence):
            findings.append(f"{component}: missing implementation evidence")
    return findings


def _scan_for_undocumented_flows(architecture_text: str) -> list[str]:
    findings: list[str] = []
    for flow_name, rules in REQUIRED_FLOWS.items():
        if not all(term in architecture_text for term in rules["terms"]):
            findings.append(f"{flow_name}: missing architecture flow declaration")
            continue
        evidence = tuple(ROOT / str(path) for path in rules["evidence"])
        if not all(path.exists() for path in evidence):
            findings.append(f"{flow_name}: missing flow evidence path")
    return findings


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def main() -> int:
    report = validate()
    status = "CLEAN" if report.clean else "DRIFT"
    print(f"ARCHITECTURE_DRIFT_REPORT: {status}")
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
