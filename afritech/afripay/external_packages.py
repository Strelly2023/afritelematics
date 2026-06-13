from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.afripay.protocol import SignedProofEvidence


@dataclass(frozen=True)
class RegulatorAuditPackage:
    title: str
    legal_wording: str
    evidence: SignedProofEvidence
    package_hash: str
    authority_boundary: str = "regulator_audit_package_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "evidence": self.evidence.canonical_dict(),
            "legal_wording": self.legal_wording,
            "package_hash": self.package_hash,
            "schema": "afritech.afripay.regulator_audit_package.v1",
            "title": self.title,
        }

    def pdf_bytes(self) -> bytes:
        return _build_pdf_document(
            self.title,
            [
                self.legal_wording,
                f"package_hash: {self.package_hash}",
                f"artifact_hash: {self.evidence.artifact_hash}",
                f"bundle_hash: {self.evidence.bundle.report_hash()}",
                f"signature_verified: {self.evidence.signature_verified}",
                f"verification_boundary: {self.authority_boundary}",
            ],
        )


@dataclass(frozen=True)
class InvestorTechnicalDossier:
    title: str
    summary: str
    evidence: SignedProofEvidence
    dossier_hash: str
    authority_boundary: str = "investor_technical_dossier_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "dossier_hash": self.dossier_hash,
            "evidence": self.evidence.canonical_dict(),
            "schema": "afritech.afripay.investor_technical_dossier.v1",
            "summary": self.summary,
            "title": self.title,
        }

    def pdf_bytes(self) -> bytes:
        return _build_pdf_document(
            self.title,
            [
                self.summary,
                f"dossier_hash: {self.dossier_hash}",
                f"artifact_hash: {self.evidence.artifact_hash}",
                f"report_hash: {self.evidence.report_hash()}",
                f"authority_boundary: {self.authority_boundary}",
            ],
        )


def build_regulator_audit_package(evidence: SignedProofEvidence) -> RegulatorAuditPackage:
    legal_wording = (
        "This regulator audit package is evidence-only. It supports regulator "
        "and independent audit review of the signed proof bundle, but it does "
        "not create settlement authority, execution authority, or regulatory approval."
    )
    title = "AfriPay Regulator Audit Package"
    package_hash = _canonical_hash({"legal_wording": legal_wording, "evidence": evidence.canonical_dict(), "title": title})
    return RegulatorAuditPackage(title=title, legal_wording=legal_wording, evidence=evidence, package_hash=package_hash)


def build_investor_technical_dossier(evidence: SignedProofEvidence) -> InvestorTechnicalDossier:
    summary = (
        "AfriPay is a verifiable financial protocol with signed recursive proofs, "
        "public verification, and bounded authority surfaces. This dossier is "
        "technical evidence for investors and diligence teams."
    )
    title = "AfriPay Investor Technical Dossier"
    dossier_hash = _canonical_hash({"summary": summary, "evidence": evidence.canonical_dict(), "title": title})
    return InvestorTechnicalDossier(title=title, summary=summary, evidence=evidence, dossier_hash=dossier_hash)


def export_package_artifacts(package: RegulatorAuditPackage | InvestorTechnicalDossier, output_dir: str | Path) -> dict[str, Path]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / f"{_slug(package.title)}.json"
    pdf_path = target / f"{_slug(package.title)}.pdf"
    json_path.write_text(json.dumps(package.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    pdf_path.write_bytes(package.pdf_bytes())
    return {"json": json_path, "pdf": pdf_path}


def _slug(value: str) -> str:
    return value.lower().replace(" ", "_")


def _canonical_hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _build_pdf_document(title: str, lines: list[str]) -> bytes:
    def _escape(text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content_lines = [f"({_escape(title)}) Tj", "T*"]
    for line in lines:
        content_lines.extend([f"({_escape(line)}) Tj", "T*"])
    content_stream = "BT /F1 12 Tf 72 760 Td " + " ".join(content_lines) + " ET"
    content_bytes = content_stream.encode("utf-8")
    objects: list[bytes] = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(
        b"5 0 obj << /Length "
        + str(len(content_bytes)).encode("utf-8")
        + b" >> stream\n"
        + content_bytes
        + b"\nendstream endobj\n"
    )
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n".encode("utf-8"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("utf-8"))
    pdf.extend((f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n").encode("utf-8"))
    return bytes(pdf)
