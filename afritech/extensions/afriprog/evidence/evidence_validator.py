from __future__ import annotations

from typing import Any

from afritech.extensions.afriprog.evidence.evidence_model import (
    EvidenceRecord,
)


class EvidenceValidatorError(Exception):
    """Raised when evidence validation fails."""


class EvidenceValidator:
    """
    AfriProgramming evidence validator.

    Constitutional properties:
    - read-only
    - deterministic
    - schema-like validation
    - non-authoritative
    """

    REQUIRED_FIELDS = frozenset(
        {
            "evidence_id",
            "phase",
            "source",
            "status",
            "subject",
            "payload",
            "evidence_hash",
        }
    )

    ALLOWED_PHASES = frozenset(
        {
            "PHASE_1_REPOSITORY_INTELLIGENCE",
            "PHASE_2_READ_ONLY_PLANNING",
            "PHASE_3_PROPOSAL_ONLY",
        }
    )

    ALLOWED_SOURCES = frozenset(
        {
            "repository_intelligence",
            "task_planner",
            "validator_runner",
            "code_executor",
            "evidence_generator",
        }
    )

    def validate_record(self, record: EvidenceRecord) -> bool:
        data = record.canonical_dict()
        return self.validate_dict(data)

    def validate_dict(self, data: dict[str, Any]) -> bool:
        missing = self.REQUIRED_FIELDS - set(data)

        if missing:
            raise EvidenceValidatorError(
                f"missing evidence fields: {sorted(missing)}"
            )

        if data["phase"] not in self.ALLOWED_PHASES:
            raise EvidenceValidatorError(
                f"unsupported evidence phase: {data['phase']}"
            )

        if data["source"] not in self.ALLOWED_SOURCES:
            raise EvidenceValidatorError(
                f"unsupported evidence source: {data['source']}"
            )

        if not isinstance(data["payload"], dict):
            raise EvidenceValidatorError("payload must be a dictionary")

        if not isinstance(data["evidence_hash"], str):
            raise EvidenceValidatorError("evidence_hash must be a string")

        if len(data["evidence_hash"]) != 64:
            raise EvidenceValidatorError(
                "evidence_hash must be a sha256 hex string"
            )

        return True

    def validate_bundle(self, bundle: dict[str, Any]) -> bool:
        if "records" not in bundle:
            raise EvidenceValidatorError("bundle missing records")

        records = bundle["records"]

        if not isinstance(records, list):
            raise EvidenceValidatorError("bundle records must be a list")

        for record in records:
            if not isinstance(record, dict):
                raise EvidenceValidatorError(
                    "bundle record must be a dictionary"
                )

            self.validate_dict(record)

        return True