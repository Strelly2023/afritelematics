from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afritech.crypto.signature import verify_signature_with_public_key


@dataclass(frozen=True)
class PublicProofValidationReport:
    artifact_hash: str
    bundle_hash: str
    public_key_fingerprint: str
    signature_verified: bool
    structural_verified: bool
    verified: bool
    trust_breaks: tuple[str, ...]
    authority_boundary: str = "public_verification_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "artifact_hash": self.artifact_hash,
            "authority_boundary": self.authority_boundary,
            "bundle_hash": self.bundle_hash,
            "public_key_fingerprint": self.public_key_fingerprint,
            "schema": "afritech.afripay.public_proof_validation_report.v1",
            "signature_verified": self.signature_verified,
            "structural_verified": self.structural_verified,
            "trust_breaks": list(self.trust_breaks),
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


class PublicProofValidator:
    def validate(self, payload: Mapping[str, Any], *, public_key_pem: str | None = None) -> PublicProofValidationReport:
        if not isinstance(payload, Mapping):
            raise ValueError("payload must be a mapping")

        artifact_hash = str(payload.get("artifact_hash") or "")
        signature = str(payload.get("signature") or "")
        bundle = payload.get("bundle")
        if not isinstance(bundle, Mapping):
            raise ValueError("payload missing bundle")

        signer_public_key_pem = str(payload.get("signer_public_key_pem") or public_key_pem or "")
        public_key_fingerprint = str(payload.get("signer_public_key_fingerprint") or _canonical_hash({"public_key_pem": signer_public_key_pem}))

        structural_breaks: list[str] = []
        signature_breaks: list[str] = []
        if len(artifact_hash) != 64:
            structural_breaks.append("artifact_hash_invalid")
        if len(signature) == 0:
            signature_breaks.append("signature_missing")
        if len(signer_public_key_pem.strip()) == 0:
            signature_breaks.append("public_key_missing")

        bundle_hash = _canonical_hash(bundle)
        if bundle.get("verified") is not True:
            structural_breaks.append("bundle_not_verified")
        if bundle.get("recursive_proof_hash") != bundle.get("recursive_proof", {}).get("proof_hash"):
            structural_breaks.append("recursive_proof_hash_mismatch")
        if len(str(bundle.get("global_proof_hash") or "")) != 64:
            structural_breaks.append("global_proof_hash_invalid")
        if len(str(bundle.get("recursive_merkle_root") or "")) != 64:
            structural_breaks.append("recursive_merkle_root_invalid")
        if artifact_hash != bundle_hash:
            structural_breaks.append("artifact_hash_mismatch")

        signature_verified = verify_signature_with_public_key(artifact_hash, signature, signer_public_key_pem)
        if not signature_verified:
            signature_breaks.append("signature_verification_failed")

        trust_breaks = structural_breaks + signature_breaks
        verified = not trust_breaks
        return PublicProofValidationReport(
            artifact_hash=artifact_hash,
            bundle_hash=bundle_hash,
            public_key_fingerprint=public_key_fingerprint,
            signature_verified=signature_verified,
            structural_verified=not structural_breaks,
            verified=verified,
            trust_breaks=tuple(trust_breaks),
        )


def validate_public_proof_artifact(payload: Mapping[str, Any], *, public_key_pem: str | None = None) -> PublicProofValidationReport:
    return PublicProofValidator().validate(payload, public_key_pem=public_key_pem)


def load_public_proof_artifact(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("artifact must decode to a JSON object")
    return data


def validate_public_proof_file(path: str | Path, *, public_key_pem: str | None = None) -> PublicProofValidationReport:
    return validate_public_proof_artifact(load_public_proof_artifact(path), public_key_pem=public_key_pem)


def _canonical_hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def verify_signed_evidence(
    artifact: str | bytes | Mapping[str, Any],
    *,
    public_key_pem: str | None = None,
) -> dict[str, Any]:
    if isinstance(artifact, bytes):
        artifact = artifact.decode("utf-8")
    if isinstance(artifact, str):
        payload = json.loads(artifact)
    elif isinstance(artifact, Mapping):
        payload = dict(artifact)
    else:
        raise ValueError("artifact must be JSON text or mapping")

    report = validate_public_proof_artifact(payload, public_key_pem=public_key_pem)
    return {
        "verified": report.verified,
        "signature_valid": report.signature_verified,
        "bundle_valid": report.structural_verified,
        "report": report.canonical_dict(),
        "report_hash": report.report_hash(),
    }
