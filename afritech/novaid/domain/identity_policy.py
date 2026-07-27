from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .models import (
    IdentityStatus,
    VerificationStatus,
)


class IdentityPolicyOperation(StrEnum):
    VIEW_IDENTITY = "VIEW_IDENTITY"
    UPDATE_PROFILE = "UPDATE_PROFILE"
    MANAGE_VERIFICATION = "MANAGE_VERIFICATION"
    MANAGE_LIFECYCLE = "MANAGE_LIFECYCLE"
    MERGE_IDENTITIES = "MERGE_IDENTITIES"
    DELETE_IDENTITY = "DELETE_IDENTITY"


class IdentityPolicyDecision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_STEP_UP = "REQUIRE_STEP_UP"


@dataclass(frozen=True)
class IdentityPolicyResult:
    decision: IdentityPolicyDecision
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class IdentityPolicyService:
    _ADMIN_ROLES = frozenset(
        {
            "ADMIN",
            "SECURITY_ADMIN",
            "IDENTITY_ADMIN",
        }
    )

    _VERIFICATION_ROLES = frozenset(
        {
            "ADMIN",
            "SECURITY_ADMIN",
            "IDENTITY_ADMIN",
            "VERIFIER",
        }
    )

    _AUTHENTICATED_STRENGTHS = frozenset(
        {
            "PASSWORD",
            "PASSWORD_OTP",
            "MFA",
            "PHISHING_RESISTANT",
        }
    )

    def evaluate(
        self,
        *,
        operation: IdentityPolicyOperation,
        actor_role: str,
        authentication_strength: str,
        same_identity: bool,
        identity_status: IdentityStatus,
        verification_status: VerificationStatus,
    ) -> IdentityPolicyResult:
        role = actor_role.strip().upper()
        strength = authentication_strength.strip().upper()

        if (
            not role
            or not strength
            or operation not in IdentityPolicyOperation
        ):
            return self._deny("MALFORMED_POLICY_CONTEXT")

        if strength not in self._AUTHENTICATED_STRENGTHS:
            return self._deny("UNSUPPORTED_AUTHENTICATION_STRENGTH")

        if identity_status is IdentityStatus.DELETED:
            return self._deny("IDENTITY_DELETED")

        if operation is IdentityPolicyOperation.VIEW_IDENTITY:
            if same_identity:
                return self._allow("SELF_SERVICE_VIEW")

            if role in self._ADMIN_ROLES or role == "OBSERVER":
                return self._allow("AUTHORIZED_IDENTITY_VIEW")

            return self._deny("IDENTITY_VIEW_DENIED")

        if operation is IdentityPolicyOperation.UPDATE_PROFILE:
            if identity_status is IdentityStatus.DISABLED:
                return self._deny("IDENTITY_DISABLED")

            if same_identity:
                if strength == "PASSWORD":
                    return self._step_up("PROFILE_UPDATE_STEP_UP_REQUIRED")
                return self._allow("SELF_SERVICE_PROFILE_UPDATE")

            if role in self._ADMIN_ROLES:
                return self._allow("ADMIN_PROFILE_UPDATE")

            return self._deny("PROFILE_UPDATE_DENIED")

        if operation is IdentityPolicyOperation.MANAGE_VERIFICATION:
            if role not in self._VERIFICATION_ROLES:
                return self._deny("VERIFICATION_MANAGEMENT_DENIED")

            if strength == "PASSWORD":
                return self._step_up(
                    "VERIFICATION_MANAGEMENT_STEP_UP_REQUIRED"
                )

            return self._allow("VERIFICATION_MANAGEMENT_ALLOWED")

        if operation is IdentityPolicyOperation.MANAGE_LIFECYCLE:
            if role not in self._ADMIN_ROLES:
                return self._deny("LIFECYCLE_MANAGEMENT_DENIED")

            if strength == "PASSWORD":
                return self._step_up(
                    "LIFECYCLE_MANAGEMENT_STEP_UP_REQUIRED"
                )

            return self._allow("LIFECYCLE_MANAGEMENT_ALLOWED")

        if operation is IdentityPolicyOperation.MERGE_IDENTITIES:
            if role not in self._ADMIN_ROLES:
                return self._deny("IDENTITY_MERGE_DENIED")

            if strength != "PHISHING_RESISTANT":
                return self._step_up("IDENTITY_MERGE_STEP_UP_REQUIRED")

            if verification_status is not VerificationStatus.VERIFIED:
                return self._deny("IDENTITY_MERGE_REQUIRES_VERIFIED_TARGET")

            return self._allow("IDENTITY_MERGE_ALLOWED")

        if operation is IdentityPolicyOperation.DELETE_IDENTITY:
            if role not in self._ADMIN_ROLES:
                return self._deny("IDENTITY_DELETE_DENIED")

            if strength != "PHISHING_RESISTANT":
                return self._step_up("IDENTITY_DELETE_STEP_UP_REQUIRED")

            if identity_status is not IdentityStatus.DISABLED:
                return self._deny("IDENTITY_DELETE_REQUIRES_DISABLED_STATE")

            return self._allow("IDENTITY_DELETE_ALLOWED")

        return self._deny("UNSUPPORTED_POLICY_OPERATION")

    @staticmethod
    def _allow(reason: str) -> IdentityPolicyResult:
        return IdentityPolicyResult(
            decision=IdentityPolicyDecision.ALLOW,
            reason_codes=(reason,),
        )

    @staticmethod
    def _deny(reason: str) -> IdentityPolicyResult:
        return IdentityPolicyResult(
            decision=IdentityPolicyDecision.DENY,
            reason_codes=(reason,),
        )

    @staticmethod
    def _step_up(reason: str) -> IdentityPolicyResult:
        return IdentityPolicyResult(
            decision=IdentityPolicyDecision.REQUIRE_STEP_UP,
            reason_codes=(reason,),
        )
