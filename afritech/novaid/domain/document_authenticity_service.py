from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .document_authenticity_events import (
    DocumentAuthenticityAssessmentEvent,
    document_authenticity_assessment_event,
)
from .document_authenticity_models import (
    DocumentAuthenticityAssessmentRecord,
    DocumentAuthenticityPolicy,
    DocumentAuthenticityProviderEvidence,
)
from .document_models import (
    DocumentAuthenticityDecision,
    DocumentAuthenticityEvidence,
    DocumentVerificationStatus,
    IdentityDocument,
    IdentityDocumentType,
)
from .models import (
    RequestContext,
    Tenant,
    identifier,
    utcnow,
)


@dataclass(frozen=True)
class DocumentAuthenticityAssessmentResult:
    document: IdentityDocument
    assessment: DocumentAuthenticityAssessmentRecord
    event: DocumentAuthenticityAssessmentEvent


class DocumentAuthenticityService:
    """Govern provider-produced document-authenticity evidence."""

    def assess(
        self,
        *,
        context: RequestContext,
        tenant: Tenant,
        document: IdentityDocument,
        evidence: DocumentAuthenticityProviderEvidence,
        expected_version: int,
        policy: DocumentAuthenticityPolicy | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DocumentAuthenticityAssessmentResult:
        active_policy = (
            policy or DocumentAuthenticityPolicy()
        )

        self._assert_boundaries(
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
            policy=active_policy,
        )

        decision, reason_codes = self._decide(
            document=document,
            evidence=evidence,
            policy=active_policy,
        )

        moment = utcnow()
        assessment_id = identifier()

        canonical_evidence = DocumentAuthenticityEvidence(
            decision=decision,
            overall_score=evidence.overall_score,
            tampering_score=evidence.tampering_score,
            security_feature_score=(
                evidence.security_feature_score
            ),
            hologram_score=evidence.hologram_score,
            portrait_integrity_score=(
                evidence.portrait_integrity_score
            ),
            mrz_consistent=evidence.mrz_consistent,
            barcode_consistent=(
                evidence.barcode_consistent
            ),
            provider_reference=(
                evidence.provider_reference
            ),
            algorithm_version=(
                evidence.algorithm_version
            ),
            reason_codes=reason_codes,
            metadata=dict(metadata or {}),
        )

        next_status = document.status

        if (
            decision
            is DocumentAuthenticityDecision.MANUAL_REVIEW
        ):
            next_status = (
                DocumentVerificationStatus.MANUAL_REVIEW
            )

        updated_document = replace(
            document,
            status=next_status,
            authenticity_evidence=canonical_evidence,
            provider_reference=(
                evidence.provider_reference
            ),
            algorithm_version=(
                evidence.algorithm_version
            ),
            updated_at=moment,
            version=document.version + 1,
        )

        assessment = DocumentAuthenticityAssessmentRecord(
            assessment_id=assessment_id,
            tenant_id=document.tenant_id,
            identity_id=document.identity_id,
            document_id=document.document_id,
            document_type=document.document_type,
            decision=decision,
            overall_score=evidence.overall_score,
            tampering_score=evidence.tampering_score,
            provider_reference=(
                evidence.provider_reference
            ),
            algorithm_version=(
                evidence.algorithm_version
            ),
            document_version=updated_document.version,
            security_feature_score=(
                evidence.security_feature_score
            ),
            hologram_score=evidence.hologram_score,
            portrait_integrity_score=(
                evidence.portrait_integrity_score
            ),
            mrz_consistent=evidence.mrz_consistent,
            barcode_consistent=(
                evidence.barcode_consistent
            ),
            fraud_indicators=evidence.fraud_indicators,
            assessed_at=moment,
            reason_codes=reason_codes,
            metadata=dict(metadata or {}),
        )

        event = document_authenticity_assessment_event(
            assessment_id=assessment.assessment_id,
            tenant_id=assessment.tenant_id,
            identity_id=assessment.identity_id,
            document_id=assessment.document_id,
            actor_identity_id=context.actor_identity_id,
            correlation_id=context.correlation_id,
            request_id=context.request_id,
            document_type=assessment.document_type,
            decision=assessment.decision,
            overall_score=assessment.overall_score,
            tampering_score=assessment.tampering_score,
            document_version=assessment.document_version,
            reason_codes=assessment.reason_codes,
            metadata=metadata,
        )

        return DocumentAuthenticityAssessmentResult(
            document=updated_document,
            assessment=assessment,
            event=event,
        )

    @staticmethod
    def _assert_boundaries(
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
            DocumentVerificationStatus.IN_PROGRESS,
            DocumentVerificationStatus.MANUAL_REVIEW,
        }:
            raise ValueError(
                "DOCUMENT_NOT_AVAILABLE_FOR_AUTHENTICITY"
            )

        if not document.captures:
            raise ValueError(
                "DOCUMENT_CAPTURE_REQUIRED"
            )

        if document.is_expired():
            raise ValueError(
                "DOCUMENT_EXPIRED"
            )

    @staticmethod
    def _assert_document_type(
        *,
        document: IdentityDocument,
        evidence: DocumentAuthenticityProviderEvidence,
    ) -> None:
        if evidence.document_type is not document.document_type:
            raise ValueError(
                "AUTHENTICITY_DOCUMENT_TYPE_MISMATCH"
            )

    @staticmethod
    def _assert_capture_policy(
        *,
        tenant: Tenant,
        document: IdentityDocument,
        policy: DocumentAuthenticityPolicy,
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

    @staticmethod
    def _decide(
        *,
        document: IdentityDocument,
        evidence: DocumentAuthenticityProviderEvidence,
        policy: DocumentAuthenticityPolicy,
    ) -> tuple[
        DocumentAuthenticityDecision,
        tuple[str, ...],
    ]:
        if (
            policy.require_supported_template
            and not evidence.document_template_supported
        ):
            return (
                DocumentAuthenticityDecision.UNREADABLE,
                ("DOCUMENT_TEMPLATE_UNSUPPORTED",),
            )

        if (
            policy.fail_on_severe_fraud
            and evidence.severe_fraud_detected()
        ):
            return (
                DocumentAuthenticityDecision.SUSPECTED_FRAUD,
                ("SEVERE_DOCUMENT_FRAUD_DETECTED",),
            )

        if (
            evidence.tampering_score
            >= policy.severe_tampering_score
        ):
            return (
                DocumentAuthenticityDecision.SUSPECTED_FRAUD,
                ("SEVERE_DOCUMENT_TAMPERING_DETECTED",),
            )

        if (
            document.document_type
            is IdentityDocumentType.PASSPORT
            and policy.require_mrz_consistency_for_passports
            and evidence.mrz_consistent is not True
        ):
            return (
                DocumentAuthenticityDecision.SUSPECTED_FRAUD,
                ("PASSPORT_MRZ_INCONSISTENT",),
            )

        if (
            policy.require_barcode_consistency_when_present
            and document.barcode_evidence is not None
            and evidence.barcode_consistent is not True
        ):
            return (
                DocumentAuthenticityDecision.SUSPECTED_FRAUD,
                ("DOCUMENT_BARCODE_INCONSISTENT",),
            )

        if (
            evidence.tampering_score
            > policy.maximum_tampering_score
        ):
            return (
                DocumentAuthenticityDecision.MANUAL_REVIEW,
                ("DOCUMENT_TAMPERING_REVIEW_REQUIRED",),
            )

        if (
            policy.require_security_features
            and (
                evidence.security_feature_score is None
                or evidence.security_feature_score
                < policy.minimum_security_feature_score
            )
        ):
            return (
                DocumentAuthenticityDecision.MANUAL_REVIEW,
                ("SECURITY_FEATURE_REVIEW_REQUIRED",),
            )

        if (
            evidence.portrait_integrity_score is not None
            and evidence.portrait_integrity_score
            < policy.minimum_portrait_integrity_score
        ):
            return (
                DocumentAuthenticityDecision.MANUAL_REVIEW,
                ("PORTRAIT_INTEGRITY_REVIEW_REQUIRED",),
            )

        if (
            evidence.overall_score
            >= policy.authentic_threshold
        ):
            return (
                DocumentAuthenticityDecision.AUTHENTIC,
                ("DOCUMENT_AUTHENTICITY_CONTROLS_SATISFIED",),
            )

        if (
            evidence.overall_score
            >= policy.manual_review_threshold
        ):
            return (
                DocumentAuthenticityDecision.MANUAL_REVIEW,
                ("DOCUMENT_AUTHENTICITY_REVIEW_REQUIRED",),
            )

        return (
            DocumentAuthenticityDecision.UNREADABLE,
            ("DOCUMENT_AUTHENTICITY_SCORE_TOO_LOW",),
        )
