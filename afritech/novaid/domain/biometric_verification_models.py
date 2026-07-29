from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from .biometric_models import (
    BiometricPurpose,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
)
from .models import utcnow


class FaceVerificationDecision(StrEnum):
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass(frozen=True)
class FaceVerificationPolicy:
    match_threshold: float = 0.85
    manual_review_threshold: float = 0.65
    minimum_capture_quality_score: float = 0.70
    require_device_integrity: bool = False
    deny_emulators: bool = True
    deny_compromised_devices: bool = True

    def __post_init__(self) -> None:
        match_threshold = self._probability(
            self.match_threshold,
            "INVALID_FACE_MATCH_THRESHOLD",
        )
        review_threshold = self._probability(
            self.manual_review_threshold,
            "INVALID_FACE_REVIEW_THRESHOLD",
        )
        quality_threshold = self._probability(
            self.minimum_capture_quality_score,
            "INVALID_FACE_CAPTURE_THRESHOLD",
        )

        if review_threshold >= match_threshold:
            raise ValueError(
                "INVALID_FACE_VERIFICATION_THRESHOLD_ORDER"
            )

        object.__setattr__(
            self,
            "match_threshold",
            match_threshold,
        )
        object.__setattr__(
            self,
            "manual_review_threshold",
            review_threshold,
        )
        object.__setattr__(
            self,
            "minimum_capture_quality_score",
            quality_threshold,
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

    def decide(
        self,
        similarity_score: float,
    ) -> FaceVerificationDecision:
        score = self._probability(
            similarity_score,
            "INVALID_FACE_SIMILARITY_SCORE",
        )

        if score >= self.match_threshold:
            return FaceVerificationDecision.MATCH

        if score >= self.manual_review_threshold:
            return FaceVerificationDecision.MANUAL_REVIEW

        return FaceVerificationDecision.NO_MATCH


@dataclass(frozen=True)
class FaceMatchEvidence:
    provider_reference: str
    algorithm_version: str
    similarity_score: float
    provider_decision_reference: str | None = None
    confidence_score: float | None = None
    evaluated_at: datetime = field(default_factory=utcnow)
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        provider_reference = self._required_text(
            self.provider_reference,
            "BIOMETRIC_PROVIDER_REFERENCE_REQUIRED",
        )
        algorithm_version = self._required_text(
            self.algorithm_version,
            "BIOMETRIC_ALGORITHM_VERSION_REQUIRED",
        )
        decision_reference = self._optional_text(
            self.provider_decision_reference
        )
        similarity_score = self._probability(
            self.similarity_score,
            "INVALID_FACE_SIMILARITY_SCORE",
        )

        confidence_score = self.confidence_score

        if confidence_score is not None:
            confidence_score = self._probability(
                confidence_score,
                "INVALID_FACE_CONFIDENCE_SCORE",
            )

        reason_codes = tuple(
            dict.fromkeys(
                reason.strip().upper()
                for reason in self.reason_codes
                if isinstance(reason, str)
                and reason.strip()
            )
        )

        object.__setattr__(
            self,
            "provider_reference",
            provider_reference,
        )
        object.__setattr__(
            self,
            "algorithm_version",
            algorithm_version,
        )
        object.__setattr__(
            self,
            "provider_decision_reference",
            decision_reference,
        )
        object.__setattr__(
            self,
            "similarity_score",
            similarity_score,
        )
        object.__setattr__(
            self,
            "confidence_score",
            confidence_score,
        )
        object.__setattr__(
            self,
            "reason_codes",
            reason_codes,
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    @staticmethod
    def _required_text(
        value: str,
        error_code: str,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(error_code)

        normalized = value.strip()

        if not normalized:
            raise ValueError(error_code)

        return normalized

    @staticmethod
    def _optional_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

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
class FaceVerificationRecord:
    verification_id: str
    tenant_id: str
    identity_id: str
    enrollment_id: str
    consent_id: str
    purpose: BiometricPurpose
    decision: FaceVerificationDecision
    similarity_score: float
    match_threshold: float
    manual_review_threshold: float
    provider_reference: str
    algorithm_version: str
    capture_device: CaptureDevice
    capture_environment: CaptureEnvironment
    capture_quality: CaptureQuality
    verified_at: datetime = field(default_factory=utcnow)
    version: int = 1
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "FACE_VERIFICATION_ID_REQUIRED": self.verification_id,
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "BIOMETRIC_ENROLLMENT_ID_REQUIRED": self.enrollment_id,
            "BIOMETRIC_CONSENT_ID_REQUIRED": self.consent_id,
            "BIOMETRIC_PROVIDER_REFERENCE_REQUIRED": (
                self.provider_reference
            ),
            "BIOMETRIC_ALGORITHM_VERSION_REQUIRED": (
                self.algorithm_version
            ),
        }

        for error_code, value in required.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(error_code)

        if self.version < 1:
            raise ValueError("INVALID_AGGREGATE_VERSION")

        if not 0.0 <= float(self.similarity_score) <= 1.0:
            raise ValueError("INVALID_FACE_SIMILARITY_SCORE")

        object.__setattr__(
            self,
            "verification_id",
            self.verification_id.strip(),
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
            "enrollment_id",
            self.enrollment_id.strip(),
        )
        object.__setattr__(
            self,
            "consent_id",
            self.consent_id.strip(),
        )
        object.__setattr__(
            self,
            "purpose",
            BiometricPurpose(self.purpose),
        )
        object.__setattr__(
            self,
            "decision",
            FaceVerificationDecision(self.decision),
        )
        object.__setattr__(
            self,
            "provider_reference",
            self.provider_reference.strip(),
        )
        object.__setattr__(
            self,
            "algorithm_version",
            self.algorithm_version.strip(),
        )
        object.__setattr__(
            self,
            "reason_codes",
            tuple(self.reason_codes),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )
