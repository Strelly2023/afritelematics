"""Canonical NovaID beneficial-ownership domain authority.

This module formalizes beneficial-owner / UBO semantics that already
exist in the NovaID KYB surface.  It intentionally contains no external
registry integration, persistence implementation, or KYB orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum


class BeneficialOwnerControlBasis(str, Enum):
    """How a person exercises beneficial ownership or effective control."""

    OWNERSHIP = "OWNERSHIP"
    VOTING_RIGHTS = "VOTING_RIGHTS"
    BOARD_CONTROL = "BOARD_CONTROL"
    OTHER_CONTROL = "OTHER_CONTROL"


class BeneficialOwnerVerificationStatus(str, Enum):
    """Fail-closed verification state for a beneficial-owner assertion."""

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


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


def _optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(
            "BENEFICIAL_OWNER_INVALID_OPTIONAL_TEXT"
        )

    normalized = value.strip()
    return normalized or None


def _timestamp(
    value: datetime,
    error_code: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(error_code)

    if value.tzinfo is None:
        raise ValueError(error_code)

    return value.astimezone(UTC)


def _ownership_percentage(
    value: Decimal | int | str | None,
) -> Decimal | None:
    if value is None:
        return None

    if isinstance(value, bool):
        raise ValueError(
            "BENEFICIAL_OWNER_INVALID_OWNERSHIP_PERCENTAGE"
        )

    try:
        percentage = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(
            "BENEFICIAL_OWNER_INVALID_OWNERSHIP_PERCENTAGE"
        ) from None

    if not percentage.is_finite():
        raise ValueError(
            "BENEFICIAL_OWNER_INVALID_OWNERSHIP_PERCENTAGE"
        )

    if percentage < Decimal("0") or percentage > Decimal("100"):
        raise ValueError(
            "BENEFICIAL_OWNER_OWNERSHIP_PERCENTAGE_OUT_OF_RANGE"
        )

    return percentage


@dataclass(frozen=True, slots=True)
class BeneficialOwner:
    """Immutable beneficial-owner assertion for one legal entity.

    ``tenant_id`` is explicit so an ownership assertion cannot be
    detached from its authorization boundary.

    ``identity_id`` references the canonical NovaID identity representing
    the natural person.  ``legal_entity_id`` references the business /
    legal entity being controlled.

    External registry/provider verification is represented only by
    evidence/provider references.  This object never claims that such an
    external verification has actually occurred.
    """

    beneficial_owner_id: str
    tenant_id: str
    legal_entity_id: str
    identity_id: str

    control_bases: tuple[BeneficialOwnerControlBasis, ...]

    ownership_percentage: Decimal | int | str | None = None

    verification_status: BeneficialOwnerVerificationStatus = (
        BeneficialOwnerVerificationStatus.PENDING
    )

    effective_from: datetime = datetime.min.replace(
        tzinfo=UTC
    )
    effective_to: datetime | None = None

    provider_reference: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "beneficial_owner_id",
            _required_text(
                self.beneficial_owner_id,
                "BENEFICIAL_OWNER_ID_REQUIRED",
            ),
        )

        object.__setattr__(
            self,
            "tenant_id",
            _required_text(
                self.tenant_id,
                "BENEFICIAL_OWNER_TENANT_ID_REQUIRED",
            ),
        )

        object.__setattr__(
            self,
            "legal_entity_id",
            _required_text(
                self.legal_entity_id,
                "BENEFICIAL_OWNER_LEGAL_ENTITY_ID_REQUIRED",
            ),
        )

        object.__setattr__(
            self,
            "identity_id",
            _required_text(
                self.identity_id,
                "BENEFICIAL_OWNER_IDENTITY_ID_REQUIRED",
            ),
        )

        try:
            control_bases = tuple(
                (
                    item
                    if isinstance(
                        item,
                        BeneficialOwnerControlBasis,
                    )
                    else BeneficialOwnerControlBasis(
                        str(item).strip().upper()
                    )
                )
                for item in self.control_bases
            )
        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "BENEFICIAL_OWNER_INVALID_CONTROL_BASIS"
            ) from None

        if not control_bases:
            raise ValueError(
                "BENEFICIAL_OWNER_CONTROL_BASIS_REQUIRED"
            )

        if len(set(control_bases)) != len(control_bases):
            raise ValueError(
                "BENEFICIAL_OWNER_DUPLICATE_CONTROL_BASIS"
            )

        object.__setattr__(
            self,
            "control_bases",
            control_bases,
        )

        percentage = _ownership_percentage(
            self.ownership_percentage
        )

        if (
            BeneficialOwnerControlBasis.OWNERSHIP
            in control_bases
            and (
                percentage is None
                or percentage <= Decimal("0")
            )
        ):
            raise ValueError(
                "BENEFICIAL_OWNER_OWNERSHIP_PERCENTAGE_REQUIRED"
            )

        object.__setattr__(
            self,
            "ownership_percentage",
            percentage,
        )

        try:
            status = (
                self.verification_status
                if isinstance(
                    self.verification_status,
                    BeneficialOwnerVerificationStatus,
                )
                else BeneficialOwnerVerificationStatus(
                    str(
                        self.verification_status
                    ).strip().upper()
                )
            )
        except ValueError:
            raise ValueError(
                "BENEFICIAL_OWNER_INVALID_VERIFICATION_STATUS"
            ) from None

        object.__setattr__(
            self,
            "verification_status",
            status,
        )

        effective_from = _timestamp(
            self.effective_from,
            "BENEFICIAL_OWNER_EFFECTIVE_FROM_REQUIRED",
        )

        effective_to = (
            None
            if self.effective_to is None
            else _timestamp(
                self.effective_to,
                "BENEFICIAL_OWNER_INVALID_EFFECTIVE_TO",
            )
        )

        if (
            effective_to is not None
            and effective_to <= effective_from
        ):
            raise ValueError(
                "BENEFICIAL_OWNER_EFFECTIVE_TO_MUST_FOLLOW_EFFECTIVE_FROM"
            )

        object.__setattr__(
            self,
            "effective_from",
            effective_from,
        )

        object.__setattr__(
            self,
            "effective_to",
            effective_to,
        )

        object.__setattr__(
            self,
            "provider_reference",
            _optional_text(
                self.provider_reference
            ),
        )

        try:
            evidence_refs = tuple(
                _required_text(
                    item,
                    "BENEFICIAL_OWNER_INVALID_EVIDENCE_REFERENCE",
                )
                for item in self.evidence_refs
            )
        except TypeError:
            raise ValueError(
                "BENEFICIAL_OWNER_INVALID_EVIDENCE_REFERENCE"
            ) from None

        if len(set(evidence_refs)) != len(evidence_refs):
            raise ValueError(
                "BENEFICIAL_OWNER_DUPLICATE_EVIDENCE_REFERENCE"
            )

        object.__setattr__(
            self,
            "evidence_refs",
            evidence_refs,
        )


__all__ = [
    "BeneficialOwner",
    "BeneficialOwnerControlBasis",
    "BeneficialOwnerVerificationStatus",
]
