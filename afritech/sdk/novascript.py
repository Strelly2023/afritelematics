from __future__ import annotations

from hashlib import sha256
from typing import Any


def verify_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    required = {
        "receipt_id",
        "organization_id",
        "project_id",
        "prompt_hash",
        "output_hash",
        "trust_score",
        "status",
        "sequence",
        "signature",
    }
    missing = sorted(required - set(receipt))
    if missing:
        return {"verified": False, "reason": "missing_fields", "missing": missing}
    expected = sha256(
        (
            f"{receipt['receipt_id']}:{receipt['prompt_hash']}:{receipt['output_hash']}:"
            f"{receipt['trust_score']}:{receipt['status']}:{receipt['sequence']}"
        ).encode("utf-8")
    ).hexdigest()
    return {
        "verified": expected == receipt.get("signature"),
        "reason": "signature_match" if expected == receipt.get("signature") else "signature_mismatch",
        "receipt_id": receipt.get("receipt_id"),
        "expected_signature": expected,
    }


def validate_certificate_chain(
    *,
    receipt: dict[str, Any],
    certificate_chain: dict[str, Any],
    receipt_verification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    receipt_verification = receipt_verification or verify_receipt(receipt)
    root = certificate_chain.get("root_certificate", {})
    org = certificate_chain.get("organization_certificate", {})
    receipt_cert = certificate_chain.get("receipt_certificate", {})
    checks = {
        "receipt_signature": bool(receipt_verification.get("verified")),
        "root_certificate": root.get("certificate_id") == "novatrust-root-v1",
        "organization_certificate": org.get("issuer") == root.get("certificate_id"),
        "receipt_certificate": receipt_cert.get("subject") == receipt.get("receipt_id"),
        "federation_consensus": bool(certificate_chain.get("federation_consensus", {}).get("verified")),
        "chain_hash": bool(certificate_chain.get("chain_hash")),
    }
    return {
        "verified": all(checks.values()),
        "checks": checks,
        "chain_id": certificate_chain.get("chain_id"),
        "chain_hash": certificate_chain.get("chain_hash"),
    }


def verify_audit_package(package: dict[str, Any]) -> dict[str, Any]:
    receipt = package.get("receipt", {})
    chain = package.get("certificate_chain", {})
    if not isinstance(receipt, dict) or not isinstance(chain, dict):
        return {"mode": "external_audit_verification", "verified": False, "reason": "invalid_package"}
    receipt_verification = verify_receipt(receipt)
    chain_verification = validate_certificate_chain(
        receipt=receipt,
        certificate_chain=chain,
        receipt_verification=receipt_verification,
    )
    return {
        "mode": "external_audit_verification",
        "verified": bool(receipt_verification.get("verified")) and bool(chain_verification.get("verified")),
        "receipt": receipt_verification,
        "certificate_chain": chain_verification,
    }


def evaluate_policy(*, source: str, context: dict[str, Any]) -> dict[str, Any]:
    requirements = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("require "):
            requirements.append(stripped.removeprefix("require ").strip())
    decisions = [_evaluate_requirement(requirement, context) for requirement in requirements]
    policy_hash = sha256(f"{source}:{sorted(context.items())}".encode("utf-8")).hexdigest()
    return {
        "mode": "sdk_policy_evaluation",
        "policy_hash": policy_hash,
        "allowed": all(item["passed"] for item in decisions),
        "requirements": decisions,
    }


def validate_portable_package(package: dict[str, Any]) -> dict[str, Any]:
    manifest = package.get("verification_manifest", {})
    files = package.get("files", {})
    verified = (
        package.get("mode") == "portable_verification_package"
        and isinstance(files, dict)
        and isinstance(manifest, dict)
        and bool(manifest.get("offline_verification"))
        and manifest.get("requires_novascript_runtime") is False
        and bool(manifest.get("manifest_hash"))
    )
    return {
        "mode": "portable_package_validation",
        "verified": verified,
        "manifest_hash": manifest.get("manifest_hash"),
        "file_count": len(files) if isinstance(files, dict) else 0,
    }


def submit_trust_exchange(
    *,
    issuer_org: str,
    subject_org: str,
    receipt_hash: str,
    trust_score: int,
) -> dict[str, Any]:
    score = max(0, min(100, int(trust_score)))
    exchange_hash = sha256(f"{issuer_org}:{subject_org}:{receipt_hash}:{score}".encode()).hexdigest()
    return {
        "mode": "cross_organization_trust_exchange",
        "exchange_id": "trustx-" + exchange_hash[:12],
        "issuer_org": issuer_org,
        "subject_org": subject_org,
        "receipt_hash": receipt_hash,
        "trust_score": score,
        "verified": score >= 60,
        "exchange_hash": exchange_hash,
    }


def validate_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    artifact_type = str(payload.get("artifact_type", "")).strip()
    artifact = payload.get("artifact", {})
    if not isinstance(artifact, dict):
        return {"mode": "novascript_artifact_validation", "verified": False, "reason": "artifact_must_be_object"}
    if artifact_type == "governance_receipt":
        result = verify_receipt(artifact)
    elif artifact_type == "audit_package":
        result = verify_audit_package(artifact)
    elif artifact_type == "portable_verification_package":
        result = validate_portable_package(artifact)
    elif artifact_type == "certificate_chain":
        receipt = payload.get("receipt", {})
        result = validate_certificate_chain(
            receipt=receipt if isinstance(receipt, dict) else {},
            certificate_chain=artifact,
        )
    elif artifact_type == "novascript_execution":
        result = _validate_execution_artifact(artifact)
    else:
        return {
            "mode": "novascript_artifact_validation",
            "verified": False,
            "reason": "unsupported_artifact_type",
            "supported_artifact_types": [
                "governance_receipt",
                "audit_package",
                "portable_verification_package",
                "certificate_chain",
                "novascript_execution",
            ],
        }
    return {
        "mode": "novascript_artifact_validation",
        "artifact_type": artifact_type,
        "verified": bool(result.get("verified")),
        "result": result,
    }


def _validate_execution_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    required = {"policy_decision_id", "certificate_chain_id", "assurance_status", "artifact_type"}
    missing = sorted(required - set(artifact))
    return {
        "verified": not missing and artifact.get("artifact_type") == "novascript_execution",
        "reason": "execution_artifact_valid" if not missing else "missing_fields",
        "missing": missing,
    }


def _evaluate_requirement(requirement: str, context: dict[str, Any]) -> dict[str, Any]:
    parts = requirement.split()
    passed = False
    if len(parts) == 3:
        key, op, raw_value = parts
        left = context.get(key)
        right: Any = raw_value
        if raw_value.lower() == "true":
            right = True
        elif raw_value.lower() == "false":
            right = False
        else:
            try:
                right = int(raw_value)
            except ValueError:
                right = raw_value.strip('"')
        if op == ">=":
            passed = int(left or 0) >= int(right)
        elif op == "<=":
            passed = int(left or 0) <= int(right)
        elif op == "==":
            passed = left == right
    return {"requirement": requirement, "passed": passed}
