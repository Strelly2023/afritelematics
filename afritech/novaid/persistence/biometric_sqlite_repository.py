from __future__ import annotations

from typing import Any

from afritech.novaid.domain import (
    BiometricConsent,
    BiometricEnrollment,
    FaceAuthenticationRecord,
    FaceVerificationRecord,
    LivenessAssessmentRecord,
    RequestContext,
)

from .biometric_codec import (
    biometric_consent_from_row,
    biometric_enrollment_from_row,
    encode_attack_types,
    encode_capture_device,
    encode_capture_environment,
    encode_capture_quality,
    encode_metadata,
    encode_reason_codes,
    face_authentication_from_row,
    face_verification_from_row,
    liveness_assessment_from_row,
)


class BiometricSQLiteRepositoryMixin:
    """Tenant-isolated SQLite persistence for biometric assurance."""

    connection: Any

    @staticmethod
    def _assert_record_tenant(
        *,
        context: RequestContext,
        tenant_id: str,
    ) -> None:
        if context.tenant_id != tenant_id:
            raise PermissionError("TENANT_ACCESS_DENIED")

    @staticmethod
    def _required_row(
        row: Any | None,
    ) -> Any:
        if row is None:
            raise LookupError("TENANT_ACCESS_DENIED")

        return row

    # ------------------------------------------------------------------
    # Biometric consent
    # ------------------------------------------------------------------

    def add_biometric_consent(
        self,
        consent: BiometricConsent,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_biometric_consents("
            "consent_id,tenant_id,identity_id,purpose,policy_version,"
            "granted_at,status,expires_at,revoked_at,"
            "capture_notice_version,lawful_basis_reference,metadata"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                consent.consent_id,
                consent.tenant_id,
                consent.identity_id,
                consent.purpose.value,
                consent.policy_version,
                consent.granted_at.isoformat(),
                consent.status.value,
                (
                    consent.expires_at.isoformat()
                    if consent.expires_at is not None
                    else None
                ),
                (
                    consent.revoked_at.isoformat()
                    if consent.revoked_at is not None
                    else None
                ),
                consent.capture_notice_version,
                consent.lawful_basis_reference,
                encode_metadata(consent.metadata),
            ),
        )

    def get_biometric_consent(
        self,
        context: RequestContext,
        consent_id: str,
    ) -> BiometricConsent:
        row = self.connection.execute(
            "SELECT * FROM novaid_biometric_consents "
            "WHERE consent_id=? AND tenant_id=?",
            (
                consent_id,
                context.tenant_id,
            ),
        ).fetchone()

        return biometric_consent_from_row(
            self._required_row(row)
        )

    # ------------------------------------------------------------------
    # Biometric enrollment
    # ------------------------------------------------------------------

    def add_biometric_enrollment(
        self,
        enrollment: BiometricEnrollment,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_biometric_enrollments("
            "enrollment_id,tenant_id,identity_id,biometric_type,"
            "purpose,consent_id,template_reference,"
            "provider_reference,algorithm_version,status,"
            "capture_device,capture_environment,capture_quality,"
            "enrolled_at,expires_at,revoked_at,created_at,"
            "updated_at,version,metadata"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                enrollment.enrollment_id,
                enrollment.tenant_id,
                enrollment.identity_id,
                enrollment.biometric_type.value,
                enrollment.purpose.value,
                enrollment.consent_id,
                enrollment.template_reference,
                enrollment.provider_reference,
                enrollment.algorithm_version,
                enrollment.status.value,
                encode_capture_device(
                    enrollment.capture_device
                ),
                encode_capture_environment(
                    enrollment.capture_environment
                ),
                encode_capture_quality(
                    enrollment.capture_quality
                ),
                (
                    enrollment.enrolled_at.isoformat()
                    if enrollment.enrolled_at is not None
                    else None
                ),
                (
                    enrollment.expires_at.isoformat()
                    if enrollment.expires_at is not None
                    else None
                ),
                (
                    enrollment.revoked_at.isoformat()
                    if enrollment.revoked_at is not None
                    else None
                ),
                enrollment.created_at.isoformat(),
                enrollment.updated_at.isoformat(),
                enrollment.version,
                encode_metadata(enrollment.metadata),
            ),
        )

    def get_biometric_enrollment(
        self,
        context: RequestContext,
        enrollment_id: str,
    ) -> BiometricEnrollment:
        row = self.connection.execute(
            "SELECT * FROM novaid_biometric_enrollments "
            "WHERE enrollment_id=? AND tenant_id=?",
            (
                enrollment_id,
                context.tenant_id,
            ),
        ).fetchone()

        return biometric_enrollment_from_row(
            self._required_row(row)
        )

    def update_biometric_enrollment(
        self,
        context: RequestContext,
        enrollment: BiometricEnrollment,
        expected_version: int,
    ) -> None:
        self._assert_record_tenant(
            context=context,
            tenant_id=enrollment.tenant_id,
        )

        if expected_version < 1:
            raise ValueError("INVALID_EXPECTED_VERSION")

        result = self.connection.execute(
            "UPDATE novaid_biometric_enrollments SET "
            "identity_id=?,biometric_type=?,purpose=?,consent_id=?,"
            "template_reference=?,provider_reference=?,"
            "algorithm_version=?,status=?,capture_device=?,"
            "capture_environment=?,capture_quality=?,enrolled_at=?,"
            "expires_at=?,revoked_at=?,updated_at=?,version=?,"
            "metadata=? "
            "WHERE enrollment_id=? AND tenant_id=? AND version=?",
            (
                enrollment.identity_id,
                enrollment.biometric_type.value,
                enrollment.purpose.value,
                enrollment.consent_id,
                enrollment.template_reference,
                enrollment.provider_reference,
                enrollment.algorithm_version,
                enrollment.status.value,
                encode_capture_device(
                    enrollment.capture_device
                ),
                encode_capture_environment(
                    enrollment.capture_environment
                ),
                encode_capture_quality(
                    enrollment.capture_quality
                ),
                (
                    enrollment.enrolled_at.isoformat()
                    if enrollment.enrolled_at is not None
                    else None
                ),
                (
                    enrollment.expires_at.isoformat()
                    if enrollment.expires_at is not None
                    else None
                ),
                (
                    enrollment.revoked_at.isoformat()
                    if enrollment.revoked_at is not None
                    else None
                ),
                enrollment.updated_at.isoformat(),
                enrollment.version,
                encode_metadata(enrollment.metadata),
                enrollment.enrollment_id,
                context.tenant_id,
                expected_version,
            ),
        )

        if result.rowcount != 1:
            raise RuntimeError("CONCURRENCY_CONFLICT")

    # ------------------------------------------------------------------
    # Face verification
    # ------------------------------------------------------------------

    def add_face_verification(
        self,
        verification: FaceVerificationRecord,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_face_verifications("
            "verification_id,tenant_id,identity_id,enrollment_id,"
            "consent_id,purpose,decision,similarity_score,"
            "match_threshold,manual_review_threshold,"
            "provider_reference,algorithm_version,capture_device,"
            "capture_environment,capture_quality,verified_at,"
            "version,reason_codes,metadata"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                verification.verification_id,
                verification.tenant_id,
                verification.identity_id,
                verification.enrollment_id,
                verification.consent_id,
                verification.purpose.value,
                verification.decision.value,
                verification.similarity_score,
                verification.match_threshold,
                verification.manual_review_threshold,
                verification.provider_reference,
                verification.algorithm_version,
                encode_capture_device(
                    verification.capture_device
                ),
                encode_capture_environment(
                    verification.capture_environment
                ),
                encode_capture_quality(
                    verification.capture_quality
                ),
                verification.verified_at.isoformat(),
                verification.version,
                encode_reason_codes(
                    verification.reason_codes
                ),
                encode_metadata(verification.metadata),
            ),
        )

    def get_face_verification(
        self,
        context: RequestContext,
        verification_id: str,
    ) -> FaceVerificationRecord:
        row = self.connection.execute(
            "SELECT * FROM novaid_face_verifications "
            "WHERE verification_id=? AND tenant_id=?",
            (
                verification_id,
                context.tenant_id,
            ),
        ).fetchone()

        return face_verification_from_row(
            self._required_row(row)
        )

    # ------------------------------------------------------------------
    # Face authentication
    # ------------------------------------------------------------------

    def add_face_authentication(
        self,
        authentication: FaceAuthenticationRecord,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_face_authentications("
            "authentication_id,tenant_id,identity_id,"
            "verification_id,enrollment_id,purpose,decision,"
            "verification_decision,risk_score,"
            "authentication_strength,current_assurance_level,"
            "required_assurance_level,authenticated_at,"
            "reason_codes,metadata"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                authentication.authentication_id,
                authentication.tenant_id,
                authentication.identity_id,
                authentication.verification_id,
                authentication.enrollment_id,
                authentication.purpose.value,
                authentication.decision.value,
                authentication.verification_decision.value,
                authentication.risk_score,
                authentication.authentication_strength.value,
                authentication.current_assurance_level.value,
                authentication.required_assurance_level.value,
                authentication.authenticated_at.isoformat(),
                encode_reason_codes(
                    authentication.reason_codes
                ),
                encode_metadata(authentication.metadata),
            ),
        )

    def get_face_authentication(
        self,
        context: RequestContext,
        authentication_id: str,
    ) -> FaceAuthenticationRecord:
        row = self.connection.execute(
            "SELECT * FROM novaid_face_authentications "
            "WHERE authentication_id=? AND tenant_id=?",
            (
                authentication_id,
                context.tenant_id,
            ),
        ).fetchone()

        return face_authentication_from_row(
            self._required_row(row)
        )

    # ------------------------------------------------------------------
    # Liveness assessment
    # ------------------------------------------------------------------

    def add_liveness_assessment(
        self,
        assessment: LivenessAssessmentRecord,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_liveness_assessments("
            "assessment_id,tenant_id,identity_id,purpose,decision,"
            "attempt_number,mode,liveness_score,"
            "presentation_attack_score,provider_reference,"
            "algorithm_version,capture_device,capture_environment,"
            "capture_quality,assessed_at,detected_attack_types,"
            "reason_codes,metadata"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                assessment.assessment_id,
                assessment.tenant_id,
                assessment.identity_id,
                assessment.purpose.value,
                assessment.decision.value,
                assessment.attempt_number,
                assessment.mode.value,
                assessment.liveness_score,
                assessment.presentation_attack_score,
                assessment.provider_reference,
                assessment.algorithm_version,
                encode_capture_device(
                    assessment.capture_device
                ),
                encode_capture_environment(
                    assessment.capture_environment
                ),
                encode_capture_quality(
                    assessment.capture_quality
                ),
                assessment.assessed_at.isoformat(),
                encode_attack_types(
                    assessment.detected_attack_types
                ),
                encode_reason_codes(
                    assessment.reason_codes
                ),
                encode_metadata(assessment.metadata),
            ),
        )

    def get_liveness_assessment(
        self,
        context: RequestContext,
        assessment_id: str,
    ) -> LivenessAssessmentRecord:
        row = self.connection.execute(
            "SELECT * FROM novaid_liveness_assessments "
            "WHERE assessment_id=? AND tenant_id=?",
            (
                assessment_id,
                context.tenant_id,
            ),
        ).fetchone()

        return liveness_assessment_from_row(
            self._required_row(row)
        )
