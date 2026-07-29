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


class LivenessMode(StrEnum):
    PASSIVE = "PASSIVE"
    ACTIVE = "ACTIVE"
    HYBRID = "HYBRID"


class LivenessDecision(StrEnum):
    PASS = "PASS"
    RECAPTURE = "RECAPTURE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    FAIL = "FAIL"
    LOCK_SESSION = "LOCK_SESSION"


class PresentationAttackType(StrEnum):
    NONE = "NONE"
    PRINTED_PHOTO = "PRINTED_PHOTO"
    SCREEN_REPLAY = "SCREEN_REPLAY"
    VIDEO_REPLAY = "VIDEO_REPLAY"
    MASK = "MASK"
    DEEPFAKE = "DEEPFAKE"
    CAMERA_INJECTION = "CAMERA_INJECTION"
    VIRTUAL_CAMERA = "VIRTUAL_CAMERA"
    SYNTHETIC_MEDIA = "SYNTHETIC_MEDIA"
    UNKNOWN = "UNKNOWN"


SEVERE_PRESENTATION_ATTACKS = frozenset(
    {
        PresentationAttackType.DEEPFAKE,
        PresentationAttackType.CAMERA_INJECTION,
        PresentationAttackType.VIRTUAL_CAMERA,
        PresentationAttackType.SYNTHETIC_MEDIA,
    }
)


@dataclass(frozen=True)
class LivenessEvidence:
    provider_reference: str
    algorithm_version: str
    mode: LivenessMode
    liveness_score: float
    presentation_attack_score: float
    depth_score: float | None = None
    motion_score: float | None = None
    texture_score: float | None = None
    challenge_completion_score: float | None = None
    detected_attack_types: frozenset[
        PresentationAttackType
    ] = frozenset()
    provider_decision_reference: str | None = None
    evaluated_at: datetime = field(default_factory=utcnow)
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "provider_reference",
            self._required_text(
                self.provider_reference,
                "LIVENESS_PROVIDER_REFERENCE_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "algorithm_version",
            self._required_text(
                self.algorithm_version,
                "LIVENESS_ALGORITHM_VERSION_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "mode",
            LivenessMode(self.mode),
        )
        object.__setattr__(
            self,
            "liveness_score",
            self._probability(
                self.liveness_score,
                "INVALID_LIVENESS_SCORE",
            ),
        )
        object.__setattr__(
            self,
            "presentation_attack_score",
            self._probability(
                self.presentation_attack_score,
                "INVALID_PRESENTATION_ATTACK_SCORE",
            ),
        )

        for field_name in (
            "depth_score",
            "motion_score",
            "texture_score",
            "challenge_completion_score",
        ):
            value = getattr(self, field_name)

            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    self._probability(
                        value,
                        "INVALID_LIVENESS_COMPONENT_SCORE",
                    ),
                )

        attacks = frozenset(
            PresentationAttackType(value)
            for value in self.detected_attack_types
        )

        if (
            PresentationAttackType.NONE in attacks
            and len(attacks) > 1
        ):
            raise ValueError(
                "INCONSISTENT_PRESENTATION_ATTACK_TYPES"
            )

        object.__setattr__(
            self,
            "detected_attack_types",
            attacks,
        )
        object.__setattr__(
            self,
            "provider_decision_reference",
            self._optional_text(
                self.provider_decision_reference
            ),
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

    def presentation_attack_detected(self) -> bool:
        return any(
            attack is not PresentationAttackType.NONE
            for attack in self.detected_attack_types
        )

    def severe_attack_detected(self) -> bool:
        return bool(
            self.detected_attack_types
            & SEVERE_PRESENTATION_ATTACKS
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
class LivenessPolicy:
    pass_threshold: float = 0.85
    manual_review_threshold: float = 0.65
    recapture_threshold: float = 0.45
    maximum_presentation_attack_score: float = 0.30
    minimum_capture_quality_score: float = 0.70
    maximum_attempts: int = 3
    require_device_integrity: bool = False
    deny_emulators: bool = True
    deny_compromised_devices: bool = True
    lock_on_severe_attack: bool = True
    fail_on_any_detected_attack: bool = True

    def __post_init__(self) -> None:
        pass_threshold = self._probability(
            self.pass_threshold,
            "INVALID_LIVENESS_PASS_THRESHOLD",
        )
        review_threshold = self._probability(
            self.manual_review_threshold,
            "INVALID_LIVENESS_REVIEW_THRESHOLD",
        )
        recapture_threshold = self._probability(
            self.recapture_threshold,
            "INVALID_LIVENESS_RECAPTURE_THRESHOLD",
        )
        attack_threshold = self._probability(
            self.maximum_presentation_attack_score,
            "INVALID_PRESENTATION_ATTACK_THRESHOLD",
        )
        quality_threshold = self._probability(
            self.minimum_capture_quality_score,
            "INVALID_LIVENESS_CAPTURE_THRESHOLD",
        )

        if not (
            recapture_threshold
            < review_threshold
            < pass_threshold
        ):
            raise ValueError(
                "INVALID_LIVENESS_THRESHOLD_ORDER"
            )

        if (
            isinstance(self.maximum_attempts, bool)
            or not isinstance(self.maximum_attempts, int)
            or self.maximum_attempts < 1
        ):
            raise ValueError(
                "INVALID_LIVENESS_MAXIMUM_ATTEMPTS"
            )

        object.__setattr__(
            self,
            "pass_threshold",
            pass_threshold,
        )
        object.__setattr__(
            self,
            "manual_review_threshold",
            review_threshold,
        )
        object.__setattr__(
            self,
            "recapture_threshold",
            recapture_threshold,
        )
        object.__setattr__(
            self,
            "maximum_presentation_attack_score",
            attack_threshold,
        )
        object.__setattr__(
            self,
            "minimum_capture_quality_score",
            quality_threshold,
        )

    def decide(
        self,
        *,
        evidence: LivenessEvidence,
        attempt_number: int,
    ) -> tuple[LivenessDecision, tuple[str, ...]]:
        if (
            isinstance(attempt_number, bool)
            or not isinstance(attempt_number, int)
            or attempt_number < 1
        ):
            raise ValueError(
                "INVALID_LIVENESS_ATTEMPT_NUMBER"
            )

        if attempt_number > self.maximum_attempts:
            return (
                LivenessDecision.LOCK_SESSION,
                ("LIVENESS_ATTEMPT_LIMIT_EXCEEDED",),
            )

        if (
            self.lock_on_severe_attack
            and evidence.severe_attack_detected()
        ):
            return (
                LivenessDecision.LOCK_SESSION,
                ("SEVERE_PRESENTATION_ATTACK_DETECTED",),
            )

        if evidence.presentation_attack_detected():
            if self.fail_on_any_detected_attack:
                return (
                    LivenessDecision.FAIL,
                    ("PRESENTATION_ATTACK_DETECTED",),
                )

            return (
                LivenessDecision.MANUAL_REVIEW,
                ("PRESENTATION_ATTACK_REVIEW_REQUIRED",),
            )

        if (
            evidence.presentation_attack_score
            > self.maximum_presentation_attack_score
        ):
            return (
                LivenessDecision.MANUAL_REVIEW,
                ("PRESENTATION_ATTACK_SCORE_ELEVATED",),
            )

        if evidence.liveness_score >= self.pass_threshold:
            return (
                LivenessDecision.PASS,
                ("LIVENESS_CONTROLS_SATISFIED",),
            )

        if (
            evidence.liveness_score
            >= self.manual_review_threshold
        ):
            return (
                LivenessDecision.MANUAL_REVIEW,
                ("LIVENESS_MANUAL_REVIEW_REQUIRED",),
            )

        if (
            evidence.liveness_score
            >= self.recapture_threshold
        ):
            return (
                LivenessDecision.RECAPTURE,
                ("LIVENESS_RECAPTURE_REQUIRED",),
            )

        return (
            LivenessDecision.FAIL,
            ("LIVENESS_SCORE_TOO_LOW",),
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
class LivenessAssessmentRecord:
    assessment_id: str
    tenant_id: str
    identity_id: str
    purpose: BiometricPurpose
    decision: LivenessDecision
    attempt_number: int
    mode: LivenessMode
    liveness_score: float
    presentation_attack_score: float
    provider_reference: str
    algorithm_version: str
    capture_device: CaptureDevice
    capture_environment: CaptureEnvironment
    capture_quality: CaptureQuality
    assessed_at: datetime = field(default_factory=utcnow)
    detected_attack_types: frozenset[
        PresentationAttackType
    ] = frozenset()
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "LIVENESS_ASSESSMENT_ID_REQUIRED": (
                self.assessment_id
            ),
            "TENANT_ID_REQUIRED": self.tenant_id,
            "IDENTITY_ID_REQUIRED": self.identity_id,
            "LIVENESS_PROVIDER_REFERENCE_REQUIRED": (
                self.provider_reference
            ),
            "LIVENESS_ALGORITHM_VERSION_REQUIRED": (
                self.algorithm_version
            ),
        }

        for error_code, value in required.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(error_code)

        if self.attempt_number < 1:
            raise ValueError(
                "INVALID_LIVENESS_ATTEMPT_NUMBER"
            )

        object.__setattr__(
            self,
            "assessment_id",
            self.assessment_id.strip(),
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
            "purpose",
            BiometricPurpose(self.purpose),
        )
        object.__setattr__(
            self,
            "decision",
            LivenessDecision(self.decision),
        )
        object.__setattr__(
            self,
            "mode",
            LivenessMode(self.mode),
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
            "detected_attack_types",
            frozenset(
                PresentationAttackType(value)
                for value in self.detected_attack_types
            ),
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
