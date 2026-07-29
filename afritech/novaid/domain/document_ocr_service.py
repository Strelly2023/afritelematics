from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from typing import Any

from .document_models import (
    DocumentVerificationStatus,
    IdentityDocument,
    IdentityDocumentType,
    OCRFieldType,
)
from .document_ocr_events import (
    OCRExtractionEvent,
    ocr_extraction_event,
)
from .document_ocr_models import (
    OCRExtractionDecision,
    OCRExtractionPolicy,
    OCRExtractionRecord,
    OCRProviderEvidence,
    required_ocr_field_types,
)
from .models import (
    RequestContext,
    Tenant,
    identifier,
    utcnow,
)


@dataclass(frozen=True)
class OCRExtractionResult:
    document: IdentityDocument
    extraction: OCRExtractionRecord
    event: OCRExtractionEvent


class DocumentOCRService:
    """Govern provider-produced OCR evidence."""

    def extract(
        self,
        *,
        context: RequestContext,
        tenant: Tenant,
        document: IdentityDocument,
        evidence: OCRProviderEvidence,
        expected_version: int,
        policy: OCRExtractionPolicy | None = None,
        metadata: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> OCRExtractionResult:
        extraction_policy = (
            policy or OCRExtractionPolicy()
        )
        moment = now or utcnow()

        self._assert_tenant_boundary(
            context=context,
            tenant=tenant,
            document=document,
        )
        self._assert_version(
            document=document,
            expected_version=expected_version,
        )
        self._assert_document_state(document)
        self._assert_document_type(
            document=document,
            evidence=evidence,
        )
        self._assert_capture_policy(
            tenant=tenant,
            document=document,
            policy=extraction_policy,
        )

        decision, reason_codes = self._decide(
            document=document,
            evidence=evidence,
            policy=extraction_policy,
            at=moment,
        )

        extraction_id = identifier()

        extraction = OCRExtractionRecord(
            extraction_id=extraction_id,
            tenant_id=document.tenant_id,
            identity_id=document.identity_id,
            document_id=document.document_id,
            document_type=document.document_type,
            decision=decision,
            source=evidence.source,
            overall_confidence_score=(
                evidence.overall_confidence_score
            ),
            extracted_data=evidence.extracted_data,
            provider_reference=(
                evidence.provider_reference
            ),
            algorithm_version=(
                evidence.algorithm_version
            ),
            document_version=document.version + 1,
            fields=evidence.fields,
            mrz_evidence=evidence.mrz_evidence,
            barcode_evidence=evidence.barcode_evidence,
            extracted_at=moment,
            reason_codes=reason_codes,
            metadata=dict(metadata or {}),
        )

        updated_document = self._apply_extraction(
            document=document,
            evidence=evidence,
            decision=decision,
            at=moment,
            metadata=metadata,
        )

        event = ocr_extraction_event(
            extraction_id=extraction.extraction_id,
            tenant_id=extraction.tenant_id,
            identity_id=extraction.identity_id,
            document_id=extraction.document_id,
            actor_identity_id=context.actor_identity_id,
            correlation_id=context.correlation_id,
            request_id=context.request_id,
            document_type=extraction.document_type,
            decision=extraction.decision,
            source=extraction.source,
            overall_confidence_score=(
                extraction.overall_confidence_score
            ),
            document_version=updated_document.version,
            reason_codes=extraction.reason_codes,
            metadata=metadata,
        )

        return OCRExtractionResult(
            document=updated_document,
            extraction=extraction,
            event=event,
        )

    @staticmethod
    def _assert_tenant_boundary(
        *,
        context: RequestContext,
        tenant: Tenant,
        document: IdentityDocument,
    ) -> None:
        if context.tenant_id != tenant.tenant_id:
            raise PermissionError(
                "TENANT_ACCESS_DENIED"
            )

        if document.tenant_id != tenant.tenant_id:
            raise PermissionError(
                "DOCUMENT_TENANT_MISMATCH"
            )

    @staticmethod
    def _assert_version(
        *,
        document: IdentityDocument,
        expected_version: int,
    ) -> None:
        if (
            isinstance(expected_version, bool)
            or not isinstance(expected_version, int)
            or expected_version < 1
        ):
            raise ValueError(
                "INVALID_EXPECTED_VERSION"
            )

        if document.version != expected_version:
            raise RuntimeError(
                "CONCURRENCY_CONFLICT"
            )

    @staticmethod
    def _assert_document_state(
        document: IdentityDocument,
    ) -> None:
        if document.status not in {
            DocumentVerificationStatus.PENDING,
            DocumentVerificationStatus.IN_PROGRESS,
        }:
            raise ValueError(
                "DOCUMENT_NOT_AVAILABLE_FOR_OCR"
            )

        if not document.captures:
            raise ValueError(
                "DOCUMENT_CAPTURE_REQUIRED"
            )

    @staticmethod
    def _assert_document_type(
        *,
        document: IdentityDocument,
        evidence: OCRProviderEvidence,
    ) -> None:
        if (
            evidence.document_type
            is not document.document_type
        ):
            raise ValueError(
                "OCR_DOCUMENT_TYPE_MISMATCH"
            )

    @staticmethod
    def _assert_capture_policy(
        *,
        tenant: Tenant,
        document: IdentityDocument,
        policy: OCRExtractionPolicy,
    ) -> None:
        for capture in document.captures:
            quality = capture.capture_quality
            device = capture.capture_device
            environment = capture.capture_environment

            if quality is not None:
                if not quality.acceptable():
                    raise ValueError(
                        "ACCEPTABLE_DOCUMENT_CAPTURE_REQUIRED"
                    )

                if (
                    quality.overall_score
                    < policy.minimum_capture_quality_score
                ):
                    raise ValueError(
                        "DOCUMENT_CAPTURE_QUALITY_BELOW_POLICY"
                    )

            integrity_required = (
                policy.require_device_integrity
                or tenant.security_policy.device_binding_required
            )

            if (
                integrity_required
                and (
                    device is None
                    or not device.integrity_verified
                )
            ):
                raise PermissionError(
                    "CAPTURE_DEVICE_INTEGRITY_REQUIRED"
                )

            if (
                policy.deny_emulators
                and environment is not None
                and environment.emulator_detected
            ):
                raise PermissionError(
                    "DOCUMENT_CAPTURE_EMULATOR_DENIED"
                )

            if (
                policy.deny_compromised_devices
                and environment is not None
                and environment.rooted_or_jailbroken
            ):
                raise PermissionError(
                    "DOCUMENT_CAPTURE_COMPROMISED_DEVICE_DENIED"
                )

    @classmethod
    def _decide(
        cls,
        *,
        document: IdentityDocument,
        evidence: OCRProviderEvidence,
        policy: OCRExtractionPolicy,
        at: datetime,
    ) -> tuple[
        OCRExtractionDecision,
        tuple[str, ...],
    ]:
        missing_fields = cls._missing_required_fields(
            document_type=document.document_type,
            evidence=evidence,
            policy=policy,
        )

        weak_fields = tuple(
            field.field_type.value
            for field in evidence.fields
            if field.confidence_score
            < policy.minimum_required_field_confidence
        )

        if (
            document.document_type
            is IdentityDocumentType.PASSPORT
            and policy.require_valid_mrz_checksums_for_passports
        ):
            if evidence.mrz_evidence is None:
                return (
                    OCRExtractionDecision.MANUAL_REVIEW,
                    ("PASSPORT_MRZ_REQUIRED",),
                )

            if not evidence.mrz_evidence.checksums_valid:
                return (
                    OCRExtractionDecision.REJECT,
                    ("MRZ_CHECKSUM_INVALID",),
                )

        expiry = evidence.extracted_data.date_of_expiry

        if (
            expiry is not None
            and expiry <= at.astimezone(UTC).date()
        ):
            return (
                OCRExtractionDecision.REJECT,
                ("DOCUMENT_EXPIRED",),
            )

        if missing_fields:
            return (
                OCRExtractionDecision.RECAPTURE,
                tuple(
                    f"MISSING_{field}"
                    for field in missing_fields
                ),
            )

        if (
            evidence.overall_confidence_score
            >= policy.acceptance_threshold
            and not weak_fields
        ):
            return (
                OCRExtractionDecision.ACCEPT,
                ("OCR_CONTROLS_SATISFIED",),
            )

        if (
            evidence.overall_confidence_score
            >= policy.manual_review_threshold
        ):
            return (
                OCRExtractionDecision.MANUAL_REVIEW,
                (
                    "OCR_CONFIDENCE_REVIEW_REQUIRED",
                    *tuple(
                        f"LOW_CONFIDENCE_{field}"
                        for field in weak_fields
                    ),
                ),
            )

        if evidence.overall_confidence_score > 0.0:
            return (
                OCRExtractionDecision.RECAPTURE,
                ("OCR_CONFIDENCE_TOO_LOW",),
            )

        return (
            OCRExtractionDecision.REJECT,
            ("OCR_EXTRACTION_FAILED",),
        )

    @staticmethod
    def _missing_required_fields(
        *,
        document_type: IdentityDocumentType,
        evidence: OCRProviderEvidence,
        policy: OCRExtractionPolicy,
    ) -> tuple[str, ...]:
        required = set(
            required_ocr_field_types(document_type)
        )

        if not policy.require_document_number:
            required.discard(
                OCRFieldType.DOCUMENT_NUMBER
            )

        if not policy.require_date_of_birth:
            required.discard(
                OCRFieldType.DATE_OF_BIRTH
            )

        if (
            not policy.require_expiry_for_expiring_documents
        ):
            required.discard(
                OCRFieldType.DATE_OF_EXPIRY
            )

        if not policy.require_name:
            required.discard(
                OCRFieldType.FULL_NAME
            )
            required.discard(
                OCRFieldType.FAMILY_NAME
            )

        present = {
            field.field_type
            for field in evidence.fields
            if field.value.strip()
        }

        data = evidence.extracted_data

        if data.document_number:
            present.add(
                OCRFieldType.DOCUMENT_NUMBER
            )

        if data.family_name:
            present.add(
                OCRFieldType.FAMILY_NAME
            )

        if data.full_name:
            present.add(
                OCRFieldType.FULL_NAME
            )

        if data.date_of_birth:
            present.add(
                OCRFieldType.DATE_OF_BIRTH
            )

        if data.date_of_expiry:
            present.add(
                OCRFieldType.DATE_OF_EXPIRY
            )

        return tuple(
            sorted(
                field.value
                for field in required - present
            )
        )

    @staticmethod
    def _apply_extraction(
        *,
        document: IdentityDocument,
        evidence: OCRProviderEvidence,
        decision: OCRExtractionDecision,
        at: datetime,
        metadata: dict[str, Any] | None,
    ) -> IdentityDocument:
        next_status = (
            DocumentVerificationStatus.IN_PROGRESS
        )

        if (
            decision
            is OCRExtractionDecision.MANUAL_REVIEW
        ):
            next_status = (
                DocumentVerificationStatus.MANUAL_REVIEW
            )

        merged_metadata = dict(document.metadata)
        merged_metadata.update(metadata or {})

        return replace(
            document,
            status=next_status,
            extracted_data=evidence.extracted_data,
            mrz_evidence=evidence.mrz_evidence,
            barcode_evidence=evidence.barcode_evidence,
            provider_reference=(
                evidence.provider_reference
            ),
            algorithm_version=(
                evidence.algorithm_version
            ),
            issued_at=(
                evidence.extracted_data.date_of_issue
                or document.issued_at
            ),
            expires_at=(
                evidence.extracted_data.date_of_expiry
                or document.expires_at
            ),
            updated_at=at,
            version=document.version + 1,
            metadata=merged_metadata,
        )
