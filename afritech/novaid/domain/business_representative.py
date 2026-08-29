"""Canonical NovaID business-representative domain authority.

This module formalizes the natural person who is authorized to act for a
legal entity during KYB and subsequent governed business operations.

It deliberately does not:
- verify an external company registry;
- create authorization policy;
- persist representatives;
- alter the existing NovaID KYB service;
- imply that a representative is a beneficial owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


class BusinessRepresentativeRole(str, Enum):
    """Canonical capacity in which a person represents a legal entity."""

    DIRECTOR = "DIRECTOR"
    COMPANY_OFFICER = "COMPANY_OFFICER"
    AUTHORIZED_SIGNATORY = "AUTHORIZED_SIGNATORY"
    TRUSTEE = "TRUSTEE"
    PARTNER = "PARTNER"
    OTHER_AUTHORIZED_REPRESENTATIVE = (
        "OTHER_AUTHORIZED_REPRESENTATIVE"
    )


class BusinessRepresentativeVerificationStatus(str, Enum):
    """Fail-closed verification state of representative authority."""

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
            "BUSINESS_REPRESENTATIVE_INVALID_OPTIONAL_TEXT"
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


@dataclass(frozen=True, slots=True)
class BusinessRepresentative:
    """Immutable legal-entity representative assertion.

    ``tenant_id`` preserves the authorization boundary.

    ``identity_id`` references the canonical NovaID identity for the
    natural person.

    ``legal_entity_id`` references the legal entity represented.

    ``roles`` describe the capacity in which the person may represent the
    entity.  This object records representative authority; it does not
    itself grant application/API permissions.

    ``authority_reference`` may identify a board resolution, registry
    extract, mandate, power of attorney, corporate resolution, or another
    governed authority record. External truth remains evidence-only until
    an approved provider or registry has actually been executed.
    """

    representative_id: str
    tenant_id: str
    legal_entity_id: str
    identity_id: str

    roles: tuple[BusinessRepresentativeRole, ...]

    verification_status: BusinessRepresentativeVerificationStatus = (
        BusinessRepresentativeVerificationStatus.PENDING
    )

    effective_from: datetime = datetime.min.replace(
        tzinfo=UTC
    )
    effective_to: datetime | None = None

    authority_reference: str | None = None
    provider_reference: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "representative_id",
            _required_text(
                self.representative_id,
                "BUSINESS_REPRESENTATIVE_ID_REQUIRED",
            ),
        )

        object.__setattr__(
            self,
            "tenant_id",
            _required_text(
                self.tenant_id,
                "BUSINESS_REPRESENTATIVE_TENANT_ID_REQUIRED",
            ),
        )

        object.__setattr__(
            self,
            "legal_entity_id",
            _required_text(
                self.legal_entity_id,
                "BUSINESS_REPRESENTATIVE_LEGAL_ENTITY_ID_REQUIRED",
            ),
        )

        object.__setattr__(
            self,
            "identity_id",
            _required_text(
                self.identity_id,
                "BUSINESS_REPRESENTATIVE_IDENTITY_ID_REQUIRED",
            ),
        )

        try:
            roles = tuple(
                (
                    role
                    if isinstance(
                        role,
                        BusinessRepresentativeRole,
                    )
                    else BusinessRepresentativeRole(
                        str(role).strip().upper()
                    )
                )
                for role in self.roles
            )
        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "BUSINESS_REPRESENTATIVE_INVALID_ROLE"
            ) from None

        if not roles:
            raise ValueError(
                "BUSINESS_REPRESENTATIVE_ROLE_REQUIRED"
            )

        if len(set(roles)) != len(roles):
            raise ValueError(
                "BUSINESS_REPRESENTATIVE_DUPLICATE_ROLE"
            )

        object.__setattr__(
            self,
            "roles",
            roles,
        )

        try:
            status = (
                self.verification_status
                if isinstance(
                    self.verification_status,
                    BusinessRepresentativeVerificationStatus,
                )
                else BusinessRepresentativeVerificationStatus(
                    str(
                        self.verification_status
                    ).strip().upper()
                )
            )
        except ValueError:
            raise ValueError(
                "BUSINESS_REPRESENTATIVE_INVALID_VERIFICATION_STATUS"
            ) from None

        object.__setattr__(
            self,
            "verification_status",
            status,
        )

        effective_from = _timestamp(
            self.effective_from,
            "BUSINESS_REPRESENTATIVE_EFFECTIVE_FROM_REQUIRED",
        )

        effective_to = (
            None
            if self.effective_to is None
            else _timestamp(
                self.effective_to,
                "BUSINESS_REPRESENTATIVE_INVALID_EFFECTIVE_TO",
            )
        )

        if (
            effective_to is not None
            and effective_to <= effective_from
        ):
            raise ValueError(
                "BUSINESS_REPRESENTATIVE_EFFECTIVE_TO_MUST_FOLLOW_EFFECTIVE_FROM"
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
            "authority_reference",
            _optional_text(
                self.authority_reference
            ),
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
                    "BUSINESS_REPRESENTATIVE_INVALID_EVIDENCE_REFERENCE",
                )
                for item in self.evidence_refs
            )
        except TypeError:
            raise ValueError(
                "BUSINESS_REPRESENTATIVE_INVALID_EVIDENCE_REFERENCE"
            ) from None

        if len(set(evidence_refs)) != len(evidence_refs):
            raise ValueError(
                "BUSINESS_REPRESENTATIVE_DUPLICATE_EVIDENCE_REFERENCE"
            )

        object.__setattr__(
            self,
            "evidence_refs",
            evidence_refs,
        )


__all__ = [
    "BusinessRepresentative",
    "BusinessRepresentativeRole",
    "BusinessRepresentativeVerificationStatus",
]
