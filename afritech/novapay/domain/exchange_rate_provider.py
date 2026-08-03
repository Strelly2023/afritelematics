from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Self
from urllib.parse import urlsplit, urlunsplit


_MAX_IDENTIFIER_LENGTH = 128
_MAX_NAME_LENGTH = 200
_MAX_DESCRIPTION_LENGTH = 1000
_MAX_METADATA_KEY_LENGTH = 128
_MAX_METADATA_STRING_LENGTH = 1000
_MAX_ENDPOINT_LENGTH = 2048
_MAX_CAPABILITY_ITEMS = 500

_PROHIBITED_METADATA_KEYS = frozenset(
    {
        "access_token",
        "account_number",
        "api_key",
        "authorization",
        "card_number",
        "client_secret",
        "credential",
        "credentials",
        "cvv",
        "password",
        "pin",
        "private_key",
        "refresh_token",
        "secret",
        "security_code",
        "token",
    }
)


def _normalize_required_text(
    value: object,
    *,
    field_name: str,
    maximum_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = " ".join(value.split())

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    if len(normalized) > maximum_length:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{maximum_length} characters"
        )

    return normalized


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
    maximum_length: int,
) -> str | None:
    if value is None:
        return None

    return _normalize_required_text(
        value,
        field_name=field_name,
        maximum_length=maximum_length,
    )


def _normalize_non_negative_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")

    if value < 0:
        raise ValueError(
            f"{field_name} must be greater than or equal to 0"
        )

    return value


def _normalize_positive_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")

    if value <= 0:
        raise ValueError(
            f"{field_name} must be greater than 0"
        )

    return value


def _normalize_ratio(
    value: object,
    *,
    field_name: str,
) -> Decimal:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be numeric")

    if isinstance(value, float):
        raise TypeError(
            f"{field_name} must not be constructed from float"
        )

    try:
        normalized = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError) as exc:
        raise ValueError(
            f"{field_name} must be a valid decimal"
        ) from exc

    if not normalized.is_finite():
        raise ValueError(f"{field_name} must be finite")

    if normalized < Decimal("0") or normalized > Decimal("1"):
        raise ValueError(
            f"{field_name} must be between 0 and 1"
        )

    return normalized


def _normalize_slug(
    value: object,
    *,
    field_name: str,
    maximum_length: int = 128,
) -> str:
    normalized = _normalize_required_text(
        value,
        field_name=field_name,
        maximum_length=maximum_length,
    ).lower()

    normalized = (
        normalized
        .replace("-", "_")
        .replace(" ", "_")
    )

    if not all(
        character.isalnum() or character == "_"
        for character in normalized
    ):
        raise ValueError(
            f"{field_name} contains unsupported characters"
        )

    return normalized


def _normalize_string_tuple(
    values: object,
    *,
    field_name: str,
    uppercase: bool = False,
) -> tuple[str, ...]:
    if values is None:
        return ()

    if isinstance(values, str):
        raise TypeError(
            f"{field_name} must be an iterable of strings"
        )

    try:
        raw_values = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(
            f"{field_name} must be iterable"
        ) from exc

    if len(raw_values) > _MAX_CAPABILITY_ITEMS:
        raise ValueError(
            f"{field_name} contains too many values"
        )

    normalized: list[str] = []

    for raw_value in raw_values:
        item = _normalize_required_text(
            raw_value,
            field_name=f"{field_name} item",
            maximum_length=128,
        )

        if uppercase:
            item = item.upper()

        normalized.append(item)

    if len(normalized) != len(set(normalized)):
        raise ValueError(
            f"{field_name} contains duplicate values"
        )

    return tuple(sorted(normalized))


def _normalize_metadata_value(
    value: object,
    *,
    field_name: str,
) -> Any:
    if value is None or isinstance(value, (bool, int)):
        return value

    if isinstance(value, float):
        raise TypeError(
            f"{field_name} must not contain float values"
        )

    if isinstance(value, str):
        if len(value) > _MAX_METADATA_STRING_LENGTH:
            raise ValueError(
                f"{field_name} string value is too long"
            )

        return value

    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(
                f"{field_name} decimal value must be finite"
            )

        return str(value)

    if isinstance(value, tuple):
        return tuple(
            _normalize_metadata_value(
                item,
                field_name=field_name,
            )
            for item in value
        )

    if isinstance(value, list):
        return tuple(
            _normalize_metadata_value(
                item,
                field_name=field_name,
            )
            for item in value
        )

    if isinstance(value, Mapping):
        return MappingProxyType(
            _normalize_metadata_mapping(value)
        )

    raise TypeError(
        f"{field_name} contains an unsupported value type"
    )


def _normalize_metadata_mapping(
    value: Mapping[object, object],
) -> dict[str, Any]:
    normalized: dict[str, Any] = {}

    for raw_key, raw_value in value.items():
        key = _normalize_slug(
            raw_key,
            field_name="provider metadata key",
            maximum_length=_MAX_METADATA_KEY_LENGTH,
        )

        if key in _PROHIBITED_METADATA_KEYS:
            raise ValueError(
                "provider metadata contains prohibited "
                f"sensitive key: {key}"
            )

        if key in normalized:
            raise ValueError(
                "duplicate normalized provider metadata "
                f"key: {key}"
            )

        normalized[key] = _normalize_metadata_value(
            raw_value,
            field_name=f"provider metadata {key}",
        )

    return dict(sorted(normalized.items()))


def _normalize_datetime(
    value: object,
    *,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _normalize_version(
    value: object,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "exchange-rate provider version must be an integer"
        )

    if value < 1:
        raise ValueError(
            "exchange-rate provider version must be "
            "greater than or equal to 1"
        )

    return value


class ExchangeRateProviderStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEGRADED = "degraded"
    SUSPENDED = "suspended"
    RETIRED = "retired"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_slug(
            value,
            field_name="exchange-rate provider status",
        )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                "unsupported exchange-rate provider status: "
                f"{normalized}"
            ) from exc


class ExchangeRateProviderType(str, Enum):
    CENTRAL_BANK = "central_bank"
    COMMERCIAL_BANK = "commercial_bank"
    MARKET_DATA_VENDOR = "market_data_vendor"
    PAYMENT_NETWORK = "payment_network"
    MONEY_TRANSFER_OPERATOR = "money_transfer_operator"
    MOBILE_MONEY_OPERATOR = "mobile_money_operator"
    DIGITAL_ASSET_EXCHANGE = "digital_asset_exchange"
    INTERNAL_TREASURY = "internal_treasury"
    GOVERNMENT_AUTHORITY = "government_authority"
    AGGREGATOR = "aggregator"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_slug(
            value,
            field_name="exchange-rate provider type",
        )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                "unsupported exchange-rate provider type: "
                f"{normalized}"
            ) from exc


class RateSourceStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEGRADED = "degraded"
    SUSPENDED = "suspended"
    RETIRED = "retired"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_slug(
            value,
            field_name="rate-source status",
        )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported rate-source status: {normalized}"
            ) from exc


class RateSourceType(str, Enum):
    SPOT = "spot"
    MID_MARKET = "mid_market"
    CENTRAL_BANK_REFERENCE = "central_bank_reference"
    CARD_NETWORK = "card_network"
    BANK_WHOLESALE = "bank_wholesale"
    REMITTANCE = "remittance"
    MOBILE_MONEY = "mobile_money"
    INTERNAL_TREASURY = "internal_treasury"
    MANUAL = "manual"
    COMPOSITE = "composite"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_slug(
            value,
            field_name="rate-source type",
        )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported rate-source type: {normalized}"
            ) from exc


class ProviderTrustLevel(str, Enum):
    UNVERIFIED = "unverified"
    OBSERVED = "observed"
    VERIFIED = "verified"
    TRUSTED = "trusted"
    AUTHORITATIVE = "authoritative"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_slug(
            value,
            field_name="provider trust level",
        )

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported provider trust level: {normalized}"
            ) from exc


@dataclass(frozen=True, slots=True, order=True)
class ExchangeRateProviderId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required_text(
                self.value,
                field_name="exchange-rate provider id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_required_text(
                value,
                field_name="exchange-rate provider id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class RateSourceId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required_text(
                self.value,
                field_name="rate-source id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_required_text(
                value,
                field_name="rate-source id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ProviderName:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required_text(
                self.value,
                field_name="provider name",
                maximum_length=_MAX_NAME_LENGTH,
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_required_text(
                value,
                field_name="provider name",
                maximum_length=_MAX_NAME_LENGTH,
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ProviderEndpoint:
    url: str
    description: str | None = None

    def __post_init__(self) -> None:
        normalized_url = _normalize_required_text(
            self.url,
            field_name="provider endpoint url",
            maximum_length=_MAX_ENDPOINT_LENGTH,
        )

        parsed = urlsplit(normalized_url)

        if parsed.scheme.lower() != "https":
            raise ValueError(
                "provider endpoint must use HTTPS"
            )

        if not parsed.hostname:
            raise ValueError(
                "provider endpoint must contain a hostname"
            )

        if parsed.username or parsed.password:
            raise ValueError(
                "provider endpoint must not contain credentials"
            )

        if parsed.query:
            raise ValueError(
                "provider endpoint must not contain query parameters"
            )

        if parsed.fragment:
            raise ValueError(
                "provider endpoint must not contain a fragment"
            )

        hostname = parsed.hostname.lower()
        port = parsed.port

        netloc = hostname

        if port is not None:
            netloc = f"{hostname}:{port}"

        path = parsed.path.rstrip("/")

        canonical_url = urlunsplit(
            (
                "https",
                netloc,
                path,
                "",
                "",
            )
        )

        object.__setattr__(
            self,
            "url",
            canonical_url,
        )
        object.__setattr__(
            self,
            "description",
            _normalize_optional_text(
                self.description,
                field_name="provider endpoint description",
                maximum_length=_MAX_DESCRIPTION_LENGTH,
            ),
        )

    @classmethod
    def of(
        cls,
        value: object,
        *,
        description: object = None,
    ) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            url=_normalize_required_text(
                value,
                field_name="provider endpoint url",
                maximum_length=_MAX_ENDPOINT_LENGTH,
            ),
            description=_normalize_optional_text(
                description,
                field_name="provider endpoint description",
                maximum_length=_MAX_DESCRIPTION_LENGTH,
            ),
        )

    @property
    def hostname(self) -> str:
        parsed = urlsplit(self.url)

        assert parsed.hostname is not None
        return parsed.hostname

    def canonical_dict(self) -> dict[str, str | None]:
        return {
            "url": self.url,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    supported_currency_pairs: tuple[str, ...] = ()
    supported_rate_source_types: tuple[RateSourceType, ...] = ()
    supports_streaming: bool = False
    supports_historical_rates: bool = False
    supports_inverse_rates: bool = False
    maximum_staleness_seconds: int = 300
    expected_latency_ms: int | None = None
    expected_reliability: Decimal | None = None

    def __post_init__(self) -> None:
        normalized_pairs = _normalize_string_tuple(
            self.supported_currency_pairs,
            field_name="supported currency pairs",
            uppercase=True,
        )

        for pair in normalized_pairs:
            if pair.count("/") != 1:
                raise ValueError(
                    "supported currency pair must use BASE/QUOTE format"
                )

            base, quote = pair.split("/", maxsplit=1)

            if (
                len(base) != 3
                or len(quote) != 3
                or not base.isalpha()
                or not quote.isalpha()
            ):
                raise ValueError(
                    "supported currency pair must use "
                    "three-letter currency codes"
                )

        try:
            raw_source_types = tuple(
                self.supported_rate_source_types
            )
        except TypeError as exc:
            raise TypeError(
                "supported rate-source types must be iterable"
            ) from exc

        normalized_source_types = tuple(
            sorted(
                {
                    RateSourceType.parse(value)
                    for value in raw_source_types
                },
                key=lambda value: value.value,
            )
        )

        for field_name in (
            "supports_streaming",
            "supports_historical_rates",
            "supports_inverse_rates",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(
                    f"{field_name} must be a boolean"
                )

        object.__setattr__(
            self,
            "supported_currency_pairs",
            normalized_pairs,
        )
        object.__setattr__(
            self,
            "supported_rate_source_types",
            normalized_source_types,
        )
        object.__setattr__(
            self,
            "maximum_staleness_seconds",
            _normalize_positive_integer(
                self.maximum_staleness_seconds,
                field_name="maximum staleness seconds",
            ),
        )
        object.__setattr__(
            self,
            "expected_latency_ms",
            (
                None
                if self.expected_latency_ms is None
                else _normalize_positive_integer(
                    self.expected_latency_ms,
                    field_name="expected latency ms",
                )
            ),
        )
        object.__setattr__(
            self,
            "expected_reliability",
            (
                None
                if self.expected_reliability is None
                else _normalize_ratio(
                    self.expected_reliability,
                    field_name="expected reliability",
                )
            ),
        )

    @classmethod
    def of(cls, value: object = None) -> Self:
        if isinstance(value, cls):
            return value

        if value is None:
            return cls()

        if not isinstance(value, Mapping):
            raise TypeError(
                "provider capabilities must be a mapping"
            )

        return cls(
            supported_currency_pairs=tuple(
                value.get("supported_currency_pairs", ())
            ),
            supported_rate_source_types=tuple(
                value.get(
                    "supported_rate_source_types",
                    (),
                )
            ),
            supports_streaming=value.get(
                "supports_streaming",
                False,
            ),
            supports_historical_rates=value.get(
                "supports_historical_rates",
                False,
            ),
            supports_inverse_rates=value.get(
                "supports_inverse_rates",
                False,
            ),
            maximum_staleness_seconds=value.get(
                "maximum_staleness_seconds",
                300,
            ),
            expected_latency_ms=value.get(
                "expected_latency_ms"
            ),
            expected_reliability=value.get(
                "expected_reliability"
            ),
        )

    def supports_pair(self, value: object) -> bool:
        normalized = _normalize_required_text(
            value,
            field_name="currency pair",
            maximum_length=16,
        ).upper()

        return normalized in self.supported_currency_pairs

    def supports_source_type(
        self,
        value: object,
    ) -> bool:
        normalized = RateSourceType.parse(value)

        return normalized in self.supported_rate_source_types

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "supported_currency_pairs": list(
                self.supported_currency_pairs
            ),
            "supported_rate_source_types": [
                value.value
                for value in self.supported_rate_source_types
            ],
            "supports_streaming": self.supports_streaming,
            "supports_historical_rates": (
                self.supports_historical_rates
            ),
            "supports_inverse_rates": (
                self.supports_inverse_rates
            ),
            "maximum_staleness_seconds": (
                self.maximum_staleness_seconds
            ),
            "expected_latency_ms": self.expected_latency_ms,
            "expected_reliability": (
                None
                if self.expected_reliability is None
                else str(self.expected_reliability)
            ),
        }


@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    values: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.values, Mapping):
            raise TypeError(
                "provider metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "values",
            MappingProxyType(
                _normalize_metadata_mapping(self.values)
            ),
        )

    @classmethod
    def of(cls, value: object = None) -> Self:
        if isinstance(value, cls):
            return value

        if value is None:
            return cls()

        if not isinstance(value, Mapping):
            raise TypeError(
                "provider metadata must be a mapping"
            )

        return cls(value)

    def with_updates(
        self,
        updates: Mapping[object, object],
    ) -> Self:
        if not isinstance(updates, Mapping):
            raise TypeError(
                "provider metadata updates must be a mapping"
            )

        merged = dict(self.values)
        merged.update(updates)

        return type(self)(merged)

    def canonical_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(self.values))


@dataclass(frozen=True, slots=True)
class RateSourceMetadata:
    values: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.values, Mapping):
            raise TypeError(
                "rate-source metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "values",
            MappingProxyType(
                _normalize_metadata_mapping(self.values)
            ),
        )

    @classmethod
    def of(cls, value: object = None) -> Self:
        if isinstance(value, cls):
            return value

        if value is None:
            return cls()

        if not isinstance(value, Mapping):
            raise TypeError(
                "rate-source metadata must be a mapping"
            )

        return cls(value)

    def with_updates(
        self,
        updates: Mapping[object, object],
    ) -> Self:
        if not isinstance(updates, Mapping):
            raise TypeError(
                "rate-source metadata updates must be a mapping"
            )

        merged = dict(self.values)
        merged.update(updates)

        return type(self)(merged)

    def canonical_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(self.values))



@dataclass(frozen=True, slots=True, order=True)
class ExchangeRateProviderRegistryId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required_text(
                self.value,
                field_name=(
                    "exchange-rate provider registry id"
                ),
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_required_text(
                value,
                field_name=(
                    "exchange-rate provider registry id"
                ),
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            )
        )

    def canonical(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ExchangeRateProviderRegistry:
    """Immutable registry of providers and provider-owned sources.

    The registry offers deterministic lookup and validates canonical
    ownership relationships. It does not acquire, calculate, select,
    publish, lock, convert, persist, or settle exchange rates.
    """

    registry_id: ExchangeRateProviderRegistryId
    providers: tuple[ExchangeRateProvider, ...]
    rate_sources: tuple[RateSource, ...]
    metadata: ProviderMetadata
    created_at: datetime
    updated_at: datetime
    version: int = 1

    def __post_init__(self) -> None:
        normalized_registry_id = (
            ExchangeRateProviderRegistryId.of(
                self.registry_id
            )
        )

        try:
            normalized_providers = tuple(self.providers)
        except TypeError as exc:
            raise TypeError(
                "provider registry providers must be iterable"
            ) from exc

        try:
            normalized_sources = tuple(self.rate_sources)
        except TypeError as exc:
            raise TypeError(
                "provider registry rate sources must be iterable"
            ) from exc

        for provider in normalized_providers:
            if not isinstance(
                provider,
                ExchangeRateProvider,
            ):
                raise TypeError(
                    "provider registry providers must contain "
                    "ExchangeRateProvider values"
                )

        for source in normalized_sources:
            if not isinstance(source, RateSource):
                raise TypeError(
                    "provider registry rate sources must contain "
                    "RateSource values"
                )

        provider_ids = [
            provider.provider_id.value
            for provider in normalized_providers
        ]

        if len(provider_ids) != len(set(provider_ids)):
            raise ValueError(
                "provider registry contains duplicate provider ids"
            )

        source_ids = [
            source.rate_source_id.value
            for source in normalized_sources
        ]

        if len(source_ids) != len(set(source_ids)):
            raise ValueError(
                "provider registry contains duplicate "
                "rate-source ids"
            )

        known_provider_ids = set(provider_ids)

        orphan_sources = sorted(
            source.rate_source_id.value
            for source in normalized_sources
            if source.provider_id.value
            not in known_provider_ids
        )

        if orphan_sources:
            raise ValueError(
                "provider registry contains rate sources "
                "without registered providers: "
                + ", ".join(orphan_sources)
            )

        normalized_providers = tuple(
            sorted(
                normalized_providers,
                key=lambda value: (
                    value.provider_id.value
                ),
            )
        )

        normalized_sources = tuple(
            sorted(
                normalized_sources,
                key=lambda value: (
                    value.priority,
                    value.provider_id.value,
                    value.rate_source_id.value,
                ),
            )
        )

        normalized_metadata = ProviderMetadata.of(
            self.metadata
        )
        normalized_created_at = _normalize_datetime(
            self.created_at,
            field_name="provider registry created_at",
        )
        normalized_updated_at = _normalize_datetime(
            self.updated_at,
            field_name="provider registry updated_at",
        )
        normalized_version = _normalize_version(
            self.version
        )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "provider registry updated_at must not be "
                "earlier than created_at"
            )

        object.__setattr__(
            self,
            "registry_id",
            normalized_registry_id,
        )
        object.__setattr__(
            self,
            "providers",
            normalized_providers,
        )
        object.__setattr__(
            self,
            "rate_sources",
            normalized_sources,
        )
        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
        )
        object.__setattr__(
            self,
            "created_at",
            normalized_created_at,
        )
        object.__setattr__(
            self,
            "updated_at",
            normalized_updated_at,
        )
        object.__setattr__(
            self,
            "version",
            normalized_version,
        )

    @classmethod
    def create(
        cls,
        *,
        registry_id: object,
        created_at: datetime,
        providers: object = (),
        rate_sources: object = (),
        metadata: object = None,
    ) -> Self:
        normalized_created_at = _normalize_datetime(
            created_at,
            field_name="provider registry created_at",
        )

        try:
            normalized_providers = tuple(providers)
        except TypeError as exc:
            raise TypeError(
                "provider registry providers must be iterable"
            ) from exc

        try:
            normalized_sources = tuple(rate_sources)
        except TypeError as exc:
            raise TypeError(
                "provider registry rate sources must be iterable"
            ) from exc

        return cls(
            registry_id=(
                ExchangeRateProviderRegistryId.of(
                    registry_id
                )
            ),
            providers=normalized_providers,
            rate_sources=normalized_sources,
            metadata=ProviderMetadata.of(metadata),
            created_at=normalized_created_at,
            updated_at=normalized_created_at,
            version=1,
        )

    def _with_change(
        self,
        *,
        occurred_at: datetime,
        **changes: object,
    ) -> Self:
        normalized_occurred_at = _normalize_datetime(
            occurred_at,
            field_name=(
                "provider registry change occurred_at"
            ),
        )

        if normalized_occurred_at < self.updated_at:
            raise ValueError(
                "provider registry change occurred_at must "
                "not be earlier than updated_at"
            )

        return replace(
            self,
            updated_at=normalized_occurred_at,
            version=self.version + 1,
            **changes,
        )

    def get_provider(
        self,
        provider_id: object,
    ) -> ExchangeRateProvider | None:
        normalized_id = ExchangeRateProviderId.of(
            provider_id
        )

        return next(
            (
                provider
                for provider in self.providers
                if provider.provider_id == normalized_id
            ),
            None,
        )

    def require_provider(
        self,
        provider_id: object,
    ) -> ExchangeRateProvider:
        provider = self.get_provider(provider_id)

        if provider is None:
            normalized_id = ExchangeRateProviderId.of(
                provider_id
            )
            raise LookupError(
                "exchange-rate provider not found: "
                f"{normalized_id.value}"
            )

        return provider

    def get_rate_source(
        self,
        rate_source_id: object,
    ) -> RateSource | None:
        normalized_id = RateSourceId.of(
            rate_source_id
        )

        return next(
            (
                source
                for source in self.rate_sources
                if source.rate_source_id == normalized_id
            ),
            None,
        )

    def require_rate_source(
        self,
        rate_source_id: object,
    ) -> RateSource:
        source = self.get_rate_source(rate_source_id)

        if source is None:
            normalized_id = RateSourceId.of(
                rate_source_id
            )
            raise LookupError(
                "rate source not found: "
                f"{normalized_id.value}"
            )

        return source

    def providers_by_status(
        self,
        status: object,
    ) -> tuple[ExchangeRateProvider, ...]:
        normalized_status = ExchangeRateProviderStatus.parse(
            status
        )

        return tuple(
            provider
            for provider in self.providers
            if provider.status is normalized_status
        )

    def providers_by_type(
        self,
        provider_type: object,
    ) -> tuple[ExchangeRateProvider, ...]:
        normalized_type = ExchangeRateProviderType.parse(
            provider_type
        )

        return tuple(
            provider
            for provider in self.providers
            if provider.provider_type is normalized_type
        )

    def providers_by_trust_level(
        self,
        trust_level: object,
    ) -> tuple[ExchangeRateProvider, ...]:
        normalized_trust = ProviderTrustLevel.parse(
            trust_level
        )

        return tuple(
            provider
            for provider in self.providers
            if provider.trust_level is normalized_trust
        )

    def sources_for_provider(
        self,
        provider_id: object,
    ) -> tuple[RateSource, ...]:
        normalized_id = ExchangeRateProviderId.of(
            provider_id
        )

        return tuple(
            source
            for source in self.rate_sources
            if source.provider_id == normalized_id
        )

    def sources_by_status(
        self,
        status: object,
    ) -> tuple[RateSource, ...]:
        normalized_status = RateSourceStatus.parse(status)

        return tuple(
            source
            for source in self.rate_sources
            if source.status is normalized_status
        )

    def sources_by_type(
        self,
        source_type: object,
    ) -> tuple[RateSource, ...]:
        normalized_type = RateSourceType.parse(
            source_type
        )

        return tuple(
            source
            for source in self.rate_sources
            if source.source_type is normalized_type
        )

    def sources_by_trust_level(
        self,
        trust_level: object,
    ) -> tuple[RateSource, ...]:
        normalized_trust = ProviderTrustLevel.parse(
            trust_level
        )

        return tuple(
            source
            for source in self.rate_sources
            if source.trust_level is normalized_trust
        )

    def sources_supporting_pair(
        self,
        currency_pair: object,
    ) -> tuple[RateSource, ...]:
        return tuple(
            source
            for source in self.rate_sources
            if source.supports_pair(currency_pair)
        )

    def active_sources_supporting_pair(
        self,
        currency_pair: object,
    ) -> tuple[RateSource, ...]:
        return tuple(
            source
            for source in self.rate_sources
            if source.status is RateSourceStatus.ACTIVE
            and source.supports_pair(currency_pair)
        )

    def register_provider(
        self,
        provider: ExchangeRateProvider,
        *,
        occurred_at: datetime,
    ) -> Self:
        if not isinstance(
            provider,
            ExchangeRateProvider,
        ):
            raise TypeError(
                "provider must be an ExchangeRateProvider"
            )

        if self.get_provider(provider.provider_id) is not None:
            raise ValueError(
                "provider registry already contains provider: "
                f"{provider.provider_id.value}"
            )

        return self._with_change(
            occurred_at=occurred_at,
            providers=self.providers + (provider,),
        )

    def update_provider(
        self,
        provider: ExchangeRateProvider,
        *,
        occurred_at: datetime,
    ) -> Self:
        if not isinstance(
            provider,
            ExchangeRateProvider,
        ):
            raise TypeError(
                "provider must be an ExchangeRateProvider"
            )

        current = self.get_provider(provider.provider_id)

        if current is None:
            raise LookupError(
                "exchange-rate provider not found: "
                f"{provider.provider_id.value}"
            )

        if provider == current:
            raise ValueError(
                "provider registry update must change provider"
            )

        updated = tuple(
            provider
            if item.provider_id == provider.provider_id
            else item
            for item in self.providers
        )

        return self._with_change(
            occurred_at=occurred_at,
            providers=updated,
        )

    def register_rate_source(
        self,
        source: RateSource,
        *,
        occurred_at: datetime,
    ) -> Self:
        if not isinstance(source, RateSource):
            raise TypeError(
                "source must be a RateSource"
            )

        if self.get_rate_source(
            source.rate_source_id
        ) is not None:
            raise ValueError(
                "provider registry already contains rate source: "
                f"{source.rate_source_id.value}"
            )

        if self.get_provider(source.provider_id) is None:
            raise ValueError(
                "rate source provider is not registered: "
                f"{source.provider_id.value}"
            )

        return self._with_change(
            occurred_at=occurred_at,
            rate_sources=self.rate_sources + (source,),
        )

    def update_rate_source(
        self,
        source: RateSource,
        *,
        occurred_at: datetime,
    ) -> Self:
        if not isinstance(source, RateSource):
            raise TypeError(
                "source must be a RateSource"
            )

        current = self.get_rate_source(
            source.rate_source_id
        )

        if current is None:
            raise LookupError(
                "rate source not found: "
                f"{source.rate_source_id.value}"
            )

        if self.get_provider(source.provider_id) is None:
            raise ValueError(
                "rate source provider is not registered: "
                f"{source.provider_id.value}"
            )

        if source == current:
            raise ValueError(
                "provider registry update must change rate source"
            )

        updated = tuple(
            source
            if item.rate_source_id == source.rate_source_id
            else item
            for item in self.rate_sources
        )

        return self._with_change(
            occurred_at=occurred_at,
            rate_sources=updated,
        )

    def update_metadata(
        self,
        metadata: object,
        *,
        occurred_at: datetime,
    ) -> Self:
        normalized_metadata = ProviderMetadata.of(metadata)

        if normalized_metadata == self.metadata:
            raise ValueError(
                "provider registry metadata update must "
                "change metadata"
            )

        return self._with_change(
            occurred_at=occurred_at,
            metadata=normalized_metadata,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "registry_id": self.registry_id.value,
            "providers": [
                provider.canonical_dict()
                for provider in self.providers
            ],
            "rate_sources": [
                source.canonical_dict()
                for source in self.rate_sources
            ],
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }



@dataclass(frozen=True, slots=True)
class RateSource:
    """Immutable definition of one provider-owned FX-rate source.

    A RateSource describes provenance, priority, trust, supported
    currency pairs, and freshness requirements. It does not fetch,
    publish, calculate, select, lock, convert, or persist rates.
    """

    rate_source_id: RateSourceId
    provider_id: ExchangeRateProviderId
    source_type: RateSourceType
    status: RateSourceStatus
    trust_level: ProviderTrustLevel
    priority: int
    supported_currency_pairs: tuple[str, ...]
    maximum_staleness_seconds: int
    expected_latency_ms: int | None
    expected_reliability: Decimal | None
    metadata: RateSourceMetadata
    created_at: datetime
    updated_at: datetime
    version: int = 1

    def __post_init__(self) -> None:
        normalized_rate_source_id = RateSourceId.of(
            self.rate_source_id
        )
        normalized_provider_id = ExchangeRateProviderId.of(
            self.provider_id
        )
        normalized_source_type = RateSourceType.parse(
            self.source_type
        )
        normalized_status = RateSourceStatus.parse(
            self.status
        )
        normalized_trust_level = ProviderTrustLevel.parse(
            self.trust_level
        )
        normalized_priority = _normalize_non_negative_integer(
            self.priority,
            field_name="rate-source priority",
        )
        normalized_pairs = _normalize_string_tuple(
            self.supported_currency_pairs,
            field_name=(
                "rate-source supported currency pairs"
            ),
            uppercase=True,
        )

        for pair in normalized_pairs:
            if pair.count("/") != 1:
                raise ValueError(
                    "rate-source currency pair must use "
                    "BASE/QUOTE format"
                )

            base, quote = pair.split("/", maxsplit=1)

            if (
                len(base) != 3
                or len(quote) != 3
                or not base.isalpha()
                or not quote.isalpha()
            ):
                raise ValueError(
                    "rate-source currency pair must use "
                    "three-letter currency codes"
                )

        normalized_staleness = _normalize_positive_integer(
            self.maximum_staleness_seconds,
            field_name=(
                "rate-source maximum staleness seconds"
            ),
        )
        normalized_latency = (
            None
            if self.expected_latency_ms is None
            else _normalize_positive_integer(
                self.expected_latency_ms,
                field_name=(
                    "rate-source expected latency ms"
                ),
            )
        )
        normalized_reliability = (
            None
            if self.expected_reliability is None
            else _normalize_ratio(
                self.expected_reliability,
                field_name=(
                    "rate-source expected reliability"
                ),
            )
        )
        normalized_metadata = RateSourceMetadata.of(
            self.metadata
        )
        normalized_created_at = _normalize_datetime(
            self.created_at,
            field_name="rate-source created_at",
        )
        normalized_updated_at = _normalize_datetime(
            self.updated_at,
            field_name="rate-source updated_at",
        )
        normalized_version = _normalize_version(
            self.version
        )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "rate-source updated_at must not be earlier "
                "than created_at"
            )

        object.__setattr__(
            self,
            "rate_source_id",
            normalized_rate_source_id,
        )
        object.__setattr__(
            self,
            "provider_id",
            normalized_provider_id,
        )
        object.__setattr__(
            self,
            "source_type",
            normalized_source_type,
        )
        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "trust_level",
            normalized_trust_level,
        )
        object.__setattr__(
            self,
            "priority",
            normalized_priority,
        )
        object.__setattr__(
            self,
            "supported_currency_pairs",
            normalized_pairs,
        )
        object.__setattr__(
            self,
            "maximum_staleness_seconds",
            normalized_staleness,
        )
        object.__setattr__(
            self,
            "expected_latency_ms",
            normalized_latency,
        )
        object.__setattr__(
            self,
            "expected_reliability",
            normalized_reliability,
        )
        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
        )
        object.__setattr__(
            self,
            "created_at",
            normalized_created_at,
        )
        object.__setattr__(
            self,
            "updated_at",
            normalized_updated_at,
        )
        object.__setattr__(
            self,
            "version",
            normalized_version,
        )

    @classmethod
    def create(
        cls,
        *,
        rate_source_id: object,
        provider_id: object,
        source_type: object,
        created_at: datetime,
        status: object = RateSourceStatus.DRAFT,
        trust_level: object = ProviderTrustLevel.UNVERIFIED,
        priority: object = 100,
        supported_currency_pairs: object = (),
        maximum_staleness_seconds: object = 300,
        expected_latency_ms: object = None,
        expected_reliability: object = None,
        metadata: object = None,
    ) -> Self:
        normalized_created_at = _normalize_datetime(
            created_at,
            field_name="rate-source created_at",
        )

        return cls(
            rate_source_id=RateSourceId.of(
                rate_source_id
            ),
            provider_id=ExchangeRateProviderId.of(
                provider_id
            ),
            source_type=RateSourceType.parse(
                source_type
            ),
            status=RateSourceStatus.parse(
                status
            ),
            trust_level=ProviderTrustLevel.parse(
                trust_level
            ),
            priority=_normalize_non_negative_integer(
                priority,
                field_name="rate-source priority",
            ),
            supported_currency_pairs=(
                _normalize_string_tuple(
                    supported_currency_pairs,
                    field_name=(
                        "rate-source supported currency pairs"
                    ),
                    uppercase=True,
                )
            ),
            maximum_staleness_seconds=(
                _normalize_positive_integer(
                    maximum_staleness_seconds,
                    field_name=(
                        "rate-source maximum staleness seconds"
                    ),
                )
            ),
            expected_latency_ms=(
                None
                if expected_latency_ms is None
                else _normalize_positive_integer(
                    expected_latency_ms,
                    field_name=(
                        "rate-source expected latency ms"
                    ),
                )
            ),
            expected_reliability=(
                None
                if expected_reliability is None
                else _normalize_ratio(
                    expected_reliability,
                    field_name=(
                        "rate-source expected reliability"
                    ),
                )
            ),
            metadata=RateSourceMetadata.of(metadata),
            created_at=normalized_created_at,
            updated_at=normalized_created_at,
            version=1,
        )


    def _with_change(
        self,
        *,
        occurred_at: datetime,
        **changes: object,
    ) -> Self:
        normalized_occurred_at = _normalize_datetime(
            occurred_at,
            field_name="rate-source change occurred_at",
        )

        if normalized_occurred_at < self.updated_at:
            raise ValueError(
                "rate-source change occurred_at must not be "
                "earlier than updated_at"
            )

        return replace(
            self,
            updated_at=normalized_occurred_at,
            version=self.version + 1,
            **changes,
        )

    def _transition_status(
        self,
        *,
        target: object,
        occurred_at: datetime,
        reason: object,
        metadata: object = None,
    ) -> Self:
        normalized_target = RateSourceStatus.parse(target)
        normalized_reason = _normalize_required_text(
            reason,
            field_name="rate-source lifecycle reason",
            maximum_length=_MAX_DESCRIPTION_LENGTH,
        )

        allowed: dict[
            RateSourceStatus,
            frozenset[RateSourceStatus],
        ] = {
            RateSourceStatus.DRAFT: frozenset(
                {
                    RateSourceStatus.ACTIVE,
                    RateSourceStatus.RETIRED,
                }
            ),
            RateSourceStatus.ACTIVE: frozenset(
                {
                    RateSourceStatus.DEGRADED,
                    RateSourceStatus.SUSPENDED,
                    RateSourceStatus.RETIRED,
                }
            ),
            RateSourceStatus.DEGRADED: frozenset(
                {
                    RateSourceStatus.ACTIVE,
                    RateSourceStatus.SUSPENDED,
                    RateSourceStatus.RETIRED,
                }
            ),
            RateSourceStatus.SUSPENDED: frozenset(
                {
                    RateSourceStatus.ACTIVE,
                    RateSourceStatus.RETIRED,
                }
            ),
            RateSourceStatus.RETIRED: frozenset(),
        }

        if normalized_target not in allowed[self.status]:
            raise ValueError(
                "invalid rate-source status transition: "
                f"{self.status.value} -> "
                f"{normalized_target.value}"
            )

        merged_metadata = dict(
            self.metadata.canonical_dict()
        )
        merged_metadata.update(
            {
                "lifecycle_reason": normalized_reason,
                "previous_status": self.status.value,
                "current_status": normalized_target.value,
            }
        )

        if metadata is not None:
            merged_metadata.update(
                RateSourceMetadata.of(
                    metadata
                ).canonical_dict()
            )

        return self._with_change(
            occurred_at=occurred_at,
            status=normalized_target,
            metadata=RateSourceMetadata.of(
                merged_metadata
            ),
        )

    def activate(
        self,
        *,
        occurred_at: datetime,
        reason: object,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target=RateSourceStatus.ACTIVE,
            occurred_at=occurred_at,
            reason=reason,
            metadata=metadata,
        )

    def mark_degraded(
        self,
        *,
        occurred_at: datetime,
        reason: object,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target=RateSourceStatus.DEGRADED,
            occurred_at=occurred_at,
            reason=reason,
            metadata=metadata,
        )

    def suspend(
        self,
        *,
        occurred_at: datetime,
        reason: object,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target=RateSourceStatus.SUSPENDED,
            occurred_at=occurred_at,
            reason=reason,
            metadata=metadata,
        )

    def retire(
        self,
        *,
        occurred_at: datetime,
        reason: object,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target=RateSourceStatus.RETIRED,
            occurred_at=occurred_at,
            reason=reason,
            metadata=metadata,
        )

    def update_priority(
        self,
        priority: object,
        *,
        occurred_at: datetime,
    ) -> Self:
        normalized_priority = _normalize_non_negative_integer(
            priority,
            field_name="rate-source priority",
        )

        if normalized_priority == self.priority:
            raise ValueError(
                "rate-source priority update must change priority"
            )

        return self._with_change(
            occurred_at=occurred_at,
            priority=normalized_priority,
        )

    def update_supported_currency_pairs(
        self,
        supported_currency_pairs: object,
        *,
        occurred_at: datetime,
    ) -> Self:
        normalized_pairs = _normalize_string_tuple(
            supported_currency_pairs,
            field_name=(
                "rate-source supported currency pairs"
            ),
            uppercase=True,
        )

        for pair in normalized_pairs:
            if pair.count("/") != 1:
                raise ValueError(
                    "rate-source currency pair must use "
                    "BASE/QUOTE format"
                )

            base, quote = pair.split("/", maxsplit=1)

            if (
                len(base) != 3
                or len(quote) != 3
                or not base.isalpha()
                or not quote.isalpha()
            ):
                raise ValueError(
                    "rate-source currency pair must use "
                    "three-letter currency codes"
                )

        if normalized_pairs == self.supported_currency_pairs:
            raise ValueError(
                "rate-source currency-pair update must "
                "change supported pairs"
            )

        return self._with_change(
            occurred_at=occurred_at,
            supported_currency_pairs=normalized_pairs,
        )

    def update_freshness_policy(
        self,
        *,
        maximum_staleness_seconds: object,
        occurred_at: datetime,
        expected_latency_ms: object = None,
        expected_reliability: object = None,
    ) -> Self:
        normalized_staleness = _normalize_positive_integer(
            maximum_staleness_seconds,
            field_name=(
                "rate-source maximum staleness seconds"
            ),
        )
        normalized_latency = (
            None
            if expected_latency_ms is None
            else _normalize_positive_integer(
                expected_latency_ms,
                field_name=(
                    "rate-source expected latency ms"
                ),
            )
        )
        normalized_reliability = (
            None
            if expected_reliability is None
            else _normalize_ratio(
                expected_reliability,
                field_name=(
                    "rate-source expected reliability"
                ),
            )
        )

        current = (
            self.maximum_staleness_seconds,
            self.expected_latency_ms,
            self.expected_reliability,
        )
        updated = (
            normalized_staleness,
            normalized_latency,
            normalized_reliability,
        )

        if updated == current:
            raise ValueError(
                "rate-source freshness-policy update "
                "must change policy"
            )

        return self._with_change(
            occurred_at=occurred_at,
            maximum_staleness_seconds=normalized_staleness,
            expected_latency_ms=normalized_latency,
            expected_reliability=normalized_reliability,
        )

    def update_trust_level(
        self,
        trust_level: object,
        *,
        occurred_at: datetime,
    ) -> Self:
        normalized_trust_level = ProviderTrustLevel.parse(
            trust_level
        )

        if normalized_trust_level is self.trust_level:
            raise ValueError(
                "rate-source trust-level update "
                "must change trust level"
            )

        return self._with_change(
            occurred_at=occurred_at,
            trust_level=normalized_trust_level,
        )

    def update_metadata(
        self,
        metadata: object,
        *,
        occurred_at: datetime,
    ) -> Self:
        normalized_metadata = RateSourceMetadata.of(
            metadata
        )

        if normalized_metadata == self.metadata:
            raise ValueError(
                "rate-source metadata update "
                "must change metadata"
            )

        return self._with_change(
            occurred_at=occurred_at,
            metadata=normalized_metadata,
        )

    @property
    def is_active(self) -> bool:
        return self.status is RateSourceStatus.ACTIVE

    @property
    def is_terminal(self) -> bool:
        return self.status is RateSourceStatus.RETIRED

    @property
    def source_reference(self) -> str:
        return self.rate_source_id.value

    @property
    def provider_reference(self) -> str:
        return self.provider_id.value

    def supports_pair(
        self,
        value: object,
    ) -> bool:
        normalized = _normalize_required_text(
            value,
            field_name="currency pair",
            maximum_length=16,
        ).upper()

        return normalized in self.supported_currency_pairs

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "rate_source_id": self.rate_source_id.value,
            "provider_id": self.provider_id.value,
            "source_type": self.source_type.value,
            "status": self.status.value,
            "trust_level": self.trust_level.value,
            "priority": self.priority,
            "supported_currency_pairs": list(
                self.supported_currency_pairs
            ),
            "maximum_staleness_seconds": (
                self.maximum_staleness_seconds
            ),
            "expected_latency_ms": (
                self.expected_latency_ms
            ),
            "expected_reliability": (
                None
                if self.expected_reliability is None
                else str(self.expected_reliability)
            ),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }



@dataclass(frozen=True, slots=True)
class ExchangeRateProvider:
    """Immutable canonical definition of an FX-rate provider.

    This aggregate stores provider identity, descriptive capabilities,
    trust classification, endpoint description, and metadata. It does
    not fetch rates, perform network calls, store credentials, lock
    exchange rates, execute conversions, or persist itself.
    """

    provider_id: ExchangeRateProviderId
    name: ProviderName
    provider_type: ExchangeRateProviderType
    status: ExchangeRateProviderStatus
    trust_level: ProviderTrustLevel
    capabilities: ProviderCapabilities
    endpoint: ProviderEndpoint | None
    metadata: ProviderMetadata
    created_at: datetime
    updated_at: datetime
    version: int = 1

    def __post_init__(self) -> None:
        normalized_provider_id = ExchangeRateProviderId.of(
            self.provider_id
        )
        normalized_name = ProviderName.of(self.name)
        normalized_provider_type = (
            ExchangeRateProviderType.parse(
                self.provider_type
            )
        )
        normalized_status = ExchangeRateProviderStatus.parse(
            self.status
        )
        normalized_trust_level = ProviderTrustLevel.parse(
            self.trust_level
        )
        normalized_capabilities = ProviderCapabilities.of(
            self.capabilities
        )
        normalized_endpoint = (
            None
            if self.endpoint is None
            else ProviderEndpoint.of(self.endpoint)
        )
        normalized_metadata = ProviderMetadata.of(
            self.metadata
        )
        normalized_created_at = _normalize_datetime(
            self.created_at,
            field_name=(
                "exchange-rate provider created_at"
            ),
        )
        normalized_updated_at = _normalize_datetime(
            self.updated_at,
            field_name=(
                "exchange-rate provider updated_at"
            ),
        )
        normalized_version = _normalize_version(
            self.version
        )

        if normalized_updated_at < normalized_created_at:
            raise ValueError(
                "exchange-rate provider updated_at must not "
                "be earlier than created_at"
            )

        object.__setattr__(
            self,
            "provider_id",
            normalized_provider_id,
        )
        object.__setattr__(
            self,
            "name",
            normalized_name,
        )
        object.__setattr__(
            self,
            "provider_type",
            normalized_provider_type,
        )
        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "trust_level",
            normalized_trust_level,
        )
        object.__setattr__(
            self,
            "capabilities",
            normalized_capabilities,
        )
        object.__setattr__(
            self,
            "endpoint",
            normalized_endpoint,
        )
        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
        )
        object.__setattr__(
            self,
            "created_at",
            normalized_created_at,
        )
        object.__setattr__(
            self,
            "updated_at",
            normalized_updated_at,
        )
        object.__setattr__(
            self,
            "version",
            normalized_version,
        )

    @classmethod
    def create(
        cls,
        *,
        provider_id: object,
        name: object,
        provider_type: object,
        created_at: datetime,
        status: object = ExchangeRateProviderStatus.DRAFT,
        trust_level: object = ProviderTrustLevel.UNVERIFIED,
        capabilities: object = None,
        endpoint: object = None,
        endpoint_description: object = None,
        metadata: object = None,
    ) -> Self:
        normalized_created_at = _normalize_datetime(
            created_at,
            field_name=(
                "exchange-rate provider created_at"
            ),
        )

        normalized_endpoint = (
            None
            if endpoint is None
            else ProviderEndpoint.of(
                endpoint,
                description=endpoint_description,
            )
        )

        return cls(
            provider_id=ExchangeRateProviderId.of(
                provider_id
            ),
            name=ProviderName.of(name),
            provider_type=ExchangeRateProviderType.parse(
                provider_type
            ),
            status=ExchangeRateProviderStatus.parse(
                status
            ),
            trust_level=ProviderTrustLevel.parse(
                trust_level
            ),
            capabilities=ProviderCapabilities.of(
                capabilities
            ),
            endpoint=normalized_endpoint,
            metadata=ProviderMetadata.of(metadata),
            created_at=normalized_created_at,
            updated_at=normalized_created_at,
            version=1,
        )

    def _with_change(
        self,
        *,
        occurred_at: datetime,
        **changes: object,
    ) -> Self:
        normalized_occurred_at = _normalize_datetime(
            occurred_at,
            field_name=(
                "exchange-rate provider change occurred_at"
            ),
        )

        if normalized_occurred_at < self.updated_at:
            raise ValueError(
                "exchange-rate provider change occurred_at "
                "must not be earlier than updated_at"
            )

        return replace(
            self,
            updated_at=normalized_occurred_at,
            version=self.version + 1,
            **changes,
        )

    def _transition_status(
        self,
        *,
        target: object,
        occurred_at: datetime,
        reason: object,
        metadata: object = None,
    ) -> Self:
        normalized_target = ExchangeRateProviderStatus.parse(
            target
        )
        normalized_reason = _normalize_required_text(
            reason,
            field_name=(
                "exchange-rate provider lifecycle reason"
            ),
            maximum_length=_MAX_DESCRIPTION_LENGTH,
        )

        allowed: dict[
            ExchangeRateProviderStatus,
            frozenset[ExchangeRateProviderStatus],
        ] = {
            ExchangeRateProviderStatus.DRAFT: frozenset(
                {
                    ExchangeRateProviderStatus.ACTIVE,
                    ExchangeRateProviderStatus.RETIRED,
                }
            ),
            ExchangeRateProviderStatus.ACTIVE: frozenset(
                {
                    ExchangeRateProviderStatus.DEGRADED,
                    ExchangeRateProviderStatus.SUSPENDED,
                    ExchangeRateProviderStatus.RETIRED,
                }
            ),
            ExchangeRateProviderStatus.DEGRADED: frozenset(
                {
                    ExchangeRateProviderStatus.ACTIVE,
                    ExchangeRateProviderStatus.SUSPENDED,
                    ExchangeRateProviderStatus.RETIRED,
                }
            ),
            ExchangeRateProviderStatus.SUSPENDED: frozenset(
                {
                    ExchangeRateProviderStatus.ACTIVE,
                    ExchangeRateProviderStatus.RETIRED,
                }
            ),
            ExchangeRateProviderStatus.RETIRED: frozenset(),
        }

        if normalized_target not in allowed[self.status]:
            raise ValueError(
                "invalid exchange-rate provider status "
                f"transition: {self.status.value} -> "
                f"{normalized_target.value}"
            )

        merged_metadata = dict(
            self.metadata.canonical_dict()
        )
        merged_metadata.update(
            {
                "lifecycle_reason": normalized_reason,
                "previous_status": self.status.value,
                "current_status": normalized_target.value,
            }
        )

        if metadata is not None:
            merged_metadata.update(
                ProviderMetadata.of(
                    metadata
                ).canonical_dict()
            )

        return self._with_change(
            occurred_at=occurred_at,
            status=normalized_target,
            metadata=ProviderMetadata.of(
                merged_metadata
            ),
        )

    def activate(
        self,
        *,
        occurred_at: datetime,
        reason: object,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target=ExchangeRateProviderStatus.ACTIVE,
            occurred_at=occurred_at,
            reason=reason,
            metadata=metadata,
        )

    def mark_degraded(
        self,
        *,
        occurred_at: datetime,
        reason: object,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target=ExchangeRateProviderStatus.DEGRADED,
            occurred_at=occurred_at,
            reason=reason,
            metadata=metadata,
        )

    def suspend(
        self,
        *,
        occurred_at: datetime,
        reason: object,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target=ExchangeRateProviderStatus.SUSPENDED,
            occurred_at=occurred_at,
            reason=reason,
            metadata=metadata,
        )

    def retire(
        self,
        *,
        occurred_at: datetime,
        reason: object,
        metadata: object = None,
    ) -> Self:
        return self._transition_status(
            target=ExchangeRateProviderStatus.RETIRED,
            occurred_at=occurred_at,
            reason=reason,
            metadata=metadata,
        )

    def update_name(
        self,
        name: object,
        *,
        occurred_at: datetime,
    ) -> Self:
        normalized_name = ProviderName.of(name)

        if normalized_name == self.name:
            raise ValueError(
                "exchange-rate provider name update "
                "must change name"
            )

        return self._with_change(
            occurred_at=occurred_at,
            name=normalized_name,
        )

    def update_endpoint(
        self,
        endpoint: object,
        *,
        occurred_at: datetime,
        description: object = None,
    ) -> Self:
        normalized_endpoint = ProviderEndpoint.of(
            endpoint,
            description=description,
        )

        if normalized_endpoint == self.endpoint:
            raise ValueError(
                "exchange-rate provider endpoint update "
                "must change endpoint"
            )

        return self._with_change(
            occurred_at=occurred_at,
            endpoint=normalized_endpoint,
        )

    def remove_endpoint(
        self,
        *,
        occurred_at: datetime,
    ) -> Self:
        if self.endpoint is None:
            raise ValueError(
                "exchange-rate provider has no endpoint "
                "to remove"
            )

        return self._with_change(
            occurred_at=occurred_at,
            endpoint=None,
        )

    def update_capabilities(
        self,
        capabilities: object,
        *,
        occurred_at: datetime,
    ) -> Self:
        normalized_capabilities = ProviderCapabilities.of(
            capabilities
        )

        if normalized_capabilities == self.capabilities:
            raise ValueError(
                "exchange-rate provider capabilities update "
                "must change capabilities"
            )

        return self._with_change(
            occurred_at=occurred_at,
            capabilities=normalized_capabilities,
        )

    def update_trust_level(
        self,
        trust_level: object,
        *,
        occurred_at: datetime,
    ) -> Self:
        normalized_trust_level = ProviderTrustLevel.parse(
            trust_level
        )

        if normalized_trust_level is self.trust_level:
            raise ValueError(
                "exchange-rate provider trust-level update "
                "must change trust level"
            )

        return self._with_change(
            occurred_at=occurred_at,
            trust_level=normalized_trust_level,
        )

    def update_metadata(
        self,
        metadata: object,
        *,
        occurred_at: datetime,
    ) -> Self:
        normalized_metadata = ProviderMetadata.of(
            metadata
        )

        if normalized_metadata == self.metadata:
            raise ValueError(
                "exchange-rate provider metadata update "
                "must change metadata"
            )

        return self._with_change(
            occurred_at=occurred_at,
            metadata=normalized_metadata,
        )

    @property
    def is_active(self) -> bool:
        return (
            self.status
            is ExchangeRateProviderStatus.ACTIVE
        )

    @property
    def is_terminal(self) -> bool:
        return (
            self.status
            is ExchangeRateProviderStatus.RETIRED
        )

    @property
    def provider_reference(self) -> str:
        """Return the canonical string reference used by FX models."""

        return self.provider_id.value

    def supports_pair(
        self,
        value: object,
    ) -> bool:
        return self.capabilities.supports_pair(value)

    def supports_source_type(
        self,
        value: object,
    ) -> bool:
        return self.capabilities.supports_source_type(
            value
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id.value,
            "name": self.name.value,
            "provider_type": self.provider_type.value,
            "status": self.status.value,
            "trust_level": self.trust_level.value,
            "capabilities": (
                self.capabilities.canonical_dict()
            ),
            "endpoint": (
                None
                if self.endpoint is None
                else self.endpoint.canonical_dict()
            ),
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }


__all__ = [
    "ExchangeRateProvider",
    "ExchangeRateProviderId",
    "ExchangeRateProviderRegistry",
    "ExchangeRateProviderRegistryId",
    "ExchangeRateProviderStatus",
    "ExchangeRateProviderType",
    "ProviderCapabilities",
    "ProviderEndpoint",
    "ProviderMetadata",
    "ProviderName",
    "ProviderTrustLevel",
    "RateSource",
    "RateSourceId",
    "RateSourceMetadata",
    "RateSourceStatus",
    "RateSourceType",
]
