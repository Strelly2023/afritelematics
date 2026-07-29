"""Typed NovaID identity-core domain."""

from .document_ocr_events import (
    OCRExtractionEvent,
    ocr_extraction_event,
)
from .document_ocr_models import (
    FORBIDDEN_OCR_PAYLOAD_FIELDS,
    OCRExtractionDecision,
    OCRExtractionPolicy,
    OCRExtractionRecord,
    OCRExtractionSource,
    OCRProviderEvidence,
    required_ocr_field_types,
)
from .document_ocr_service import (
    DocumentOCRService,
    OCRExtractionResult,
)
from .document_selfie_match_events import (
    DocumentSelfieMatchEvent,
    document_selfie_match_event,
)
from .document_selfie_match_models import (
    FORBIDDEN_DOCUMENT_SELFIE_FIELDS,
    DocumentSelfieMatchDecision,
    DocumentSelfieMatchEvidence,
    DocumentSelfieMatchPolicy,
    DocumentSelfieMatchRecord,
)
from .document_selfie_match_service import (
    DocumentSelfieMatchResult,
    DocumentSelfieMatchService,
)
from .document_authenticity_events import (
    DocumentAuthenticityAssessmentEvent,
    document_authenticity_assessment_event,
)
from .document_authenticity_models import (
    FORBIDDEN_DOCUMENT_AUTHENTICITY_FIELDS,
    SEVERE_DOCUMENT_FRAUD_INDICATORS,
    DocumentAuthenticityAssessmentRecord,
    DocumentAuthenticityPolicy,
    DocumentAuthenticityProviderEvidence,
    DocumentFraudIndicator,
    DocumentSecurityFeature,
    DocumentSecurityFeatureEvidence,
)
from .document_authenticity_service import (
    DocumentAuthenticityAssessmentResult,
    DocumentAuthenticityService,
)
from .identity_verification_events import (
    IdentityVerificationOutcomeEvent,
    identity_verification_outcome_event,
)
from .identity_verification_models import (
    FORBIDDEN_IDENTITY_VERIFICATION_FIELDS,
    IdentityVerificationDecision,
    IdentityVerificationEvidence,
    IdentityVerificationPolicy,
    IdentityVerificationRecord,
    IdentityVerificationStage,
)
from .identity_verification_service import (
    IdentityVerificationResult,
    IdentityVerificationService,
)
from .document_models import (
    BarcodeEvidence,
    BarcodeType,
    DOCUMENT_STATUS_TRANSITIONS,
    DocumentAuthenticityDecision,
    DocumentAuthenticityEvidence,
    DocumentCaptureChannel,
    DocumentCaptureReference,
    DocumentExtractedData,
    DocumentSide,
    DocumentVerificationDecision,
    DocumentVerificationEvidence,
    DocumentVerificationStatus,
    FORBIDDEN_DOCUMENT_METADATA_FIELDS,
    IdentityDocument,
    IdentityDocumentType,
    MachineReadableZoneEvidence,
    MachineReadableZoneType,
    OCRField,
    OCRFieldType,
    new_document_capture_id,
    new_document_evidence_id,
    new_document_id,
)
from .biometric_events import (
    FaceEnrollmentEvent,
    face_enrollment_event,
)
from .face_enrollment_service import (
    FaceEnrollmentResult,
    FaceEnrollmentService,
    NON_TERMINAL_ENROLLMENT_STATUSES,
)
from .biometric_verification_events import (
    FaceVerificationEvent,
    face_verification_event,
)
from .biometric_verification_models import (
    FaceMatchEvidence,
    FaceVerificationDecision,
    FaceVerificationPolicy,
    FaceVerificationRecord,
)
from .face_authentication_events import (
    FaceAuthenticationEvent,
    face_authentication_event,
)
from .liveness_events import (
    LivenessAssessmentEvent,
    liveness_assessment_event,
)
from .liveness_models import (
    SEVERE_PRESENTATION_ATTACKS,
    LivenessAssessmentRecord,
    LivenessDecision,
    LivenessEvidence,
    LivenessMode,
    LivenessPolicy,
    PresentationAttackType,
)
from .liveness_service import (
    LivenessAssessmentResult,
    LivenessAssessmentService,
)
from .face_authentication_models import (
    ASSURANCE_LEVEL_ORDER,
    FaceAuthenticationContext,
    FaceAuthenticationDecision,
    FaceAuthenticationPolicy,
    FaceAuthenticationRecord,
)
from .face_authentication_service import (
    FaceAuthenticationResult,
    FaceAuthenticationService,
)
from .face_verification_service import (
    FaceVerificationResult,
    FaceVerificationService,
)
from .biometric_models import (
    BIOMETRIC_ENROLLMENT_TRANSITIONS,
    BiometricConsent,
    BiometricConsentStatus,
    BiometricEnrollment,
    BiometricEnrollmentStatus,
    BiometricPurpose,
    BiometricType,
    CaptureChannel,
    CaptureDecision,
    CaptureDevice,
    CaptureEnvironment,
    CaptureLighting,
    CaptureQuality,
    new_biometric_enrollment_id,
)
from .domain_event_codec import (
    DOMAIN_EVENT_SCHEMA_VERSION,
    encode_domain_event,
)
from .domain_events import (
    NovaIDDomainEvent,
    domain_event_subject_ids,
)
from .identity_events import (
    IdentityLifecycleEvent,
    lifecycle_event,
)
from .identity_merge_service import (
    IdentityMergeResult,
    IdentityMergeService,
)
from .merge_events import (
    IdentityMergedEvent,
    identity_merged_event,
)
from .identity_policy import (
    IdentityPolicyDecision,
    IdentityPolicyOperation,
    IdentityPolicyResult,
    IdentityPolicyService,
)
from .identity_service import (
    IdentityLifecycleResult,
    IdentityLifecycleService,
)
from .models import (
    AddressType,
    AssuranceLevel,
    AuthenticationDecision,
    AuthenticationPolicy,
    PHISHING_RESISTANT_STRENGTHS,
    AUTHENTICATION_STRENGTH_ORDER,
    AuthenticationStrength,
    ContactPoint,
    ContactPointType,
    Identity,
    IdentityAddress,
    IdentityIdentifier,
    IdentityName,
    IdentityStatus,
    IdentityType,
    IdentifierType,
    LegalName,
    NameType,
    RequestContext,
    SecurityEvent,
    Tenant,
    TenantSecurityPolicy,
    TenantSettings,
    TenantBrand,
    LegalEntity,
    TenantType,
    TenantTier,
    TenantStatus,
    TenantMembership,
    VerificationStatus,
    identifier,
    utcnow,
)
from .tenant_boundary import (
    TenantBoundaryService,
)
from .tenant_events import (
    TenantLifecycleEvent,
    tenant_lifecycle_event,
)
from .tenant_service import (
    TenantLifecycleResult,
    TenantLifecycleService,
)
from .verification_events import (
    IdentityVerificationEvent,
    verification_event,
)
from .verification_service import (
    IdentityVerificationResult,
    IdentityVerificationService,
    VERIFICATION_TRANSITIONS,
)
from .webauthn import (
    AuthenticatorPolicy,
    PasskeyMetadata,
    WebAuthnChallengeStatus,
    WebAuthnCredential,
    WebAuthnCredentialStatus,
)


# ---------------------------------------------------------------------------
# Canonical NID-P1-004 Step 4E orchestration exports
#
# NovaID already contains an earlier IdentityVerificationService in
# verification_service.py for aggregate lifecycle transitions. The imports
# below intentionally occur after all other domain imports so the public
# package surface resolves IdentityVerification* names to the complete eKYC
# orchestration implementation.
# ---------------------------------------------------------------------------
from .identity_verification_events import (
    IdentityVerificationOutcomeEvent
    as IdentityVerificationOutcomeEvent,
    identity_verification_outcome_event
    as identity_verification_outcome_event,
)
from .identity_verification_models import (
    FORBIDDEN_IDENTITY_VERIFICATION_FIELDS
    as FORBIDDEN_IDENTITY_VERIFICATION_FIELDS,
    IdentityVerificationDecision
    as IdentityVerificationDecision,
    IdentityVerificationEvidence
    as IdentityVerificationEvidence,
    IdentityVerificationPolicy
    as IdentityVerificationPolicy,
    IdentityVerificationRecord
    as IdentityVerificationRecord,
    IdentityVerificationStage
    as IdentityVerificationStage,
)
from .identity_verification_service import (
    IdentityVerificationResult
    as IdentityVerificationResult,
    IdentityVerificationService
    as IdentityVerificationService,
)
__all__ = [
    "AddressType",
    "AssuranceLevel",
    "AuthenticationDecision",
    "AuthenticationPolicy",
    "PHISHING_RESISTANT_STRENGTHS",
    "AUTHENTICATION_STRENGTH_ORDER",
    "AuthenticationStrength",
    "AuthenticatorPolicy",
    "ContactPoint",
    "ContactPointType",
    "DOMAIN_EVENT_SCHEMA_VERSION",
    "NovaIDDomainEvent",
    "domain_event_subject_ids",
    "encode_domain_event",
    "Identity",
    "IdentityAddress",
    "IdentityIdentifier",
    "IdentityLifecycleEvent",
    "IdentityLifecycleResult",
    "IdentityLifecycleService",
    "IdentityMergedEvent",
    "identity_merged_event",
    "IdentityMergeResult",
    "IdentityMergeService",
    "IdentityPolicyDecision",
    "IdentityPolicyOperation",
    "IdentityPolicyResult",
    "IdentityPolicyService",
    "IdentityName",
    "IdentityStatus",
    "IdentityVerificationEvent",
    "identity_verification_outcome_event",
    "IdentityVerificationOutcomeEvent",
    "IdentityVerificationResult",
    "IdentityVerificationService",
    "IdentityType",
    "IdentifierType",
    "LegalName",
    "NameType",
    "PasskeyMetadata",
    "RequestContext",
    "SecurityEvent",
    "Tenant",
    "TenantLifecycleEvent",
    "TenantLifecycleResult",
    "TenantLifecycleService",
    "tenant_lifecycle_event",
    "TenantSecurityPolicy",
    "TenantSettings",
    "TenantBrand",
    "LegalEntity",
    "TenantType",
    "TenantTier",
    "TenantStatus",
    "TenantMembership",
    "TenantBoundaryService",
    "VerificationStatus",
    "WebAuthnChallengeStatus",
    "WebAuthnCredential",
    "WebAuthnCredentialStatus",
    "identifier",
    "lifecycle_event",
    "VERIFICATION_TRANSITIONS",
    "verification_event",
    "utcnow",    "BIOMETRIC_ENROLLMENT_TRANSITIONS",
    "BiometricConsent",
    "BiometricConsentStatus",
    "BiometricEnrollment",
    "BiometricEnrollmentStatus",
    "BiometricPurpose",
    "BiometricType",
    "CaptureChannel",
    "CaptureDecision",
    "CaptureDevice",
    "CaptureEnvironment",
    "CaptureLighting",
    "CaptureQuality",
    "new_biometric_enrollment_id",
    "FaceEnrollmentEvent",
    "FaceEnrollmentResult",
    "FaceEnrollmentService",
    "NON_TERMINAL_ENROLLMENT_STATUSES",
    "face_enrollment_event",
    "FaceMatchEvidence",
    "FaceVerificationDecision",
    "FaceVerificationEvent",
    "FaceVerificationPolicy",
    "FaceVerificationRecord",
    "FaceVerificationResult",
    "FaceVerificationService",
    "face_verification_event",
    "ASSURANCE_LEVEL_ORDER",
    "FaceAuthenticationContext",
    "FaceAuthenticationDecision",
    "FaceAuthenticationEvent",
    "FaceAuthenticationPolicy",
    "FaceAuthenticationRecord",
    "FaceAuthenticationResult",
    "FaceAuthenticationService",
    "face_authentication_event",
    "SEVERE_PRESENTATION_ATTACKS",
    "LivenessAssessmentEvent",
    "LivenessAssessmentRecord",
    "LivenessAssessmentResult",
    "LivenessAssessmentService",
    "LivenessDecision",
    "LivenessEvidence",
    "LivenessMode",
    "LivenessPolicy",
    "PresentationAttackType",
    "liveness_assessment_event",
    "BarcodeEvidence",
    "BarcodeType",
    "DOCUMENT_STATUS_TRANSITIONS",
    "DocumentAuthenticityDecision",
    "DocumentAuthenticityEvidence",
    "DocumentCaptureChannel",
    "DocumentCaptureReference",
    "DocumentExtractedData",
    "DocumentSide",
    "DocumentVerificationDecision",
    "DocumentVerificationEvidence",
    "DocumentVerificationStatus",
    "FORBIDDEN_DOCUMENT_METADATA_FIELDS",
    "IdentityDocument",
    "IdentityDocumentType",
    "MachineReadableZoneEvidence",
    "MachineReadableZoneType",
    "OCRField",
    "OCRFieldType",
    "new_document_capture_id",
    "new_document_evidence_id",
    "new_document_id",
    "DocumentOCRService",
    "FORBIDDEN_OCR_PAYLOAD_FIELDS",
    "OCRExtractionDecision",
    "OCRExtractionEvent",
    "OCRExtractionPolicy",
    "OCRExtractionRecord",
    "OCRExtractionResult",
    "OCRExtractionSource",
    "OCRProviderEvidence",
    "ocr_extraction_event",
    "required_ocr_field_types",
    "DocumentSelfieMatchDecision",
    "DocumentSelfieMatchEvidence",
    "DocumentSelfieMatchEvent",
    "DocumentSelfieMatchPolicy",
    "DocumentSelfieMatchRecord",
    "DocumentSelfieMatchResult",
    "DocumentSelfieMatchService",
    "FORBIDDEN_DOCUMENT_SELFIE_FIELDS",
    "document_selfie_match_event",
    "DocumentAuthenticityAssessmentEvent",
    "DocumentAuthenticityAssessmentRecord",
    "DocumentAuthenticityAssessmentResult",
    "DocumentAuthenticityPolicy",
    "DocumentAuthenticityProviderEvidence",
    "DocumentAuthenticityService",
    "DocumentFraudIndicator",
    "DocumentSecurityFeature",
    "DocumentSecurityFeatureEvidence",
    "FORBIDDEN_DOCUMENT_AUTHENTICITY_FIELDS",
    "SEVERE_DOCUMENT_FRAUD_INDICATORS",
    "document_authenticity_assessment_event",
    "FORBIDDEN_IDENTITY_VERIFICATION_FIELDS",
    "IdentityVerificationDecision",
    "IdentityVerificationEvidence",
    "IdentityVerificationPolicy",
    "IdentityVerificationRecord",
    "IdentityVerificationStage",

]
