"""Canonical NovaID KYB ownership and representative linkage.

The legacy NovaID KYB surface historically represented corporate checks
as strings such as ``director`` and ``ubo``.  This module links those
checks to the canonical structured authorities introduced by NR-PROD-002E
D2 and D3.

The linkage is deliberately persistence-neutral.  Persistence and schema
parity are certified separately.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from .beneficial_ownership import (
    BeneficialOwner,
    BeneficialOwnerVerificationStatus,
)
from .business_representative import (
    BusinessRepresentative,
    BusinessRepresentativeRole,
    BusinessRepresentativeVerificationStatus,
)


_UBO_CHECKS = frozenset(
    {
        "ubo",
        "beneficial_owner",
        "beneficial_ownership",
    }
)

_REPRESENTATIVE_CHECKS = frozenset(
    {
        "director",
        "business_representative",
        "authorized_representative",
        "authorised_representative",
        "authorized_signatory",
        "authorised_signatory",
    }
)


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


def _normalized_checks(
    checks: tuple[str, ...],
) -> tuple[str, ...]:
    try:
        normalized = tuple(
            _required_text(
                check,
                "KYB_LINKAGE_INVALID_CHECK",
            ).lower()
            for check in checks
        )
    except TypeError:
        raise ValueError(
            "KYB_LINKAGE_INVALID_CHECK"
        ) from None

    if len(set(normalized)) != len(normalized):
        raise ValueError(
            "KYB_LINKAGE_DUPLICATE_CHECK"
        )

    return normalized


def _currently_effective(
    effective_from: datetime,
    effective_to: datetime | None,
    at: datetime,
) -> bool:
    if effective_from > at:
        return False

    if (
        effective_to is not None
        and effective_to <= at
    ):
        return False

    return True


@dataclass(frozen=True, slots=True)
class KYBPartyLinkage:
    """Validated structured KYB parties for a single legal entity."""

    organization_id: str
    legal_entity_id: str
    checks: tuple[str, ...]

    beneficial_owners: tuple[BeneficialOwner, ...]
    business_representatives: tuple[BusinessRepresentative, ...]

    verified_beneficial_owner_ids: tuple[str, ...]
    verified_representative_ids: tuple[str, ...]

    evaluated_at: datetime

    @property
    def structured(self) -> bool:
        return bool(
            self.beneficial_owners
            or self.business_representatives
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "structured": self.structured,
            "legal_entity_id": self.legal_entity_id,
            "beneficial_owner_ids": list(
                self.verified_beneficial_owner_ids
            ),
            "representative_ids": list(
                self.verified_representative_ids
            ),
            "evaluated_at": self.evaluated_at.isoformat(),
        }


def link_kyb_parties(
    *,
    organization_id: str,
    legal_entity_id: str,
    checks: tuple[str, ...],
    beneficial_owners: tuple[BeneficialOwner, ...] = (),
    business_representatives: tuple[
        BusinessRepresentative,
        ...
    ] = (),
    require_verified: bool = True,
    evaluated_at: datetime | None = None,
) -> KYBPartyLinkage:
    """Validate structured KYB ownership/representative assertions.

    ``organization_id`` is the existing NovaID KYB organization boundary.
    The canonical ownership and representative records must carry the
    same boundary through ``tenant_id``.

    When ``require_verified`` is true, every supplied party must already
    be VERIFIED and currently effective.

    Legacy KYB callers remain supported because this function is invoked
    only when structured party data is supplied by ``run_kyb``.
    """

    organization_id = _required_text(
        organization_id,
        "KYB_LINKAGE_ORGANIZATION_ID_REQUIRED",
    )

    legal_entity_id = _required_text(
        legal_entity_id,
        "KYB_LINKAGE_LEGAL_ENTITY_ID_REQUIRED",
    )

    checks = _normalized_checks(
        checks
    )

    now = (
        datetime.now(UTC)
        if evaluated_at is None
        else evaluated_at
    )

    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError(
            "KYB_LINKAGE_EVALUATED_AT_MUST_BE_TIMEZONE_AWARE"
        )

    now = now.astimezone(UTC)

    try:
        beneficial_owners = tuple(
            beneficial_owners
        )
        business_representatives = tuple(
            business_representatives
        )
    except TypeError:
        raise ValueError(
            "KYB_LINKAGE_INVALID_PARTY_COLLECTION"
        ) from None

    if not (
        beneficial_owners
        or business_representatives
    ):
        raise ValueError(
            "KYB_LINKAGE_STRUCTURED_PARTIES_REQUIRED"
        )

    owner_ids: list[str] = []

    for owner in beneficial_owners:
        if not isinstance(
            owner,
            BeneficialOwner,
        ):
            raise ValueError(
                "KYB_LINKAGE_INVALID_BENEFICIAL_OWNER"
            )

        if owner.tenant_id != organization_id:
            raise ValueError(
                "KYB_LINKAGE_BENEFICIAL_OWNER_TENANT_MISMATCH"
            )

        if owner.legal_entity_id != legal_entity_id:
            raise ValueError(
                "KYB_LINKAGE_BENEFICIAL_OWNER_ENTITY_MISMATCH"
            )

        if require_verified and (
            owner.verification_status
            is not BeneficialOwnerVerificationStatus.VERIFIED
        ):
            raise ValueError(
                "KYB_LINKAGE_BENEFICIAL_OWNER_NOT_VERIFIED"
            )

        if require_verified and not _currently_effective(
            owner.effective_from,
            owner.effective_to,
            now,
        ):
            raise ValueError(
                "KYB_LINKAGE_BENEFICIAL_OWNER_NOT_EFFECTIVE"
            )

        owner_ids.append(
            owner.beneficial_owner_id
        )

    representative_ids: list[str] = []

    for representative in business_representatives:
        if not isinstance(
            representative,
            BusinessRepresentative,
        ):
            raise ValueError(
                "KYB_LINKAGE_INVALID_BUSINESS_REPRESENTATIVE"
            )

        if representative.tenant_id != organization_id:
            raise ValueError(
                "KYB_LINKAGE_BUSINESS_REPRESENTATIVE_TENANT_MISMATCH"
            )

        if representative.legal_entity_id != legal_entity_id:
            raise ValueError(
                "KYB_LINKAGE_BUSINESS_REPRESENTATIVE_ENTITY_MISMATCH"
            )

        if require_verified and (
            representative.verification_status
            is not BusinessRepresentativeVerificationStatus.VERIFIED
        ):
            raise ValueError(
                "KYB_LINKAGE_BUSINESS_REPRESENTATIVE_NOT_VERIFIED"
            )

        if require_verified and not _currently_effective(
            representative.effective_from,
            representative.effective_to,
            now,
        ):
            raise ValueError(
                "KYB_LINKAGE_BUSINESS_REPRESENTATIVE_NOT_EFFECTIVE"
            )

        representative_ids.append(
            representative.representative_id
        )

    if len(set(owner_ids)) != len(owner_ids):
        raise ValueError(
            "KYB_LINKAGE_DUPLICATE_BENEFICIAL_OWNER"
        )

    if (
        len(set(representative_ids))
        != len(representative_ids)
    ):
        raise ValueError(
            "KYB_LINKAGE_DUPLICATE_BUSINESS_REPRESENTATIVE"
        )

    check_set = set(
        checks
    )

    if (
        check_set & _UBO_CHECKS
        and not beneficial_owners
    ):
        raise ValueError(
            "KYB_LINKAGE_UBO_CHECK_REQUIRES_BENEFICIAL_OWNER"
        )

    if (
        check_set & _REPRESENTATIVE_CHECKS
        and not business_representatives
    ):
        raise ValueError(
            "KYB_LINKAGE_REPRESENTATIVE_CHECK_REQUIRES_REPRESENTATIVE"
        )

    if "director" in check_set:
        if not any(
            BusinessRepresentativeRole.DIRECTOR
            in representative.roles
            for representative
            in business_representatives
        ):
            raise ValueError(
                "KYB_LINKAGE_DIRECTOR_CHECK_REQUIRES_DIRECTOR"
            )

    return KYBPartyLinkage(
        organization_id=organization_id,
        legal_entity_id=legal_entity_id,
        checks=checks,
        beneficial_owners=beneficial_owners,
        business_representatives=business_representatives,
        verified_beneficial_owner_ids=tuple(
            owner_ids
        ),
        verified_representative_ids=tuple(
            representative_ids
        ),
        evaluated_at=now,
    )


__all__ = [
    "KYBPartyLinkage",
    "link_kyb_parties",
]
