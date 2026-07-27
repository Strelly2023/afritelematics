from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping

from ..domain import (
    AddressType,
    AssuranceLevel,
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
    VerificationStatus,
)


def _datetime_value(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def encode_legal_name(value: LegalName | None) -> str | None:
    if value is None:
        return None

    return json.dumps(
        {
            "given_names": list(value.given_names),
            "family_name": value.family_name,
            "middle_names": list(value.middle_names),
            "honorific": value.honorific,
            "suffix": value.suffix,
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def decode_legal_name(value: str | Mapping[str, Any] | None) -> LegalName | None:
    if value is None:
        return None

    payload = json.loads(value) if isinstance(value, str) else dict(value)

    return LegalName(
        given_names=tuple(payload.get("given_names", ())),
        family_name=payload["family_name"],
        middle_names=tuple(payload.get("middle_names", ())),
        honorific=payload.get("honorific"),
        suffix=payload.get("suffix"),
    )


def encode_identity_names(values: tuple[IdentityName, ...]) -> str:
    return json.dumps(
        [
            {
                "name_type": value.name_type.value,
                "display_name": value.display_name,
                "source": value.source,
                "effective_from": _datetime_value(value.effective_from),
                "effective_until": _datetime_value(value.effective_until),
            }
            for value in values
        ],
        separators=(",", ":"),
        sort_keys=True,
    )


def decode_identity_names(
    value: str | list[Mapping[str, Any]] | None,
) -> tuple[IdentityName, ...]:
    payload = json.loads(value) if isinstance(value, str) else value or []

    return tuple(
        IdentityName(
            name_type=NameType(item["name_type"]),
            display_name=item["display_name"],
            source=item.get("source"),
            effective_from=_parse_datetime(item.get("effective_from")),
            effective_until=_parse_datetime(item.get("effective_until")),
        )
        for item in payload
    )


def encode_contact_points(values: tuple[ContactPoint, ...]) -> str:
    return json.dumps(
        [
            {
                "contact_type": value.contact_type.value,
                "value": value.value,
                "verified": value.verified,
                "primary": value.primary,
            }
            for value in values
        ],
        separators=(",", ":"),
        sort_keys=True,
    )


def decode_contact_points(
    value: str | list[Mapping[str, Any]] | None,
) -> tuple[ContactPoint, ...]:
    payload = json.loads(value) if isinstance(value, str) else value or []

    return tuple(
        ContactPoint(
            contact_type=ContactPointType(item["contact_type"]),
            value=item["value"],
            verified=bool(item.get("verified", False)),
            primary=bool(item.get("primary", False)),
        )
        for item in payload
    )


def encode_addresses(values: tuple[IdentityAddress, ...]) -> str:
    return json.dumps(
        [
            {
                "address_type": value.address_type.value,
                "line1": value.line1,
                "line2": value.line2,
                "locality": value.locality,
                "region": value.region,
                "postal_code": value.postal_code,
                "country_code": value.country_code,
            }
            for value in values
        ],
        separators=(",", ":"),
        sort_keys=True,
    )


def decode_addresses(
    value: str | list[Mapping[str, Any]] | None,
) -> tuple[IdentityAddress, ...]:
    payload = json.loads(value) if isinstance(value, str) else value or []

    return tuple(
        IdentityAddress(
            address_type=AddressType(item["address_type"]),
            line1=item["line1"],
            line2=item.get("line2"),
            locality=item["locality"],
            region=item.get("region"),
            postal_code=item.get("postal_code"),
            country_code=item["country_code"],
        )
        for item in payload
    )


def encode_identifiers(values: tuple[IdentityIdentifier, ...]) -> str:
    return json.dumps(
        [
            {
                "identifier_type": value.identifier_type.value,
                "value": value.value,
                "issuer": value.issuer,
                "jurisdiction": value.jurisdiction,
                "primary": value.primary,
                "valid_from": _datetime_value(value.valid_from),
                "valid_until": _datetime_value(value.valid_until),
            }
            for value in values
        ],
        separators=(",", ":"),
        sort_keys=True,
    )


def decode_identifiers(
    value: str | list[Mapping[str, Any]] | None,
) -> tuple[IdentityIdentifier, ...]:
    payload = json.loads(value) if isinstance(value, str) else value or []

    return tuple(
        IdentityIdentifier(
            identifier_type=IdentifierType(item["identifier_type"]),
            value=item["value"],
            issuer=item.get("issuer"),
            jurisdiction=item.get("jurisdiction"),
            primary=bool(item.get("primary", False)),
            valid_from=_parse_datetime(item.get("valid_from")),
            valid_until=_parse_datetime(item.get("valid_until")),
        )
        for item in payload
    )


def encode_metadata(value: Mapping[str, Any]) -> str:
    return json.dumps(
        dict(value),
        separators=(",", ":"),
        sort_keys=True,
    )


def decode_metadata(value: str | Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    return json.loads(value) if isinstance(value, str) else dict(value)


def _row_value(
    row: Mapping[str, Any],
    key: str,
    default: Any = None,
) -> Any:
    getter = getattr(row, "get", None)
    if callable(getter):
        return getter(key, default)

    keys = row.keys() if hasattr(row, "keys") else ()
    return row[key] if key in keys else default


def identity_from_row(row: Mapping[str, Any]) -> Identity:
    return Identity(
        identity_id=str(row["identity_id"]),
        tenant_id=str(row["tenant_id"]),
        normalized_email=row["normalized_email"],
        status=IdentityStatus(row["status"]),
        created_at=_parse_datetime(str(row["created_at"])),
        updated_at=_parse_datetime(str(row["updated_at"])),
        version=int(row["version"]),
        identity_type=IdentityType(
            _row_value(row, "identity_type") or IdentityType.PERSON
        ),
        legal_name=decode_legal_name(_row_value(row, "legal_name")),
        preferred_name=_row_value(row, "preferred_name"),
        alternative_names=decode_identity_names(
            _row_value(row, "alternative_names")
        ),
        contact_points=decode_contact_points(_row_value(row, "contact_points")),
        addresses=decode_addresses(_row_value(row, "addresses")),
        identifiers=decode_identifiers(_row_value(row, "identifiers")),
        verification_status=VerificationStatus(
            _row_value(row, "verification_status")
            or VerificationStatus.UNVERIFIED
        ),
        assurance_level=AssuranceLevel(
            _row_value(row, "assurance_level") or AssuranceLevel.NID_AL0
        ),
        metadata=decode_metadata(_row_value(row, "metadata")),
    )
