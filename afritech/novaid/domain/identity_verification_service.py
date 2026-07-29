from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .biometric_models import BiometricPurpose
from .document_models import (
    DocumentAuthenticityDecision,
    DocumentVerificationStatus,
    IdentityDocument,
)
from .document_ocr_models import (
    OCRExtractionDecision,
)
from .document_selfie_match_models import (
    DocumentSelfieMatchDecision,
)
from .identity_verification_events import (
    IdentityVerificationOutcomeEvent,
    identity_verification_outcome_event,
)
from .identity_verification_models import (
    IdentityVerificationDecision,
    IdentityVerificationEvidence,
    IdentityVerificationPolicy,
    IdentityVerificationRecord,
)
from .models import (
    AssuranceLevel,
    RequestContext,
    Tenant,
    identifier,
    utcnow,
)


@dataclass(frozen=True)
class IdentityVerificationResult:
    document: IdentityDocument
    verification: IdentityVerificationRecord
    event: IdentityVerificationOutcomeEvent


class IdentityVerificationService:
    """Orchestrate the final governed eKYC decision."""

    def verify(
        self,
        *,
        context: RequestContext,
        tenant: Tenant,
        document: IdentityDocument,
        evidence: IdentityVerificationEvidence,
        expected_version: int,
        policy: IdentityVerificationPolicy | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityVerificationResult:
        active_policy = (
            policy or IdentityVerificationPolicy()
        )

        self._assert_tenant_boundary(
            context=context,
            tenant=tenant,
            document=document,
        )
        self._assert_document_version(
            document=document,
            expected_version=expected_version,
        )
        self._assert_document_state(document)
        self._assert_evidence_bindings(
            document=document,
            evidence=evidence,
        )

        combined_score = self._combined_score(
            evidence=evidence,
        )

        decision, reason_codes = self._decide(
            evidence=evidence,
            policy=active_policy,
            combined_score=combined_score,
        )

        assurance_level = self._assurance_level(
            decision=decision,
            policy=active_policy,
        )

        moment = utcnow()
        verification_id = identifier()

        next_status = self._document_status(
            decision=decision,
        )

        updated_document = replace(
            document,
            status=next_status,
            verified_at=(
                moment
                if next_status
                is DocumentVerificationStatus.VERIFIED
                else document.verified_at
            ),
            updated_at=moment,
            version=document.version + 1,
        )

        verification = IdentityVerificationRecord(
            verification_id=verification_id,
            workflow_id=evidence.workflow_id,
            tenant_id=document.tenant_id,
            identity_id=document.identity_id,
            document_id=document.document_id,
            document_type=document.document_type,
            purpose=evidence.selfie_match.purpose,
            decision=decision,
            assurance_level=assurance_level,
            combined_score=combined_score,
            ocr_score=(
                evidence.ocr_extraction
                .overall_confidence_score
            ),
            authenticity_score=(
                evidence.authenticity_assessment
                .overall_score
            ),
            selfie_match_score=(
                evidence.selfie_match
                .similarity_score
            ),
            liveness_score=(
                evidence.selfie_match
                .liveness_score
            ),
            ocr_extraction_id=(
                evidence.ocr_extraction.extraction_id
            ),
            authenticity_assessment_id=(
                evidence.authenticity_assessment
                .assessment_id
            ),
            selfie_match_id=(
                evidence.selfie_match.match_id
            ),
            policy_version=active_policy.policy_version,
            document_version=updated_document.version,
            verified_at=moment,
            reason_codes=reason_codes,
            metadata=dict(metadata or {}),
        )

        event = identity_verification_outcome_event(
            verification_id=verification.verification_id,
            workflow_id=verification.workflow_id,
            tenant_id=verification.tenant_id,
            identity_id=verification.identity_id,
            document_id=verification.document_id,
            actor_identity_id=context.actor_identity_id,
            correlation_id=context.correlation_id,
            request_id=context.request_id,
            document_type=verification.document_type,
            purpose=verification.purpose,
            decision=verification.decision,
            assurance_level=verification.assurance_level,
            combined_score=verification.combined_score,
            policy_version=verification.policy_version,
            document_version=verification.document_version,
            reason_codes=verification.reason_codes,
            metadata=metadata,
        )

        return IdentityVerificationResult(
            document=updated_document,
            verification=verification,
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
    def _assert_document_version(
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
                "DOCUMENT_NOT_AVAILABLE_FOR_FINAL_VERIFICATION"
            )

        if document.is_expired():
            raise ValueError(
                "DOCUMENT_EXPIRED"
            )

    @staticmethod
    def _assert_evidence_bindings(
        *,
        document: IdentityDocument,
        evidence: IdentityVerificationEvidence,
    ) -> None:
        ocr = evidence.ocr_extraction
        authenticity = evidence.authenticity_assessment
        selfie = evidence.selfie_match

        tenant_ids = {
            document.tenant_id,
            ocr.tenant_id,
            authenticity.tenant_id,
            selfie.tenant_id,
        }

        if tenant_ids != {document.tenant_id}:
            raise PermissionError(
                "IDENTITY_VERIFICATION_TENANT_MISMATCH"
            )

        identity_ids = {
            document.identity_id,
            ocr.identity_id,
            authenticity.identity_id,
            selfie.identity_id,
        }

        if identity_ids != {document.identity_id}:
            raise PermissionError(
                "IDENTITY_VERIFICATION_IDENTITY_MISMATCH"
            )

        document_ids = {
            document.document_id,
            ocr.document_id,
            authenticity.document_id,
            selfie.document_id,
        }

        if document_ids != {document.document_id}:
            raise ValueError(
                "IDENTITY_VERIFICATION_DOCUMENT_MISMATCH"
            )

        document_types = {
            document.document_type,
            ocr.document_type,
            authenticity.document_type,
            selfie.document_type,
        }

        if document_types != {document.document_type}:
            raise ValueError(
                "IDENTITY_VERIFICATION_DOCUMENT_TYPE_MISMATCH"
            )

        evidence_versions = {
            ocr.document_version,
            authenticity.document_version,
            selfie.document_version,
        }

        if any(
            version < 1
            for version in evidence_versions
        ):
            raise ValueError(
                "INVALID_EVIDENCE_DOCUMENT_VERSION"
            )

        if max(evidence_versions) > document.version:
            raise RuntimeError(
                "EVIDENCE_VERSION_AHEAD_OF_DOCUMENT"
            )

    @staticmethod
    def _combined_score(
        *,
        evidence: IdentityVerificationEvidence,
    ) -> float:
        scores = (
            evidence.ocr_extraction
            .overall_confidence_score,
            evidence.authenticity_assessment
            .overall_score,
            evidence.selfie_match
            .similarity_score,
            evidence.selfie_match
            .liveness_score,
        )

        return round(
            sum(scores) / len(scores),
            6,
        )

    @staticmethod
    def _decide(
        *,
        evidence: IdentityVerificationEvidence,
        policy: IdentityVerificationPolicy,
        combined_score: float,
    ) -> tuple[
        IdentityVerificationDecision,
        tuple[str, ...],
    ]:
        ocr = evidence.ocr_extraction
        authenticity = evidence.authenticity_assessment
        selfie = evidence.selfie_match

        if (
            policy.require_ekyc_purpose
            and selfie.purpose
            is not BiometricPurpose.EKYC
        ):
            return (
                IdentityVerificationDecision.REJECTED,
                ("EKYC_PURPOSE_REQUIRED",),
            )

        if (
            policy.lock_on_session_lock
            and selfie.decision
            is DocumentSelfieMatchDecision.LOCK_SESSION
        ):
            return (
                IdentityVerificationDecision.LOCKED,
                ("BIOMETRIC_SESSION_LOCK_REQUIRED",),
            )

        if (
            policy.reject_suspected_fraud
            and authenticity.decision
            is DocumentAuthenticityDecision.SUSPECTED_FRAUD
        ):
            return (
                IdentityVerificationDecision.REJECTED,
                ("DOCUMENT_FRAUD_DETECTED",),
            )

        if ocr.decision in {
            OCRExtractionDecision.REJECT,
        }:
            return (
                IdentityVerificationDecision.REJECTED,
                ("OCR_REJECTED",),
            )

        if (
            authenticity.decision
            is DocumentAuthenticityDecision.UNREADABLE
        ):
            return (
                IdentityVerificationDecision.RECAPTURE_REQUIRED,
                ("DOCUMENT_UNREADABLE",),
            )

        if (
            selfie.decision
            is DocumentSelfieMatchDecision.NO_MATCH
        ):
            return (
                IdentityVerificationDecision.REJECTED,
                ("DOCUMENT_SELFIE_NO_MATCH",),
            )

        if ocr.decision in {
            OCRExtractionDecision.RECAPTURE,
            OCRExtractionDecision.PARTIAL,
        }:
            return (
                IdentityVerificationDecision.RECAPTURE_REQUIRED,
                ("OCR_RECAPTURE_REQUIRED",),
            )

        if (
            selfie.decision
            is DocumentSelfieMatchDecision.RECAPTURE
        ):
            return (
                IdentityVerificationDecision.RECAPTURE_REQUIRED,
                ("SELFIE_RECAPTURE_REQUIRED",),
            )

        review_required = any(
            (
                ocr.decision
                is OCRExtractionDecision.MANUAL_REVIEW,
                authenticity.decision
                is DocumentAuthenticityDecision.MANUAL_REVIEW,
                selfie.decision
                is DocumentSelfieMatchDecision.MANUAL_REVIEW,
            )
        )

        if review_required:
            return (
                IdentityVerificationDecision.MANUAL_REVIEW,
                ("IDENTITY_VERIFICATION_REVIEW_REQUIRED",),
            )

        if (
            policy.require_ocr_accept
            and ocr.decision
            is not OCRExtractionDecision.ACCEPT
        ):
            return (
                IdentityVerificationDecision.MANUAL_REVIEW,
                ("OCR_ACCEPTANCE_REQUIRED",),
            )

        if (
            policy.require_authentic_document
            and authenticity.decision
            is not DocumentAuthenticityDecision.AUTHENTIC
        ):
            return (
                IdentityVerificationDecision.MANUAL_REVIEW,
                ("AUTHENTIC_DOCUMENT_REQUIRED",),
            )

        if (
            policy.require_document_selfie_match
            and selfie.decision
            is not DocumentSelfieMatchDecision.MATCH
        ):
            return (
                IdentityVerificationDecision.MANUAL_REVIEW,
                ("DOCUMENT_SELFIE_MATCH_REQUIRED",),
            )

        threshold_failures: list[str] = []

        if (
            ocr.overall_confidence_score
            < policy.minimum_ocr_score
        ):
            threshold_failures.append(
                "OCR_SCORE_BELOW_POLICY"
            )

        if (
            authenticity.overall_score
            < policy.minimum_authenticity_score
        ):
            threshold_failures.append(
                "AUTHENTICITY_SCORE_BELOW_POLICY"
            )

        if (
            selfie.similarity_score
            < policy.minimum_selfie_match_score
        ):
            threshold_failures.append(
                "SELFIE_MATCH_SCORE_BELOW_POLICY"
            )

        if (
            selfie.liveness_score
            < policy.minimum_liveness_score
        ):
            threshold_failures.append(
                "LIVENESS_SCORE_BELOW_POLICY"
            )

        if threshold_failures:
            return (
                IdentityVerificationDecision.MANUAL_REVIEW,
                tuple(threshold_failures),
            )

        if (
            combined_score
            >= policy.minimum_combined_score
        ):
            return (
                IdentityVerificationDecision.VERIFIED,
                (
                    "IDENTITY_VERIFICATION_CONTROLS_SATISFIED",
                ),
            )

        if (
            combined_score
            >= policy.manual_review_combined_score
        ):
            return (
                IdentityVerificationDecision.MANUAL_REVIEW,
                (
                    "COMBINED_SCORE_REVIEW_REQUIRED",
                ),
            )

        return (
            IdentityVerificationDecision.REJECTED,
            (
                "IDENTITY_VERIFICATION_SCORE_TOO_LOW",
            ),
        )

    @staticmethod
    def _assurance_level(
        *,
        decision: IdentityVerificationDecision,
        policy: IdentityVerificationPolicy,
    ) -> AssuranceLevel:
        if (
            decision
            is IdentityVerificationDecision.VERIFIED
        ):
            return policy.verified_assurance_level

        if (
            decision
            is IdentityVerificationDecision.MANUAL_REVIEW
        ):
            return policy.manual_review_assurance_level

        return AssuranceLevel.NID_AL0

    @staticmethod
    def _document_status(
        *,
        decision: IdentityVerificationDecision,
    ) -> DocumentVerificationStatus:
        if (
            decision
            is IdentityVerificationDecision.VERIFIED
        ):
            return DocumentVerificationStatus.VERIFIED

        if (
            decision
            is IdentityVerificationDecision.MANUAL_REVIEW
        ):
            return (
                DocumentVerificationStatus.MANUAL_REVIEW
            )

        if (
            decision
            is IdentityVerificationDecision.REJECTED
        ):
            return DocumentVerificationStatus.REJECTED

        return DocumentVerificationStatus.IN_PROGRESS
