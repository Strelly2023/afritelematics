from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from afritech.afripay.public_validation import (
    PublicProofValidationReport,
    validate_public_proof_artifact,
    validate_public_proof_file,
)


@dataclass(frozen=True)
class IndependentAuditSandboxReport:
    artifact_path: str
    pdf_path: str | None
    proof_report: PublicProofValidationReport
    pdf_verified: bool
    verified: bool
    authority_boundary: str = "independent_audit_sandbox_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "authority_boundary": self.authority_boundary,
            "pdf_path": self.pdf_path,
            "pdf_verified": self.pdf_verified,
            "proof_report": self.proof_report.canonical_dict(),
            "schema": "afritech.afripay.independent_audit_sandbox_report.v1",
            "verified": self.verified,
        }


class IndependentAuditSandbox:
    def verify(self, artifact_path: str | Path, *, public_key_pem: str | None = None) -> IndependentAuditSandboxReport:
        path = Path(artifact_path)
        if path.is_dir():
            json_path = path / "recursive_proof_bundle.json"
            pdf_path = path / "recursive_proof_bundle.pdf"
        else:
            json_path = path
            pdf_path = path.with_suffix(".pdf")

        proof_report = validate_public_proof_file(json_path, public_key_pem=public_key_pem)
        pdf_verified = False
        if pdf_path.exists():
            pdf_verified = pdf_path.read_bytes().startswith(b"%PDF-")

        verified = proof_report.verified and (pdf_verified or not pdf_path.exists())
        return IndependentAuditSandboxReport(
            artifact_path=str(json_path),
            pdf_path=str(pdf_path) if pdf_path.exists() else None,
            proof_report=proof_report,
            pdf_verified=pdf_verified,
            verified=verified,
        )


def verify_independent_audit_sandbox(artifact_path: str | Path, *, public_key_pem: str | None = None) -> IndependentAuditSandboxReport:
    return IndependentAuditSandbox().verify(artifact_path, public_key_pem=public_key_pem)
