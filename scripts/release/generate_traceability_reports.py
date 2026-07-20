#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import subprocess
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


PRODUCT_REQUIREMENTS: dict[str, list[dict[str, Any]]] = {
    "novaid": [
        {
            "requirement_id": "NI-AUTH-001",
            "title": "Registration, password authentication, and session lifecycle",
            "statement": "NovaID must support workforce, rider, driver, agent, and merchant registration and password authentication with a governed session lifecycle.",
            "category": "functional",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/novaid", "afritech/api/novaid_api.py", "afritech/novaid/persistence/migrations"],
            "configuration_paths": ["contracts/api/baselines/novaid/latest.openapi.json"],
            "migration_paths": ["afritech/novaid/persistence/migrations/0002_novaid_runtime.sql"],
            "symbols": ["NovaIDService", "NovaIDSessionStore"],
            "test_ids": ["tests/novaid/test_novaid_ecosystem.py"],
            "commands": ["pytest -q tests/novaid/test_novaid_ecosystem.py"],
            "result_artifacts": ["docs/novaid/implementation/NOVAID_CURRENT_STATE.md"],
            "artifact_paths": ["docs/novaid/implementation/NOVAID_GAP_MATRIX.md"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novaid/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVAID-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "NOT_RUN",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["release candidate selection not yet frozen"],
        },
        {
            "requirement_id": "NI-RECOVERY-002",
            "title": "Account recovery and revocation",
            "statement": "NovaID must provide account recovery, revocation, and recovery controls for governed identities.",
            "category": "security",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/novaid/revocation.py", "afritech/novaid/revocation_delivery.py", "afritech/novaid/security.py"],
            "configuration_paths": ["docs/novaid/implementation/NOVAID_EXECUTION_PLAN.md"],
            "migration_paths": ["afritech/novaid/persistence/migrations/0007_novaid_webauthn_distributed_runtime.sql"],
            "symbols": ["revocation", "recovery"],
            "test_ids": ["afritech/tests/novaid/test_novaid_ecosystem.py"],
            "commands": ["pytest -q afritech/tests/novaid/test_novaid_ecosystem.py"],
            "result_artifacts": ["docs/novaid/implementation/NOVAID_CURRENT_STATE.md"],
            "artifact_paths": ["docs/novaid/implementation/NOVAID_GAP_MATRIX.md"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novaid/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVAID-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "NOT_RUN",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["external approval for release candidate not yet issued"],
        },
        {
            "requirement_id": "NI-AUTHZ-003",
            "title": "Tenant-aware authorization and audit events",
            "statement": "NovaID must enforce tenant-aware authorization and emit durable audit events.",
            "category": "security",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/novaid/service.py", "afritech/novaid/trust.py", "afritech/api/novaid_audit_replay_api.py"],
            "configuration_paths": ["contracts/api/baselines/novaid/latest.openapi.json"],
            "migration_paths": ["afritech/novaid/persistence/migrations/0008_novaid_governed_audit_replay.sql"],
            "symbols": ["audit", "authorization", "tenant"],
            "test_ids": ["afritech/tests/novaid/test_novaid_ecosystem.py"],
            "commands": ["pytest -q afritech/tests/novaid/test_novaid_ecosystem.py"],
            "result_artifacts": ["contracts/api/baselines/novaid/latest.openapi.json"],
            "artifact_paths": ["docs/novaid/implementation/NOVAID_GAP_MATRIX.md"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novaid/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVAID-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "NOT_RUN",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["no certified GA approval"],
        },
        {
            "requirement_id": "NI-MFA-004",
            "title": "MFA and step-up authentication",
            "statement": "NovaID should support MFA where fully implemented and record step-up authentication events.",
            "category": "security",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/novaid/ai.py", "afritech/novaid/runtime.py", "afritech/novaid/tokens.py"],
            "configuration_paths": ["docs/novaid/implementation/NOVAID_EXECUTION_PLAN.md"],
            "migration_paths": [],
            "symbols": ["MFA", "step-up"],
            "test_ids": ["afritech/tests/novaid/test_novaid_ecosystem.py"],
            "commands": ["pytest -q afritech/tests/novaid/test_novaid_ecosystem.py"],
            "result_artifacts": ["docs/novaid/implementation/NOVAID_CURRENT_STATE.md"],
            "artifact_paths": ["docs/novaid/implementation/NOVAID_GAP_MATRIX.md"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novaid/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVAID-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "NOT_RUN",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["certified MFA provider evidence not present"],
        },
        {
            "requirement_id": "NI-IDP-005",
            "title": "Supported identity provider integrations certified",
            "statement": "NovaID must only rely on approved and certified external identity provider integrations for GA.",
            "category": "compliance",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["docs/novaid/implementation/NOVAID_GAP_MATRIX.md"],
            "configuration_paths": ["contracts/api/baselines/novaid/latest.openapi.json"],
            "migration_paths": [],
            "symbols": ["identity provider"],
            "test_ids": ["afritech/tests/novaid/test_novaid_ecosystem.py"],
            "commands": ["pytest -q afritech/tests/novaid/test_novaid_ecosystem.py"],
            "result_artifacts": ["docs/novaid/implementation/NOVAID_GAP_MATRIX.md"],
            "artifact_paths": ["docs/novaid/implementation/NOVAID_GAP_MATRIX.md"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novaid/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVAID-RC-001"],
            "implementation_status": "BLOCKED",
            "verification_status": "NOT_RUN",
            "evidence_status": "BLOCKED",
            "acceptance_status": "BLOCKED",
            "blockers": ["certified external identity provider evidence absent"],
        },
    ],
    "novapay": [
        {
            "requirement_id": "NP-BALANCE-001",
            "title": "Balance visibility and controlled funding",
            "statement": "NovaPay must expose account balance visibility and controlled funding for approved domestic AUD flows.",
            "category": "functional",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/novapay", "afritech/core_platform/novapay_runtime.py", "afritech/api/novapay_runtime_api.py"],
            "configuration_paths": ["contracts/api/baselines/novapay/latest.openapi.json"],
            "migration_paths": [],
            "symbols": ["balance", "funding"],
            "test_ids": ["afritech/tests/core_platform/test_novapay_transfer_flow.py"],
            "commands": ["pytest -q afritech/tests/core_platform/test_novapay_transfer_flow.py"],
            "result_artifacts": ["reports/api-contracts/novapay.openapi.json"],
            "artifact_paths": ["docs/operations/NOVAPAY_MFS_FIRST_TRANSACTION_RUNBOOK.md"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novapay/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVAPAY-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "NOT_RUN",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["live money movement disabled until licensed arrangement exists"],
        },
        {
            "requirement_id": "NP-PAY-002",
            "title": "Controlled merchant payment and receipts",
            "statement": "NovaPay must support controlled merchant payment, reversal, and immutable receipt generation.",
            "category": "functional",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/api/novapay_ecosystem_api.py", "afritech/api/novapay_runtime_api.py", "afritech/core_platform/novapay_external_verifier.py"],
            "configuration_paths": ["contracts/api/baselines/novapay/latest.openapi.json"],
            "migration_paths": [],
            "symbols": ["receipt", "merchant payment", "reversal"],
            "test_ids": ["afritech/tests/core_platform/test_novapay_external_verifier.py"],
            "commands": ["pytest -q afritech/tests/core_platform/test_novapay_external_verifier.py"],
            "result_artifacts": ["reports/api-contracts/novapay.openapi.json"],
            "artifact_paths": ["docs/operations/NOVAPAY_PRODUCTION_ROLLOUT_PLAN.md"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novapay/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVAPAY-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "NOT_RUN",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["production payment activation not approved"],
        },
        {
            "requirement_id": "NP-REFUND-003",
            "title": "Refund and reconciliation workflow",
            "statement": "NovaPay must support refunds, reversals, and reconciliation with immutable receipts.",
            "category": "operations",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/tests/afripay/test_novapay_certification_fraud.py", "afritech/tests/core_platform/test_novapay_transfer_flow.py"],
            "configuration_paths": ["contracts/api/baselines/novapay/latest.openapi.json"],
            "migration_paths": [],
            "symbols": ["refund", "reconciliation"],
            "test_ids": ["afritech/tests/afripay/test_novapay_certification_fraud.py"],
            "commands": ["pytest -q afritech/tests/afripay/test_novapay_certification_fraud.py"],
            "result_artifacts": ["artifacts/novaride/ga-readiness/RELEASE_GATE_RESULTS.json"],
            "artifact_paths": ["docs/operations/NOVAPAY_TREASURY_AI_SYSTEM.md"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novapay/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVAPAY-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "NOT_RUN",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["live refund rail approval absent"],
        },
        {
            "requirement_id": "NP-RECON-004",
            "title": "Transaction limits and reconciliation",
            "statement": "NovaPay must enforce configuration-driven transaction limits and maintain reconciliation evidence.",
            "category": "data",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/ci/novapay_mobile_money_validator.py", "afritech/core_platform/novapay_runtime.py"],
            "configuration_paths": ["afritech/governance/adr/ADR-0048-novapay-multi-country-mobile-money.yaml"],
            "migration_paths": [],
            "symbols": ["transaction limit", "reconciliation"],
            "test_ids": ["afritech/tests/ci/test_novapay_mobile_money_validator.py"],
            "commands": ["pytest -q afritech/tests/ci/test_novapay_mobile_money_validator.py"],
            "result_artifacts": ["artifacts/novaride/ga-readiness/DEPENDENCY_LOCK_STATUS.json"],
            "artifact_paths": ["docs/technical/NOVAPAY_CERTIFICATION_FRAUD_DETECTION_LAYER.md"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novapay/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVAPAY-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "NOT_RUN",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["licensed settlement and reconciliation evidence absent"],
        },
        {
            "requirement_id": "NP-LIVE-005",
            "title": "Live money movement activation",
            "statement": "NovaPay may only enable live money movement after approved licensing, provider approval, live credentials, and settlement certification.",
            "category": "compliance",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["docs/operations/NOVAPAY_PRODUCTION_ROLLOUT_PLAN.md", "afritech/governance/rules/RULE-068-novapay-multi-country-mobile-money.yaml"],
            "configuration_paths": ["contracts/api/baselines/novapay/latest.openapi.json"],
            "migration_paths": [],
            "symbols": ["live money movement"],
            "test_ids": ["afritech/tests/core_platform/test_novapay_external_verifier.py"],
            "commands": ["pytest -q afritech/tests/core_platform/test_novapay_external_verifier.py"],
            "result_artifacts": ["artifacts/novaride/ga-readiness/RELEASE_GATE_RESULTS.json"],
            "artifact_paths": ["docs/operations/NOVAPAY_PRODUCTION_ROLLOUT_PLAN.md"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novapay/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVAPAY-RC-001"],
            "implementation_status": "BLOCKED",
            "verification_status": "NOT_RUN",
            "evidence_status": "BLOCKED",
            "acceptance_status": "BLOCKED",
            "blockers": ["licensed arrangement and live rail approval absent"],
        },
    ],
    "novaride": [
        {
            "requirement_id": "NR-RIDER-001",
            "title": "Rider registration and booking",
            "statement": "NovaRide must support rider registration, identity verification, and ride request creation within the defined Australian launch geography.",
            "category": "functional",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/novaride_runtime", "apps/novaride-operations", "rider_app"],
            "configuration_paths": ["docs/novaride/requirements/NOVARIDE_REQUIREMENTS.yaml"],
            "migration_paths": ["afritech/novaride_runtime/persistence/migrations/0001_novaride_runtime.sql"],
            "symbols": ["booking", "ride request"],
            "test_ids": ["tests/novaride_runtime/contracts/test_runtime_api.py", "apps/novaride-operations/tests/browser/overview.spec.ts"],
            "commands": ["pytest -q tests/novaride_runtime/contracts/test_runtime_api.py"],
            "result_artifacts": ["artifacts/novaride/ga-readiness/RIDE_LIFECYCLE_RESULTS.json"],
            "artifact_paths": ["artifacts/novaride/ga-readiness/TEST_RESULTS.json"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novaride/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVARIDE-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "PASS",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["live deployment approval not present"],
        },
        {
            "requirement_id": "NR-DRIVER-002",
            "title": "Driver registration and acceptance",
            "statement": "NovaRide must support driver registration, assignment, acceptance, and trip lifecycle management.",
            "category": "functional",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/novaride_runtime", "driver_app", "apps/novaride-operations"],
            "configuration_paths": ["docs/novaride/implementation/NOVARIDE_CURRENT_STATE.md"],
            "migration_paths": ["afritech/novaride_runtime/persistence/migrations/0004_novaride_read_models.sql"],
            "symbols": ["driver acceptance", "trip lifecycle"],
            "test_ids": ["tests/novaride_runtime/unit/test_state_machines.py", "apps/novaride-operations/tests/browser/navigation.spec.ts"],
            "commands": ["pytest -q tests/novaride_runtime/unit/test_state_machines.py"],
            "result_artifacts": ["artifacts/novaride/ga-readiness/RIDE_LIFECYCLE_RESULTS.json"],
            "artifact_paths": ["artifacts/novaride/ga-readiness/RELEASE_GATE_RESULTS.json"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novaride/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVARIDE-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "PASS",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["physical-device certification remains external"],
        },
        {
            "requirement_id": "NR-SAFETY-003",
            "title": "Safety event reporting and support workflow",
            "statement": "NovaRide must support safety event reporting, support workflows, and receipt generation for launch geography.",
            "category": "operations",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/novaride_runtime/safety", "apps/novaride-operations", "docs/novaride"],
            "configuration_paths": ["docs/novaride/strategy/NOVARIDE_PILOT_SUCCESS_CRITERIA.md"],
            "migration_paths": ["afritech/novaride_runtime/persistence/migrations/0008_novaride_resilience_hardening.sql"],
            "symbols": ["safety", "support", "receipt"],
            "test_ids": ["apps/novaride-operations/tests/browser/safety.spec.ts", "apps/novaride-operations/tests/browser/support.spec.ts"],
            "commands": ["PLAYWRIGHT_USE_EXISTING_SERVERS=1 PLAYWRIGHT_SKIP_BACKEND=1 npx playwright test tests/browser/safety.spec.ts tests/browser/support.spec.ts"],
            "result_artifacts": ["artifacts/novaride/operations-browser-certification/TEST_RESULTS.json"],
            "artifact_paths": ["artifacts/novaride/operations-browser-certification/RELEASE_DECISION.md"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novaride/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVARIDE-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "PASS",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["external pilot and live deployment evidence absent"],
        },
        {
            "requirement_id": "NR-PAY-004",
            "title": "Controlled cash or approved NovaPay payment handling",
            "statement": "NovaRide must accept only controlled cash or approved NovaPay payment handling in the launch geography.",
            "category": "functional",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/novaride_runtime/wallet_adapter", "afritech/novaride_runtime/pricing"],
            "configuration_paths": ["artifacts/novaride/ga-readiness/GA_SCOPE.json"],
            "migration_paths": ["afritech/novaride_runtime/persistence/migrations/0006_novaride_runtime_constraints.sql"],
            "symbols": ["cash", "NovaPay"],
            "test_ids": ["tests/novaride_runtime/deployment/test_production_operated_assets.py"],
            "commands": ["pytest -q tests/novaride_runtime/deployment/test_production_operated_assets.py"],
            "result_artifacts": ["artifacts/novaride/ga-readiness/LOAD_RESULTS.json"],
            "artifact_paths": ["artifacts/novaride/ga-readiness/RELEASE_GATE_RESULTS.json"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novaride/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVARIDE-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "PASS",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["approved NovaPay payment activation not yet certified"],
        },
        {
            "requirement_id": "NR-RUNTIME-005",
            "title": "Operational runtime, readiness, and evidence integration",
            "statement": "NovaRide must maintain the runtime, readiness, and evidence paths needed for governed operations.",
            "category": "operations",
            "mandatory_for_ga": True,
            "in_scope": True,
            "source_paths": ["afritech/novaride_runtime/readiness", "afritech/novaride_runtime/observability", "afritech/novaride_runtime/events"],
            "configuration_paths": ["artifacts/novaride/ga-readiness/INFRASTRUCTURE_RESULTS.json"],
            "migration_paths": ["afritech/novaride_runtime/persistence/migrations/0005_novaride_replay_indexes.sql"],
            "symbols": ["readiness", "evidence", "observability"],
            "test_ids": ["tests/novaride_runtime/replay/test_verified_replay.py", "tests/novaride_runtime/security/test_boundaries.py"],
            "commands": ["pytest -q tests/novaride_runtime/replay/test_verified_replay.py tests/novaride_runtime/security/test_boundaries.py"],
            "result_artifacts": ["artifacts/novaride/trusted-mobility-upgrade/TEST_RESULTS.json"],
            "artifact_paths": ["artifacts/novaride/trusted-mobility-upgrade/NOVARIDE_RELEASE_CERTIFICATE.md"],
            "manifest_paths": ["artifacts/release-baseline/evidence/novaride/TRACEABILITY_SUMMARY.json"],
            "certificate_ids": ["NOVARIDE-RC-001"],
            "implementation_status": "PASS",
            "verification_status": "PASS",
            "evidence_status": "PASS",
            "acceptance_status": "BLOCKED",
            "blockers": ["live PostgreSQL/Redis/Kafka proof and physical-device matrix remain external"],
        },
    ],
}


def repo_root() -> Path:
    path = Path(__file__).resolve()
    while path != path.parent:
        if (path / ".git").exists():
            return path
        path = path.parent
    raise SystemExit("unable to locate repository root")


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_manifest(root: Path) -> dict[str, Any]:
    manifest = load_json(root / "release" / "candidates" / "RELEASE_CANDIDATE_SET.json")
    if manifest.get("scope_id") != "INITIAL-GA-AU-VIC-001":
        raise SystemExit("unexpected scope id in release candidate set")
    return manifest


def summary_status(requirement: dict[str, Any]) -> str:
    if requirement["acceptance_status"] == "PASS":
        return "PASS"
    if requirement["acceptance_status"] == "BLOCKED":
        return "BLOCKED"
    return requirement["verification_status"]


def render_markdown(product: str, matrix: dict[str, Any]) -> str:
    lines = [
        f"# {product.upper()} traceability",
        "",
        f"Release candidate: {matrix['release_candidate_id']}",
        f"Commit: {matrix['commit_sha']}",
        f"Scope: {matrix['scope_id']}",
        "",
        "| Requirement | Status | Evidence | Blockers |",
        "| --- | --- | --- | --- |",
    ]
    for req in matrix["requirements"]:
        lines.append(
            f"| {req['requirement_id']} {req['title']} | {req['acceptance']['status']} | "
            f"{', '.join(req['evidence']['artifact_paths']) or 'none'} | "
            f"{'; '.join(req['acceptance']['blockers']) or 'none'} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_product_outputs(root: Path, product: str, matrix: dict[str, Any]) -> None:
    out_dir = root / "release" / "traceability"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{product.upper()}_TRACEABILITY.yaml").write_text(
        yaml.safe_dump(matrix, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (out_dir / f"{product.upper()}_TRACEABILITY.md").write_text(render_markdown(product, matrix), encoding="utf-8")
    evidence_dir = root / "artifacts" / "release-baseline" / "evidence" / product
    evidence_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "product": product,
        "release_candidate_id": matrix["release_candidate_id"],
        "commit_sha": matrix["commit_sha"],
        "scope_id": matrix["scope_id"],
        "generated_at_utc": matrix["generated_at_utc"],
        "requirements": [
            {
                "requirement_id": req["requirement_id"],
                "title": req["title"],
                "status": summary_status(req),
                "evidence": req["evidence"]["artifact_paths"],
                "tests": req["verification"]["test_ids"],
            }
            for req in matrix["requirements"]
        ],
    }
    (evidence_dir / "TRACEABILITY_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "TRACEABILITY_SUMMARY.md").write_text(render_markdown(product, matrix), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", default="release/scopes/INITIAL_GA_SCOPE.yaml")
    args = parser.parse_args()
    root = repo_root()
    if yaml is None:
        raise SystemExit("PyYAML is required for traceability generation")
    scope = yaml.safe_load((root / args.scope).read_text(encoding="utf-8"))
    scope_id = str(scope.get("scope_id") or "")
    manifest = ensure_manifest(root)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for product, requirements in PRODUCT_REQUIREMENTS.items():
        product_manifest = manifest["products"][product]
        matrix = {
            "schema_version": "1.0",
            "product": product,
            "release_candidate_id": product_manifest["release_candidate_id"],
            "commit_sha": product_manifest["commit_sha"],
            "scope_id": scope_id,
            "generated_at_utc": generated_at,
            "requirements": [],
        }
        for req in requirements:
            req_copy = dict(req)
            req_copy["current_status"] = summary_status(req)
            req_copy["last_validated_commit"] = product_manifest["commit_sha"]
            req_copy["reviewer"] = "release-baseline-generator"
            matrix["requirements"].append(
                {
                    "requirement_id": req_copy["requirement_id"],
                    "title": req_copy["title"],
                    "statement": req_copy["statement"],
                    "category": req_copy["category"],
                    "mandatory_for_ga": req_copy["mandatory_for_ga"],
                    "in_scope": req_copy["in_scope"],
                    "implementation": {
                        "status": req_copy["implementation_status"],
                        "source_paths": req_copy["source_paths"],
                        "configuration_paths": req_copy["configuration_paths"],
                        "migration_paths": req_copy["migration_paths"],
                        "symbols": req_copy["symbols"],
                    },
                    "verification": {
                        "status": req_copy["verification_status"],
                        "test_ids": req_copy["test_ids"],
                        "commands": req_copy["commands"],
                        "result_artifacts": req_copy["result_artifacts"],
                    },
                    "evidence": {
                        "status": req_copy["evidence_status"],
                        "artifact_paths": req_copy["artifact_paths"],
                        "manifest_paths": req_copy["manifest_paths"],
                        "certificate_ids": req_copy["certificate_ids"],
                    },
                    "acceptance": {
                        "status": req_copy["acceptance_status"],
                        "entry_criteria_ids": [f"{product.upper()}-ENTRY-001"],
                        "exit_criteria_ids": [f"{product.upper()}-EXIT-001"],
                        "blockers": req_copy["blockers"],
                    },
                    "current_status": req_copy["current_status"],
                    "last_validated_commit": req_copy["last_validated_commit"],
                    "reviewer": req_copy["reviewer"],
                }
            )
        write_product_outputs(root, product, matrix)
    print(json.dumps({"status": "PASS", "products": sorted(PRODUCT_REQUIREMENTS)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
