"""Typed NovaID identity-core domain."""

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
    TenantMembership,
    VerificationStatus,
    identifier,
    utcnow,
)
from .tenant_boundary import (
    TenantBoundaryService,
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

__all__ = [
    "AddressType",
    "AssuranceLevel",
    "AuthenticationDecision",
    "AuthenticationPolicy",
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
    "utcnow",
]
