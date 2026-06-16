"""Governed AfriTech feature evidence registry.

The registry is static and side-effect free. It can be imported by dashboards,
CLIs, API routers, and CI validators without activating runtime or pilot
behavior.
"""

from __future__ import annotations

import json
import hashlib
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from afritech.security.signing import public_key_hex, sign_registry, signer_id


TechnicalStatus = Literal[
    "IMPLEMENTED",
    "PARTIAL",
    "PLANNED",
]

ActivationStatus = Literal[
    "GATED",
    "CONTROLLED_PILOT_READY",
    "PRODUCTION_READY",
]

EvidenceKind = Literal[
    "implementation",
    "test",
    "replay",
    "proof",
    "boundary_guard",
]


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_CLASSIFICATION = "GOVERNED_EVIDENCE_VALIDATED_FEATURE_REGISTRY"
REGISTRY_STATUS = "FEATURE_REGISTRY_LEVEL_12"
REGISTRY_GENERATION_MODE = "REPLAY_DERIVED_EVIDENCE_PROJECTION"
SNAPSHOT_SCHEMA = "afritech.feature_registry_snapshot.v1"
REQUIRED_PROOF_KEYS = {
    "classification",
    "authority_source",
}
TRUSTED_AUTHORITIES = {
    "AfriTech Constitution",
    "AfriTech Governance",
    "AfriTech Replay",
    "AfriTech Proof",
    "AfriTech CI",
}
ALLOWED_PROOF_CLASSES = {
    "CONTROLLED_PILOT_READY_SYSTEM",
    "GOVERNED_EVIDENCE_VALIDATED_FEATURE_REGISTRY",
    "REPLAY_DERIVED_FEATURE_REGISTRY",
    "CONSTITUTIONAL_EVIDENCE_SYSTEM",
}


SYSTEM_STATUS = {
    "classification": "CONTROLLED_PILOT_READY_SYSTEM",
    "feature_registry_classification": REGISTRY_CLASSIFICATION,
    "feature_registry_status": REGISTRY_STATUS,
    "live_pilot_authorized": False,
    "production_proven": False,
    "economic_activation_allowed": False,
}


@dataclass(frozen=True)
class EvidenceRef:
    kind: EvidenceKind
    path: str
    required: bool = True

    def canonical_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FeatureEvidence:
    """Implementation, validation, and boundary links for a feature claim."""

    id: str
    name: str
    description: str
    technical_status: TechnicalStatus
    activation_status: ActivationStatus
    evidence: tuple[EvidenceRef, ...]
    boundary: str
    boundary_guard: str
    version: str
    last_updated: str
    dependencies: tuple[str, ...] = ()

    @property
    def feature_id(self) -> str:
        """Backward-compatible alias for earlier registry consumers."""
        return self.id

    @property
    def use(self) -> str:
        """Backward-compatible alias for the previous summary field."""
        return self.description

    @property
    def status(self) -> str:
        """Backward-compatible activation-oriented status string."""
        if self.activation_status != "GATED":
            return self.activation_status
        return self.technical_status

    def canonical_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["feature_id"] = self.id
        payload["use"] = self.description
        payload["status"] = self.status
        payload["evidence_complete"] = evidence_complete(self)
        payload["validation"] = feature_validation_summary(self)
        return payload


@dataclass(frozen=True)
class EvidenceArtifact:
    id: str
    type: EvidenceKind
    path: str
    hash: str
    size_bytes: int
    required: bool
    origin_event: str
    timestamp: str

    def canonical_dict(self) -> dict[str, object]:
        return asdict(self)


def ref(kind: EvidenceKind, path: str, required: bool = True) -> EvidenceRef:
    return EvidenceRef(kind=kind, path=path, required=required)


FEATURE_CANDIDATES: tuple[FeatureEvidence, ...] = (
    FeatureEvidence(
        id="trust-kernel",
        name="Trust Kernel",
        description="Anchors events, evidence bundles, replay verification, and state truth.",
        technical_status="IMPLEMENTED",
        activation_status="GATED",
        evidence=(
            ref("implementation", "afritech/core/runtime/admission/admission_engine.py"),
            ref("implementation", "afritech/api/trust_kernel_views.py"),
            ref("implementation", "afritech/trust_network.py"),
            ref("test", "afritech/tests/distributed/test_sovereign_ledger_protocol.py"),
            ref("test", "afritech/tests/crypto/test_blockchain_anchor.py"),
            ref("replay", "reports/continuity_proof_v1/recovery_equivalence.json"),
            ref("proof", "docs/trust/trust_model.md"),
            ref("boundary_guard", "afritech/ci/trust_lock_validator.py"),
        ),
        boundary="Truth authority remains replay and proof evidence, not dashboard presentation.",
        boundary_guard="afritech/ci/trust_lock_validator.py",
        version="v1",
        last_updated="2026-06-16",
    ),
    FeatureEvidence(
        id="afritpps-execution",
        name="AfriTPPS Execution",
        description="Executes domain operations through governed contracts.",
        technical_status="IMPLEMENTED",
        activation_status="GATED",
        evidence=(
            ref("implementation", "afritech/afritpps/execution_engine.py"),
            ref("implementation", "afritech/afritpps/domain_contracts.py"),
            ref("implementation", "afritech/afritpps/services.py"),
            ref("test", "afritech/tests/distributed/test_docs_and_tools_suite.py"),
            ref("replay", "reports/continuity_proof_v1/continuity_equivalence.json"),
            ref("proof", "docs/standards/AFRICPPT_PROTOCOL_SPEC.md"),
            ref("boundary_guard", "afritech/ci/afritpps_execution_validator.py"),
        ),
        boundary="Execution is admissibility-gated and must not bypass declared contracts.",
        boundary_guard="afritech/ci/afritpps_execution_validator.py",
        version="v1",
        last_updated="2026-06-16",
    ),
    FeatureEvidence(
        id="cross-domain-orchestration",
        name="Cross-Domain Orchestration",
        description="Coordinates verified operations across multiple AfriTech domains.",
        technical_status="IMPLEMENTED",
        activation_status="GATED",
        evidence=(
            ref("implementation", "afritech/api/orchestration_views.py"),
            ref("implementation", "afritech/afritpps/orchestration.py"),
            ref("implementation", "afritech/api/cross_proof_views.py"),
            ref("test", "mutants/tests/integration/test_cross_system_proof.py"),
            ref("replay", "reports/continuity_proof_v1/offline_merge.json"),
            ref("proof", "docs/api/state_service_api.md"),
            ref("boundary_guard", "afritech/ci/execution_integrity_validator.py"),
        ),
        boundary="Cross-system views expose evidence; they do not merge authority between domains.",
        boundary_guard="afritech/ci/execution_integrity_validator.py",
        version="v1",
        last_updated="2026-06-16",
        dependencies=("trust-kernel", "afritpps-execution"),
    ),
    FeatureEvidence(
        id="federation",
        name="Federation",
        description="Supports signed node communication and independent verification.",
        technical_status="IMPLEMENTED",
        activation_status="GATED",
        evidence=(
            ref("implementation", "afritech/network/node_api.py"),
            ref("implementation", "afritech/trust_network.py"),
            ref("implementation", "afritech/tools/partner_verification_session_cli.py"),
            ref("test", "afritech/tests/distributed/test_activation_scale_and_services.py"),
            ref("test", "afritech/tests/distributed/test_protocol_hardening_and_adversarial.py"),
            ref("replay", "reports/chaos_proof_v1/stability_equivalence.json"),
            ref("proof", "docs/partners/AFRITECH_FIRST_EXTERNAL_PARTNER_VERIFICATION_SESSION.md"),
            ref("boundary_guard", "afritech/ci/network_determinism_validator.py"),
        ),
        boundary="Federated peers may verify independently but cannot declare production activation.",
        boundary_guard="afritech/ci/network_determinism_validator.py",
        version="v1",
        last_updated="2026-06-16",
        dependencies=("trust-kernel",),
    ),
    FeatureEvidence(
        id="resilience-hardening",
        name="Resilience Hardening",
        description="Handles consensus failure, malicious nodes, replay divergence, and isolation.",
        technical_status="IMPLEMENTED",
        activation_status="GATED",
        evidence=(
            ref("implementation", "afritech/simulation/scale/load_generator.py"),
            ref("implementation", "afritech/runtime/replay/replay_engine.py"),
            ref("implementation", "afriride/field_validation/sync_replayer.py"),
            ref("test", "afritech/tests/distributed/test_protocol_hardening_and_adversarial.py"),
            ref("test", "afritech/tests/adversarial/test_adversarial_integrity_gate7.py"),
            ref("replay", "reports/chaos_proof_v1/drift_analysis.json"),
            ref("replay", "reports/adversarial_integrity_proof_v1/adversarial_integrity_equivalence.json"),
            ref("proof", "docs/trust/trust_model.md"),
            ref("boundary_guard", "afritech/ci/resilience_hardening_validator.py"),
        ),
        boundary="Recovery and hardening artifacts are evidence-backed; they are not live pilot authorization.",
        boundary_guard="afritech/ci/resilience_hardening_validator.py",
        version="v1",
        last_updated="2026-06-16",
        dependencies=("trust-kernel", "federation"),
    ),
    FeatureEvidence(
        id="afripower-intelligence",
        name="AfriPower Intelligence",
        description="Provides advisory-only prediction, risk scoring, and anomaly suggestions.",
        technical_status="IMPLEMENTED",
        activation_status="GATED",
        evidence=(
            ref("implementation", "afritech/afripower/predictive_orchestration.py"),
            ref("implementation", "afritech/afripower/resilience_intelligence.py"),
            ref("implementation", "afritech/ci/afripower_intelligence_validator.py"),
            ref("test", "afritech/tests/afripower/test_predictive_orchestration.py"),
            ref("test", "afritech/tests/afripower/test_resilience_intelligence.py"),
            ref("test", "afritech/tests/afripower/test_validator.py"),
            ref("replay", "reports/entropy_proof_v1/replay_equivalence_report.json"),
            ref("proof", "afritech/afripower/constants.py"),
            ref("boundary_guard", "afritech/ci/afripower_intelligence_validator.py"),
        ),
        boundary="Intelligence may recommend or explain only; it cannot mutate truth or governance.",
        boundary_guard="afritech/ci/afripower_intelligence_validator.py",
        version="v1",
        last_updated="2026-06-16",
        dependencies=("trust-kernel",),
    ),
    FeatureEvidence(
        id="governance-chain",
        name="Governance Chain",
        description="Enforces ADR -> INVARIANT -> BINDING -> RULE -> GUARD -> CI integrity.",
        technical_status="IMPLEMENTED",
        activation_status="GATED",
        evidence=(
            ref("implementation", "afritech/governance/binding_validator.py"),
            ref("implementation", "afritech/governance/document_registry.yaml"),
            ref("implementation", "afritech/ci/CI_AUTHORITY.yaml"),
            ref("test", "afritech/tests/governance/test_document_registry_guard.py"),
            ref("test", "afritech/tests/governance/test_authority_compression.py"),
            ref("replay", "reports/continuity_proof_v1/gap_detection.json"),
            ref("proof", "docs/reviews/AFRITECH_DOCUMENTATION_AUTHORITY_AUDIT.md"),
            ref("boundary_guard", "afritech/ci/binding_completeness_validator.py"),
        ),
        boundary="Governance validates declared authority; it does not create runtime authority by wording.",
        boundary_guard="afritech/ci/binding_completeness_validator.py",
        version="v1",
        last_updated="2026-06-16",
        dependencies=("trust-kernel",),
    ),
    FeatureEvidence(
        id="classification-ci",
        name="Classification CI",
        description="Blocks false production, live deployment, and economic maturity claims.",
        technical_status="IMPLEMENTED",
        activation_status="GATED",
        evidence=(
            ref("implementation", "afritech/ci/afriprogramming_engineering_validator.py"),
            ref("implementation", "afritech/ci/afriride_pilot_execution_checklist_validator.py"),
            ref("implementation", "afritech/certification/production_readiness_certificate.py"),
            ref("test", "afritech/tests/governance/test_afriride_test_status_assessment_doc.py"),
            ref("test", "afritech/tests/governance/test_pilot_operational_readiness.py"),
            ref("replay", "reports/afriride_live_pilot_protocol_v1/live_pilot_protocol.json"),
            ref("proof", "docs/STATUS_CONVENTIONS.md"),
            ref("boundary_guard", "afritech/ci/production_readiness_certificate_validator.py"),
        ),
        boundary="Classification blocks overclaiming; controlled readiness is not production proof.",
        boundary_guard="afritech/ci/production_readiness_certificate_validator.py",
        version="v1",
        last_updated="2026-06-16",
        dependencies=("governance-chain",),
    ),
    FeatureEvidence(
        id="pilot-gates",
        name="Pilot Gates",
        description="Keeps AfriRide pilot execution evidence-gated and controlled.",
        technical_status="IMPLEMENTED",
        activation_status="CONTROLLED_PILOT_READY",
        evidence=(
            ref("implementation", "afriride/field_validation/live_pilot_protocol.py"),
            ref("implementation", "afriride/field_validation/day_one_runbook.py"),
            ref("implementation", "afritech/certification/afriride_phase5_readiness_certificate.py"),
            ref("test", "afritech/tests/governance/test_pilot_operational_readiness.py"),
            ref("replay", "traces/pilot_runs/day_one_003/replay_verification_result.json"),
            ref("replay", "reports/afriride_live_pilot_protocol_v1/live_pilot_protocol.json"),
            ref("proof", "docs/pilot/AFRIRIDE_PILOT_ACTIVATION_CHECKLIST.md"),
            ref("boundary_guard", "afritech/ci/afriride_pilot_execution_checklist_validator.py"),
        ),
        boundary="Live riders, production field execution, and economic activation remain unauthorized.",
        boundary_guard="afritech/ci/afriride_pilot_execution_checklist_validator.py",
        version="v1",
        last_updated="2026-06-16",
        dependencies=("classification-ci", "resilience-hardening"),
    ),
    FeatureEvidence(
        id="driver-identity-proof",
        name="Driver Identity Proof",
        description="Exports signed driver identity and event-origin verification as a public trust feature.",
        technical_status="IMPLEMENTED",
        activation_status="PRODUCTION_READY",
        evidence=(
            ref("implementation", "afriride_system/backend/event_signatures.py"),
            ref("implementation", "afritech/identity/mobility_participant.py"),
            ref("implementation", "afritech/security/device_identity.py"),
            ref("test", "afriride_system/tests/test_event_ledger_validation.py"),
            ref("test", "afritech/tests/identity/test_mobility_participant.py"),
            ref("replay", "reports/adversarial_integrity_proof_v1/identity_spoofing.json"),
            ref("proof", "docs/architecture/AFRIID_UNIFIED_MOBILITY_PARTICIPANT_MODEL.md"),
            ref("boundary_guard", "afritech/ci/identity_validator.py"),
        ),
        boundary="Identity proof verifies signer and participant evidence only; it cannot override replay, proof, dispatch, or payment truth.",
        boundary_guard="afritech/ci/identity_validator.py",
        version="v1",
        last_updated="2026-06-17",
        dependencies=("trust-kernel", "governance-chain"),
    ),
    FeatureEvidence(
        id="trip-integrity-proof",
        name="Trip Integrity Proof",
        description="Verifies that trip lifecycle events, trace hashes, replay receipts, and evidence exports match.",
        technical_status="IMPLEMENTED",
        activation_status="PRODUCTION_READY",
        evidence=(
            ref("implementation", "afriride_system/backend/trace_enforcement.py"),
            ref("implementation", "afriride_system/backend/evidence_engine.py"),
            ref("implementation", "afriride_system/backend/replay_engine.py"),
            ref("test", "afriride_system/tests/test_trace_enforcement.py"),
            ref("test", "afriride_system/tests/test_evidence_engine.py"),
            ref("replay", "traces/pilot_runs/day_one_003/replay_verification_result.json"),
            ref("proof", "docs/proof/AFRIRIDE_CONTROLLED_PILOT_EXECUTION_RECEIPT.md"),
            ref("boundary_guard", "afritech/ci/afriride_controlled_pilot_execution_receipt_validator.py"),
        ),
        boundary="Trip integrity proof exports replay-verifiable evidence and does not authorize live field execution.",
        boundary_guard="afritech/ci/afriride_controlled_pilot_execution_receipt_validator.py",
        version="v1",
        last_updated="2026-06-17",
        dependencies=("trust-kernel", "pilot-gates"),
    ),
    FeatureEvidence(
        id="payment-proof-anchor",
        name="Payment Proof Anchor",
        description="Packages payment and ledger receipt evidence into a signed, externally verifiable proof anchor.",
        technical_status="IMPLEMENTED",
        activation_status="PRODUCTION_READY",
        evidence=(
            ref("implementation", "afritech/afripay/protocol.py"),
            ref("implementation", "afritech/afripay/public_validation.py"),
            ref("implementation", "afritech/architecture/blockchain_anchor.py"),
            ref("test", "afritech/tests/afripay/test_afripay_verifiable_payment_api.py"),
            ref("test", "afritech/tests/crypto/test_blockchain_anchor.py"),
            ref("replay", "traces/pilot_runs/day_one_003/api_response_receipts.json"),
            ref("proof", "docs/proof/ECONOMIC_TRUST_PROOF.md"),
            ref("boundary_guard", "afritech/ci/afritech_blockchain_anchor_validator.py"),
        ),
        boundary="Payment proof anchors prove exported payment evidence only; they do not activate settlement, pricing, escrow, or economic authority.",
        boundary_guard="afritech/ci/afritech_blockchain_anchor_validator.py",
        version="v1",
        last_updated="2026-06-17",
        dependencies=("trust-kernel", "governance-chain"),
    ),
    FeatureEvidence(
        id="domain-surfaces",
        name="Domain Surfaces",
        description="Defines bounded surfaces for AfriRide, AfriConnectTL, AfriEats, and AfriPay.",
        technical_status="PARTIAL",
        activation_status="GATED",
        evidence=(
            ref("implementation", "afritech/architecture/surface_authority_registry.yaml"),
            ref("implementation", "afritech/architecture/planned_surface_policy.yaml"),
            ref("implementation", "afritech/afripay/protocol.py"),
            ref("test", "afritech/tests/afripay/test_afripay_protocol_level_design.py"),
            ref("test", "afritech/tests/governance/test_afriride_rider_features_doc.py"),
            ref("replay", "reports/afriride_live_pilot_protocol_v1/stakeholder_evidence_report_initial.json"),
            ref("proof", "docs/requirements/AfriRide_Rider_Features_and_Experience.md"),
            ref("boundary_guard", "afritech/ci/surface_state_resolution_validator.py"),
        ),
        boundary="Planned product surfaces must remain planned until implementation and replay evidence exist.",
        boundary_guard="afritech/ci/surface_state_resolution_validator.py",
        version="v1",
        last_updated="2026-06-16",
        dependencies=("governance-chain",),
    ),
    FeatureEvidence(
        id="legal-evidence-export",
        name="Legal Evidence Export",
        description="Packages replayable evidence for jurisdiction-aware review.",
        technical_status="IMPLEMENTED",
        activation_status="GATED",
        evidence=(
            ref("implementation", "afriride/field_validation/stakeholder_evidence_report.py"),
            ref("implementation", "afritech/tools/external_verifier_cli.py"),
            ref("implementation", "afritech/verify/public_verifier_bundle.schema.json"),
            ref("test", "afritech/tests/distributed/test_docs_and_tools_suite.py"),
            ref("test", "afritech/tests/afripay/test_afripay_regulatory_assurance.py"),
            ref("replay", "traces/pilot_runs/day_one_003/stakeholder_evidence_report.md"),
            ref("proof", "docs/api/afriride_mobile_api_contract.md"),
            ref("boundary_guard", "afritech/ci/afriride_stakeholder_evidence_report_validator.py"),
        ),
        boundary="Evidence export is review material and must be independently replay-verifiable.",
        boundary_guard="afritech/ci/afriride_stakeholder_evidence_report_validator.py",
        version="v1",
        last_updated="2026-06-16",
        dependencies=("trust-kernel", "pilot-gates"),
    ),
    FeatureEvidence(
        id="operational-tooling",
        name="Operational Tooling",
        description="Provides CLI, inspectors, validators, and pilot readiness checks.",
        technical_status="IMPLEMENTED",
        activation_status="GATED",
        evidence=(
            ref("implementation", "afritech/cli/main.py"),
            ref("implementation", "dashboard/src/App.jsx"),
            ref("implementation", "replay_dashboard/src/App.jsx"),
            ref("test", "dashboard/tests/test_operator_dashboard_surface.py"),
            ref("test", "afritech/tests/distributed/test_activation_scale_and_services.py"),
            ref("replay", "traces/sample_trace.json"),
            ref("proof", "README.md"),
            ref("boundary_guard", "afritech/ci/observability_authority_validator.py"),
        ),
        boundary="Tooling visualizes and validates evidence; it does not override replay or governance.",
        boundary_guard="afritech/ci/observability_authority_validator.py",
        version="v1",
        last_updated="2026-06-16",
        dependencies=("legal-evidence-export", "classification-ci"),
    ),
)


def path_exists(evidence_ref: EvidenceRef) -> bool:
    return (ROOT / evidence_ref.path).exists()


def file_non_empty(evidence_ref: EvidenceRef) -> bool:
    path = ROOT / evidence_ref.path
    return path.exists() and path.stat().st_size > 0


def valid_json_file(evidence_ref: EvidenceRef) -> bool:
    path = ROOT / evidence_ref.path
    if path.suffix.lower() != ".json":
        return True

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return False

    return isinstance(payload, dict) and len(payload) > 0


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_repository_for_evidence(
    candidates: tuple[FeatureEvidence, ...] = FEATURE_CANDIDATES,
) -> dict[str, EvidenceArtifact]:
    artifacts: dict[str, EvidenceArtifact] = {}

    for feature in candidates:
        origin_event = f"feature-evidence:{feature.id}:{feature.version}"
        timestamp = f"{feature.last_updated}T00:00:00Z"
        for evidence_ref in feature.evidence:
            path = ROOT / evidence_ref.path
            if not path.exists() or not path.is_file():
                continue
            artifacts[evidence_ref.path] = EvidenceArtifact(
                id=hashlib.sha256(evidence_ref.path.encode("utf-8")).hexdigest()[:16],
                type=evidence_ref.kind,
                path=evidence_ref.path,
                hash=file_sha256(path),
                size_bytes=path.stat().st_size,
                required=evidence_ref.required,
                origin_event=origin_event,
                timestamp=timestamp,
            )

    return artifacts


def valid_proof_payload(evidence_ref: EvidenceRef) -> bool:
    path = ROOT / evidence_ref.path
    if evidence_ref.kind != "proof" or path.suffix.lower() != ".json":
        return True

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False

    return isinstance(payload, dict) and REQUIRED_PROOF_KEYS.issubset(payload.keys())


def authority_chain_valid(payload: dict[str, object]) -> bool:
    classification = payload.get("classification")
    authority_source = payload.get("authority_source")
    if not isinstance(classification, str) or not isinstance(authority_source, str):
        return False
    return classification in ALLOWED_PROOF_CLASSES and authority_source in TRUSTED_AUTHORITIES


def proof_hash_matches_replay(
    evidence_ref: EvidenceRef,
    feature: FeatureEvidence,
    evidence_index: dict[str, EvidenceArtifact] | None = None,
) -> bool:
    path = ROOT / evidence_ref.path
    if evidence_ref.kind != "proof" or path.suffix.lower() != ".json":
        return True

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False

    replay_hash = payload.get("replay_hash")
    if replay_hash is None:
        return True
    if not isinstance(replay_hash, str):
        return False

    index = evidence_index or scan_repository_for_evidence((feature,))
    replay_hashes = {
        index[evidence.path].hash
        for evidence in feature.evidence
        if evidence.kind == "replay" and evidence.path in index
    }
    return replay_hash in replay_hashes


def proof_admissible(
    evidence_ref: EvidenceRef,
    feature: FeatureEvidence,
    evidence_index: dict[str, EvidenceArtifact] | None = None,
) -> bool:
    path = ROOT / evidence_ref.path
    if evidence_ref.kind != "proof" or path.suffix.lower() != ".json":
        return valid_proof_payload(evidence_ref)

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False

    return (
        isinstance(payload, dict)
        and REQUIRED_PROOF_KEYS.issubset(payload.keys())
        and authority_chain_valid(payload)
        and proof_hash_matches_replay(evidence_ref, feature, evidence_index)
    )


def boundary_guard_exists(feature: FeatureEvidence) -> bool:
    return (ROOT / feature.boundary_guard).exists()


def boundary_guard_valid(feature: FeatureEvidence) -> bool:
    return feature.boundary_guard.endswith(".py") and boundary_guard_exists(feature)


def evidence_ref_valid(evidence_ref: EvidenceRef) -> bool:
    return (
        path_exists(evidence_ref)
        and file_non_empty(evidence_ref)
        and valid_json_file(evidence_ref)
        and valid_proof_payload(evidence_ref)
    )


def evidence_complete(
    feature: FeatureEvidence,
    evidence_index: dict[str, EvidenceArtifact] | None = None,
) -> bool:
    index = evidence_index or scan_repository_for_evidence((feature,))
    required_refs = [evidence_ref for evidence_ref in feature.evidence if evidence_ref.required]
    return (
        all(
            evidence_ref.path in index
            and evidence_ref_valid(evidence_ref)
            and proof_admissible(evidence_ref, feature, index)
            for evidence_ref in required_refs
        )
        and boundary_guard_valid(feature)
    )


def evidence_chain_hash(
    feature: FeatureEvidence,
    evidence_index: dict[str, EvidenceArtifact] | None = None,
) -> str:
    index = evidence_index or scan_repository_for_evidence((feature,))
    chain_payload = [
        {
            "kind": evidence.kind,
            "path": evidence.path,
            "required": evidence.required,
            "hash": index[evidence.path].hash if evidence.path in index else None,
        }
        for evidence in feature.evidence
    ]
    encoded = json.dumps(chain_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def feature_validation_summary(
    feature: FeatureEvidence,
    evidence_index: dict[str, EvidenceArtifact] | None = None,
) -> dict[str, object]:
    index = evidence_index or scan_repository_for_evidence((feature,))
    required_refs = [evidence_ref for evidence_ref in feature.evidence if evidence_ref.required]
    optional_refs = [evidence_ref for evidence_ref in feature.evidence if not evidence_ref.required]
    invalid_required = [
        evidence_ref.path
        for evidence_ref in required_refs
        if evidence_ref.path not in index
        or not evidence_ref_valid(evidence_ref)
        or not proof_admissible(evidence_ref, feature, index)
    ]
    invalid_optional = [
        evidence_ref.path
        for evidence_ref in optional_refs
        if evidence_ref.path not in index
        or not evidence_ref_valid(evidence_ref)
        or not proof_admissible(evidence_ref, feature, index)
    ]

    return {
        "required_evidence_count": len(required_refs),
        "optional_evidence_count": len(optional_refs),
        "invalid_required_evidence": invalid_required,
        "invalid_optional_evidence": invalid_optional,
        "boundary_guard_exists": boundary_guard_exists(feature),
        "boundary_guard_valid": boundary_guard_valid(feature),
        "evidence_complete": len(invalid_required) == 0 and boundary_guard_valid(feature),
        "evidence_chain_hash": evidence_chain_hash(feature, index),
        "proof_admissible": all(
            proof_admissible(evidence_ref, feature, index)
            for evidence_ref in feature.evidence
            if evidence_ref.kind == "proof"
        ),
    }


def derive_features_from_evidence(
    evidence_index: dict[str, EvidenceArtifact],
    candidates: tuple[FeatureEvidence, ...] = FEATURE_CANDIDATES,
) -> tuple[FeatureEvidence, ...]:
    derived: list[FeatureEvidence] = []
    completed_ids: set[str] = set()

    for feature in candidates:
        if not evidence_complete(feature, evidence_index):
            continue
        if not set(feature.dependencies).issubset(completed_ids):
            continue
        derived.append(feature)
        completed_ids.add(feature.id)

    return tuple(derived)


EVIDENCE_INDEX = scan_repository_for_evidence()
FEATURES = derive_features_from_evidence(EVIDENCE_INDEX)


def feature_names() -> list[str]:
    return [feature.name for feature in FEATURES]


def feature_ids() -> list[str]:
    return [feature.id for feature in FEATURES]


def feature_matrix() -> list[dict[str, object]]:
    return [feature.canonical_dict() for feature in FEATURES]


def feature_by_id(feature_id: str) -> FeatureEvidence:
    for feature in FEATURES:
        if feature.id == feature_id:
            return feature
    raise KeyError(f"Unknown AfriTech feature id: {feature_id}")


def status_summary() -> str:
    return (
        f"{SYSTEM_STATUS['classification']} "
        f"(live_pilot_authorized={SYSTEM_STATUS['live_pilot_authorized']}, "
        f"production_proven={SYSTEM_STATUS['production_proven']})"
    )


def incomplete_features() -> list[str]:
    return [
        feature.id
        for feature in FEATURE_CANDIDATES
        if not evidence_complete(feature, EVIDENCE_INDEX)
    ]


def _stable_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return "unavailable"
    return result.stdout.strip() or "unavailable"


def feature_hash() -> str:
    return _stable_hash(feature_matrix())


def evidence_hash() -> str:
    return _stable_hash(
        [artifact.canonical_dict() for artifact in sorted(EVIDENCE_INDEX.values(), key=lambda item: item.path)]
    )


def registry_payload() -> dict[str, object]:
    production_ready_features = [
        feature.id
        for feature in FEATURES
        if feature.activation_status == "PRODUCTION_READY"
    ]
    payload = {
        "classification": REGISTRY_CLASSIFICATION,
        "status": REGISTRY_STATUS,
        "generation_mode": REGISTRY_GENERATION_MODE,
        "system_status": SYSTEM_STATUS,
        "candidate_feature_count": len(FEATURE_CANDIDATES),
        "feature_count": len(FEATURES),
        "complete_feature_count": len(FEATURES),
        "incomplete_feature_ids": incomplete_features(),
        "production_ready_feature_count": len(production_ready_features),
        "production_ready_feature_ids": production_ready_features,
        "verified_true_threshold": 3,
        "verified_true": len(production_ready_features) >= 3,
        "live_pilot_authorized": SYSTEM_STATUS["live_pilot_authorized"],
        "production_proven": SYSTEM_STATUS["production_proven"],
        "economic_activation_allowed": SYSTEM_STATUS["economic_activation_allowed"],
        "claim_history": "docs/governance/AFRITECH_FEATURE_CLAIM_HISTORY.md",
        "read_only": True,
        "creates_authority": False,
        "evidence_index": [
            artifact.canonical_dict()
            for artifact in sorted(EVIDENCE_INDEX.values(), key=lambda item: item.path)
        ],
        "feature_hash": feature_hash(),
        "evidence_hash": evidence_hash(),
        "features": feature_matrix(),
    }
    registry_hash = _stable_hash(payload)
    payload["registry_hash"] = registry_hash
    payload["signature"] = {
        "algorithm": "Ed25519",
        "signer_id": signer_id(),
        "public_key": public_key_hex(),
        "value": sign_registry(registry_hash),
        "scope": "registry_payload",
        "trust_chain": ("AFRITECH_CORE", "REGISTRY_SIGNER", "VALIDATOR"),
    }
    return payload


def generate_claim_snapshot(version: str = "v1") -> dict[str, object]:
    payload = registry_payload()
    snapshot = {
        "schema": SNAPSHOT_SCHEMA,
        "version": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "classification": payload["classification"],
        "status": payload["status"],
        "generation_mode": payload["generation_mode"],
        "feature_count": payload["feature_count"],
        "candidate_feature_count": payload["candidate_feature_count"],
        "feature_hash": payload["feature_hash"],
        "evidence_hash": payload["evidence_hash"],
        "registry_hash": payload["registry_hash"],
        "signature": payload["signature"],
        "incomplete_feature_ids": payload["incomplete_feature_ids"],
        "production_ready_feature_count": payload["production_ready_feature_count"],
        "live_pilot_authorized": payload["live_pilot_authorized"],
        "production_proven": payload["production_proven"],
        "economic_activation_allowed": payload["economic_activation_allowed"],
    }
    snapshot["snapshot_hash"] = _stable_hash(snapshot)
    return snapshot


def write_claim_snapshot(version: str = "v1") -> Path:
    output_dir = ROOT / "reports/feature_registry_history"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{version}.json"
    output_path.write_text(
        json.dumps(generate_claim_snapshot(version), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "FEATURES",
    "FEATURE_CANDIDATES",
    "EVIDENCE_INDEX",
    "REGISTRY_CLASSIFICATION",
    "REGISTRY_GENERATION_MODE",
    "REGISTRY_STATUS",
    "REQUIRED_PROOF_KEYS",
    "ROOT",
    "SYSTEM_STATUS",
    "ActivationStatus",
    "EvidenceKind",
    "EvidenceRef",
    "EvidenceArtifact",
    "FeatureEvidence",
    "TechnicalStatus",
    "authority_chain_valid",
    "boundary_guard_exists",
    "boundary_guard_valid",
    "derive_features_from_evidence",
    "evidence_complete",
    "evidence_hash",
    "evidence_chain_hash",
    "evidence_ref_valid",
    "feature_by_id",
    "feature_hash",
    "feature_ids",
    "feature_matrix",
    "feature_names",
    "feature_validation_summary",
    "file_non_empty",
    "generate_claim_snapshot",
    "incomplete_features",
    "path_exists",
    "proof_admissible",
    "proof_hash_matches_replay",
    "registry_payload",
    "scan_repository_for_evidence",
    "status_summary",
    "valid_json_file",
    "valid_proof_payload",
    "write_claim_snapshot",
]
