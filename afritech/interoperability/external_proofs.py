from __future__ import annotations

from typing import Any

from afritech.models import ExternalProofReference


class ExternalProofError(ValueError):
    """Raised when external proof references exceed evidence authority."""


def ingest_external_proof_reference(
    *,
    external_system: str,
    transaction_hash: str,
    proof_type: str,
    raw_reference: dict[str, Any],
) -> ExternalProofReference:
    _require_text(external_system, "external_system")
    _require_text(transaction_hash, "transaction_hash")
    _require_text(proof_type, "proof_type")
    record, _ = ExternalProofReference.objects.update_or_create(
        external_system=external_system,
        transaction_hash=transaction_hash,
        proof_type=proof_type,
        defaults={
            "raw_reference": raw_reference,
            "independently_verified": False,
            "verification_notes": "",
        },
    )
    return record


def verify_external_proof_reference(
    record: ExternalProofReference,
    *,
    verification_notes: str,
) -> ExternalProofReference:
    if not verification_notes.strip():
        raise ExternalProofError("external proof verification notes are required")
    ExternalProofReference.objects.filter(pk=record.pk).update(
        independently_verified=True,
        verification_notes=verification_notes,
    )
    record.refresh_from_db()
    return record


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ExternalProofError(f"{field} is required")
