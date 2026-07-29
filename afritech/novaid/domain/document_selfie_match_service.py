from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .biometric_models import BiometricPurpose
from .biometric_verification_models import (
    FaceVerificationDecision,
)
from .document_models import (
    DocumentVerificationDecision,
    DocumentVerificationStatus,
    IdentityDocument,
)
from .document_selfie_match_events import (
    DocumentSelfieMatchEvent,
    document_selfie_match_event,
)
from .document_selfie_match_models import (
    DocumentSelfieMatchDecision,
    DocumentSelfieMatchEvidence,
    DocumentSelfieMatchPolicy,
    DocumentSelfieMatchRecord,
)
from .liveness_models import LivenessDecision
from .models import (
    RequestContext,
    Tenant,
    identifier,
    utcnow,
)


@dataclass(frozen=True)
class DocumentSelfieMatchResult:
    match: DocumentSelfieMatchRecord
    event: DocumentSelfieMatchEvent


class DocumentSelfieMatchService:
    """Convert document portrait, liveness and face evidence into a decision."""

    def match(
        self,
        *,
        context: RequestContext,
        tenant: Tenant,
        document: IdentityDocument,
        evidence: DocumentSelfieMatchEvidence,
        expected_version: int,
        policy: DocumentSelfieMatchPolicy | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DocumentSelfieMatchResult:
        active_policy = (
            policy or DocumentSelfieMatchPolicy()
        )

        self._assert_boundaries(
            context=context,
            tenant=tenant,
            document=document,
            evidence=evidence,
        )
        self._assert_version(
            document=document,
            expected_version=expected_version,
        )
        self._assert_document_state(document)

        decision, reason_codes = self._decide(
            evidence=evidence,
            policy=active_policy,
        )

        match_id = identifier()
        moment = utcnow()

        record = DocumentSelfieMatchRecord(
            match_id=match_id,
            tenant_id=document.tenant_id,
            identity_id=document.identity_id,
            document_id=document.document_id,
            document_evidence_id=(
                evidence.document_evidence.evidence_id
            ),
            verification_id=(
                evidence.face_verification.verification_id
            ),
            liveness_assessment_id=(
                evidence.liveness_assessment.assessment_id
            ),
            document_type=document.document_type,
            purpose=evidence.face_verification.purpose,
            decision=decision,
            similarity_score=(
                evidence.face_verification.similarity_score
            ),
            liveness_score=(
                evidence.liveness_assessment.liveness_score
            ),
            document_score=(
                evidence.document_evidence.overall_score
            ),
            portrait_reference=(
                evidence.document_evidence.portrait_reference
                or ""
            ),
            provider_reference=evidence.provider_reference,
            algorithm_version=evidence.algorithm_version,
            document_version=document.version,
            matched_at=moment,
            reason_codes=reason_codes,
            metadata=dict(metadata or {}),
        )

        event = document_selfie_match_event(
            match_id=record.match_id,
            tenant_id=record.tenant_id,
            identity_id=record.identity_id,
            document_id=record.document_id,
            verification_id=record.verification_id,
            liveness_assessment_id=(
                record.liveness_assessment_id
            ),
            actor_identity_id=context.actor_identity_id,
            correlation_id=context.correlation_id,
            request_id=context.request_id,
            document_type=record.document_type,
            purpose=record.purpose,
            decision=record.decision,
            similarity_score=record.similarity_score,
            document_version=record.document_version,
            reason_codes=record.reason_codes,
            metadata=metadata,
        )

        return DocumentSelfieMatchResult(
            match=record,
            event=event,
        )

    @staticmethod
    def _assert_boundaries(
        *,
        context: RequestContext,
        tenant: Tenant,
        document: IdentityDocument,
        evidence: DocumentSelfieMatchEvidence,
    ) -> None:
        if context.tenant_id != tenant.tenant_id:
            raise PermissionError("TENANT_ACCESS_DENIED")

        if document.tenant_id != tenant.tenant_id:
            raise PermissionError("DOCUMENT_TENANT_MISMATCH")

        document_evidence = evidence.document_evidence
        verification = evidence.face_verification
        liveness = evidence.liveness_assessment

        tenant_ids = {
            document_evidence.tenant_id,
            verification.tenant_id,
            liveness.tenant_id,
        }

        if tenant_ids != {tenant.tenant_id}:
            raise PermissionError(
                "DOCUMENT_SELFIE_TENANT_MISMATCH"
            )

        identity_ids = {
            document.identity_id,
            document_evidence.identity_id,
            verification.identity_id,
            liveness.identity_id,
        }

        if identity_ids != {document.identity_id}:
            raise PermissionError(
                "DOCUMENT_SELFIE_IDENTITY_MISMATCH"
            )

        if (
            document_evidence.document_id
            != document.document_id
        ):
            raise ValueError(
                "DOCUMENT_EVIDENCE_BINDING_MISMATCH"
            )

        if (
            document_evidence.document_type
            is not document.document_type
        ):
            raise ValueError(
                "DOCUMENT_TYPE_BINDING_MISMATCH"
            )

        if (
            verification.purpose
            is not liveness.purpose
        ):
            raise ValueError(
                "DOCUMENT_SELFIE_PURPOSE_MISMATCH"
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
            raise ValueError("INVALID_EXPECTED_VERSION")

        if document.version != expected_version:
            raise RuntimeError("CONCURRENCY_CONFLICT")

    @staticmethod
    def _assert_document_state(
        document: IdentityDocument,
    ) -> None:
        if document.status not in {
            DocumentVerificationStatus.IN_PROGRESS,
            DocumentVerificationStatus.MANUAL_REVIEW,
        }:
            raise ValueError(
                "DOCUMENT_NOT_AVAILABLE_FOR_SELFIE_MATCH"
            )

        if document.is_expired():
            raise ValueError("DOCUMENT_EXPIRED")

    @staticmethod
    def _decide(
        *,
        evidence: DocumentSelfieMatchEvidence,
        policy: DocumentSelfieMatchPolicy,
    ) -> tuple[
        DocumentSelfieMatchDecision,
        tuple[str, ...],
    ]:
        document_evidence = evidence.document_evidence
        verification = evidence.face_verification
        liveness = evidence.liveness_assessment

        if (
            policy.require_ekyc_purpose
            and verification.purpose
            is not BiometricPurpose.EKYC
        ):
            return (
                DocumentSelfieMatchDecision.NO_MATCH,
                ("EKYC_PURPOSE_REQUIRED",),
            )

        if liveness.decision is LivenessDecision.LOCK_SESSION:
            return (
                DocumentSelfieMatchDecision.LOCK_SESSION,
                ("LIVENESS_SESSION_LOCK_REQUIRED",),
            )

        if (
            policy.lock_on_liveness_attack
            and liveness.decision is LivenessDecision.FAIL
        ):
            return (
                DocumentSelfieMatchDecision.LOCK_SESSION,
                ("LIVENESS_ATTACK_OR_FAILURE_DETECTED",),
            )

        if (
            policy.require_liveness_pass
            and liveness.decision
            is not LivenessDecision.PASS
        ):
            if liveness.decision is LivenessDecision.RECAPTURE:
                return (
                    DocumentSelfieMatchDecision.RECAPTURE,
                    ("LIVENESS_RECAPTURE_REQUIRED",),
                )

            return (
                DocumentSelfieMatchDecision.MANUAL_REVIEW,
                ("LIVENESS_REVIEW_REQUIRED",),
            )

        if (
            liveness.liveness_score
            < policy.minimum_liveness_score
        ):
            return (
                DocumentSelfieMatchDecision.RECAPTURE,
                ("LIVENESS_SCORE_BELOW_POLICY",),
            )

        if (
            policy.require_document_pass
            and document_evidence.decision
            is not DocumentVerificationDecision.PASS
        ):
            if (
                document_evidence.decision
                is DocumentVerificationDecision.RECAPTURE
            ):
                return (
                    DocumentSelfieMatchDecision.RECAPTURE,
                    ("DOCUMENT_RECAPTURE_REQUIRED",),
                )

            if (
                document_evidence.decision
                is DocumentVerificationDecision.FAIL
            ):
                return (
                    DocumentSelfieMatchDecision.NO_MATCH,
                    ("DOCUMENT_VERIFICATION_FAILED",),
                )

            return (
                DocumentSelfieMatchDecision.MANUAL_REVIEW,
                ("DOCUMENT_REVIEW_REQUIRED",),
            )

        if (
            document_evidence.overall_score
            < policy.minimum_document_score
        ):
            return (
                DocumentSelfieMatchDecision.MANUAL_REVIEW,
                ("DOCUMENT_SCORE_BELOW_POLICY",),
            )

        if (
            verification.decision
            is FaceVerificationDecision.NO_MATCH
        ):
            return (
                DocumentSelfieMatchDecision.NO_MATCH,
                ("DOCUMENT_SELFIE_FACE_NO_MATCH",),
            )

        if (
            verification.decision
            is FaceVerificationDecision.MANUAL_REVIEW
        ):
            return (
                DocumentSelfieMatchDecision.MANUAL_REVIEW,
                ("DOCUMENT_SELFIE_FACE_REVIEW_REQUIRED",),
            )

        similarity = verification.similarity_score

        if (
            verification.decision
            is FaceVerificationDecision.MATCH
            and similarity >= policy.match_threshold
        ):
            return (
                DocumentSelfieMatchDecision.MATCH,
                ("DOCUMENT_SELFIE_CONTROLS_SATISFIED",),
            )

        if similarity >= policy.manual_review_threshold:
            return (
                DocumentSelfieMatchDecision.MANUAL_REVIEW,
                ("DOCUMENT_SELFIE_SCORE_REVIEW_REQUIRED",),
            )

        return (
            DocumentSelfieMatchDecision.NO_MATCH,
            ("DOCUMENT_SELFIE_SCORE_TOO_LOW",),
        )
