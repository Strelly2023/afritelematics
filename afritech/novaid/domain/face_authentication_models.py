from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from .biometric_models import BiometricPurpose
from .biometric_verification_models import (
    FaceVerificationDecision,
    FaceVerificationRecord,
)
from .models import (
    AssuranceLevel,
    AuthenticationStrength,
    IdentityStatus,
    utcnow,
)


class FaceAuthenticationDecision(StrEnum):
    ALLOW = "ALLOW"
    REQUIRE_STEP_UP = "REQUIRE_STEP_UP"
    REQUIRE_MANUAL_REVIEW = "REQUIRE_MANUAL_REVIEW"
    DENY = "DENY"
    LOCK_SESSION = "LOCK_SESSION"
    LOCK_IDENTITY = "LOCK_IDENTITY"


ASSURANCE_LEVEL_ORDER: dict[AssuranceLevel, int] = {
    AssuranceLevel.NID_AL0: 0,
    AssuranceLevel.NID_AL1: 10,
    AssuranceLevel.NID_AL2: 20,
    AssuranceLevel.NID_AL3: 30,
    AssuranceLevel.NID_AL4: 40,
}


@dataclass(frozen=True)
class FaceAuthenticationContext:
    verification: FaceVerificationRecord
    identity_status: IdentityStatus
    membership_active: bool
    credential_active: bool
    authentication_strength: AuthenticationStrength
    current_assurance_level: AssuranceLevel
    required_assurance_level: AssuranceLevel
    risk_score: float
    session_active: bool = True
    previous_failed_attempts: int = 0
    purpose: BiometricPurpose = BiometricPurpose.LOGIN
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "identity_status",
            IdentityStatus(self.identity_status),
        )
        object.__setattr__(
            self,
            "authentication_strength",
            AuthenticationStrength(
                self.authentication_strength
            ),
        )
        object.__setattr__(
            self,
            "current_assurance_level",
            AssuranceLevel(self.current_assurance_level),
        )
        object.__setattr__(
            self,
            "required_assurance_level",
            AssuranceLevel(self.required_assurance_level),
        )
        object.__setattr__(
            self,
            "purpose",
            BiometricPurpose(self.purpose),
        )

        if (
            isinstance(self.risk_score, bool)
            or not isinstance(self.risk_score, int | float)
            or not 0.0 <= float(self.risk_score) <= 1.0
        ):
            raise ValueError("INVALID_RISK_SCORE")

        if (
            isinstance(self.previous_failed_attempts, bool)
            or not isinstance(self.previous_failed_attempts, int)
            or self.previous_failed_attempts < 0
        ):
            raise ValueError(
                "INVALID_PREVIOUS_FAILED_ATTEMPTS"
            )

        if self.verification.purpose is not self.purpose:
            raise ValueError(
                "FACE_VERIFICATION_PURPOSE_MISMATCH"
            )

        object.__setattr__(
            self,
            "risk_score",
            float(self.risk_score),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    def assurance_satisfied(self) -> bool:
        return (
            ASSURANCE_LEVEL_ORDER[
                self.current_assurance_level
            ]
            >= ASSURANCE_LEVEL_ORDER[
                self.required_assurance_level
            ]
        )


@dataclass(frozen=True)
class FaceAuthenticationPolicy:
    session_lock_risk_threshold: float = 0.80
    identity_lock_risk_threshold: float = 0.95
    maximum_failed_attempts_before_session_lock: int = 3
    maximum_failed_attempts_before_identity_lock: int = 5
    manual_review_fails_closed: bool = True
    no_match_locks_session: bool = False

    def __post_init__(self) -> None:
        session_threshold = self._probability(
            self.session_lock_risk_threshold,
            "INVALID_SESSION_LOCK_RISK_THRESHOLD",
        )
        identity_threshold = self._probability(
            self.identity_lock_risk_threshold,
            "INVALID_IDENTITY_LOCK_RISK_THRESHOLD",
        )

        if session_threshold >= identity_threshold:
            raise ValueError(
                "INVALID_AUTHENTICATION_RISK_THRESHOLD_ORDER"
            )

        if (
            self.maximum_failed_attempts_before_session_lock
            < 1
        ):
            raise ValueError(
                "INVALID_SESSION_LOCK_ATTEMPT_THRESHOLD"
            )

        if (
            self.maximum_failed_attempts_before_identity_lock
            <= self.maximum_failed_attempts_before_session_lock
        ):
            raise ValueError(
                "INVALID_AUTHENTICATION_ATTEMPT_THRESHOLD_ORDER"
            )

        object.__setattr__(
            self,
            "session_lock_risk_threshold",
            session_threshold,
        )
        object.__setattr__(
            self,
            "identity_lock_risk_threshold",
            identity_threshold,
        )

    @staticmethod
    def _probability(
        value: float,
        error_code: str,
    ) -> float:
        if (
            isinstance(value, bool)
            or not isinstance(value, int | float)
        ):
            raise ValueError(error_code)

        normalized = float(value)

        if not 0.0 <= normalized <= 1.0:
            raise ValueError(error_code)

        return normalized


@dataclass(frozen=True)
class FaceAuthenticationRecord:
    authentication_id: str
    tenant_id: str
    identity_id: str
    verification_id: str
    enrollment_id: str
    purpose: BiometricPurpose
    decision: FaceAuthenticationDecision
    verification_decision: FaceVerificationDecision
    risk_score: float
    authentication_strength: AuthenticationStrength
    current_assurance_level: AssuranceLevel
    required_assurance_level: AssuranceLevel
    authenticated_at: datetime = field(default_factory=utcnow)
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "FACE_AUTHENTICATION_ID_REQUIRED": (
                self.authentication_id
            ),
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "FACE_VERIFICATION_ID_REQUIRED": (
                self.verification_id
            ),
            "BIOMETRIC_ENROLLMENT_ID_REQUIRED": (
                self.enrollment_id
            ),
        }

        for error_code, value in required.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(error_code)

        if (
            isinstance(self.risk_score, bool)
            or not isinstance(self.risk_score, int | float)
            or not 0.0 <= float(self.risk_score) <= 1.0
        ):
            raise ValueError("INVALID_RISK_SCORE")

        object.__setattr__(
            self,
            "authentication_id",
            self.authentication_id.strip(),
        )
        object.__setattr__(
            self,
            "tenant_id",
            self.tenant_id.strip(),
        )
        object.__setattr__(
            self,
            "identity_id",
            self.identity_id.strip(),
        )
        object.__setattr__(
            self,
            "verification_id",
            self.verification_id.strip(),
        )
        object.__setattr__(
            self,
            "enrollment_id",
            self.enrollment_id.strip(),
        )
        object.__setattr__(
            self,
            "purpose",
            BiometricPurpose(self.purpose),
        )
        object.__setattr__(
            self,
            "decision",
            FaceAuthenticationDecision(self.decision),
        )
        object.__setattr__(
            self,
            "verification_decision",
            FaceVerificationDecision(
                self.verification_decision
            ),
        )
        object.__setattr__(
            self,
            "authentication_strength",
            AuthenticationStrength(
                self.authentication_strength
            ),
        )
        object.__setattr__(
            self,
            "current_assurance_level",
            AssuranceLevel(self.current_assurance_level),
        )
        object.__setattr__(
            self,
            "required_assurance_level",
            AssuranceLevel(self.required_assurance_level),
        )
        object.__setattr__(
            self,
            "risk_score",
            float(self.risk_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            tuple(
                dict.fromkeys(
                    code.strip().upper()
                    for code in self.reason_codes
                    if isinstance(code, str)
                    and code.strip()
                )
            ),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )
