from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Self

from .money import Currency


_MAX_IDENTIFIER_LENGTH = 128
_MAX_NAME_LENGTH = 120
_MAX_SYMBOL_LENGTH = 12
_MAX_METADATA_KEY_LENGTH = 128
_MAX_METADATA_STRING_LENGTH = 1000

_PROHIBITED_METADATA_KEYS = frozenset(
    {
        "access_token",
        "account_number",
        "api_key",
        "authorization",
        "card_number",
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


def _normalize_country_code(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("country code must be a string")

    normalized = value.strip().upper()

    if (
        len(normalized) != 2
        or not normalized.isalpha()
        or not normalized.isascii()
    ):
        raise ValueError(
            "country code must contain exactly "
            "two ASCII alphabetic characters"
        )

    return normalized


def _normalize_minor_units(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("currency minor units must be an integer")

    if value < 0 or value > 8:
        raise ValueError(
            "currency minor units must be between 0 and 8"
        )

    return value


def _normalize_version(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "currency definition version must be an integer"
        )

    if value < 1:
        raise ValueError(
            "currency definition version must be "
            "greater than or equal to 1"
        )

    return value


def _normalize_metadata_value(
    value: object,
    *,
    field_name: str,
) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        if len(value) > _MAX_METADATA_STRING_LENGTH:
            raise ValueError(
                f"{field_name} string value is too long"
            )

        return value

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
        key = _normalize_required_text(
            raw_key,
            field_name="currency metadata key",
            maximum_length=_MAX_METADATA_KEY_LENGTH,
        ).lower().replace(" ", "_")

        if key in _PROHIBITED_METADATA_KEYS:
            raise ValueError(
                "currency metadata contains prohibited "
                f"sensitive key: {key}"
            )

        if key in normalized:
            raise ValueError(
                f"duplicate normalized currency metadata key: {key}"
            )

        normalized[key] = _normalize_metadata_value(
            raw_value,
            field_name=f"currency metadata {key}",
        )

    return dict(sorted(normalized.items()))


class CurrencyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_required_text(
            value,
            field_name="currency status",
            maximum_length=32,
        ).lower().replace("-", "_").replace(" ", "_")

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported currency status: {normalized}"
            ) from exc


class CurrencyType(str, Enum):
    FIAT = "fiat"
    DIGITAL = "digital"
    COMMODITY_BACKED = "commodity_backed"
    LOYALTY = "loyalty"
    TEST = "test"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_required_text(
            value,
            field_name="currency type",
            maximum_length=64,
        ).lower().replace("-", "_").replace(" ", "_")

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported currency type: {normalized}"
            ) from exc


class CurrencyRoundingMode(str, Enum):
    HALF_EVEN = "half_even"
    HALF_UP = "half_up"
    HALF_DOWN = "half_down"
    DOWN = "down"
    UP = "up"

    @classmethod
    def parse(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        normalized = _normalize_required_text(
            value,
            field_name="currency rounding mode",
            maximum_length=32,
        ).lower().replace("-", "_").replace(" ", "_")

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported currency rounding mode: {normalized}"
            ) from exc


@dataclass(frozen=True, slots=True, order=True)
class CurrencyDefinitionId:
    value: str

    def __post_init__(self) -> None:
        normalized = _normalize_required_text(
            self.value,
            field_name="currency definition id",
            maximum_length=_MAX_IDENTIFIER_LENGTH,
        )

        object.__setattr__(self, "value", normalized)

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_required_text(
                value,
                field_name="currency definition id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class CurrencyName:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required_text(
                self.value,
                field_name="currency name",
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
                field_name="currency name",
                maximum_length=_MAX_NAME_LENGTH,
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class CurrencySymbol:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required_text(
                self.value,
                field_name="currency symbol",
                maximum_length=_MAX_SYMBOL_LENGTH,
            ),
        )

    @classmethod
    def of(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value

        return cls(
            _normalize_required_text(
                value,
                field_name="currency symbol",
                maximum_length=_MAX_SYMBOL_LENGTH,
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class CurrencyCountryCodes:
    values: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.values, str):
            raw_values: tuple[object, ...] = (self.values,)
        else:
            try:
                raw_values = tuple(self.values)
            except TypeError as exc:
                raise TypeError(
                    "currency country codes must be iterable"
                ) from exc

        normalized = tuple(
            sorted(
                {
                    _normalize_country_code(value)
                    for value in raw_values
                }
            )
        )

        object.__setattr__(self, "values", normalized)

    @classmethod
    def of(cls, value: object = None) -> Self:
        if isinstance(value, cls):
            return value

        if value is None:
            return cls()

        if isinstance(value, str):
            return cls((value,))

        try:
            return cls(tuple(value))  # type: ignore[arg-type]
        except TypeError as exc:
            raise TypeError(
                "currency country codes must be iterable"
            ) from exc

    def contains(self, country_code: object) -> bool:
        return _normalize_country_code(country_code) in self.values

    def canonical(self) -> tuple[str, ...]:
        return tuple(self.values)


@dataclass(frozen=True, slots=True)
class CurrencyMetadata:
    values: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.values, Mapping):
            raise TypeError(
                "currency metadata must be a mapping"
            )

        normalized = MappingProxyType(
            _normalize_metadata_mapping(self.values)
        )

        object.__setattr__(self, "values", normalized)

    @classmethod
    def of(cls, value: object = None) -> Self:
        if isinstance(value, cls):
            return value

        if value is None:
            return cls()

        if not isinstance(value, Mapping):
            raise TypeError(
                "currency metadata must be a mapping"
            )

        return cls(value)

    def with_updates(
        self,
        updates: Mapping[object, object],
    ) -> Self:
        if not isinstance(updates, Mapping):
            raise TypeError(
                "currency metadata updates must be a mapping"
            )

        merged = dict(self.values)
        merged.update(updates)

        return type(self)(merged)

    def canonical_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(self.values))


@dataclass(frozen=True, slots=True)
class CurrencyDefinition:
    currency_definition_id: CurrencyDefinitionId
    currency: Currency
    name: CurrencyName
    symbol: CurrencySymbol
    currency_type: CurrencyType
    status: CurrencyStatus
    minor_units: int
    rounding_mode: CurrencyRoundingMode
    country_codes: CurrencyCountryCodes = field(
        default_factory=CurrencyCountryCodes
    )
    numeric_code: str | None = None
    fund_code: str | None = None
    metadata: CurrencyMetadata = field(
        default_factory=CurrencyMetadata
    )
    version: int = 1

    def __post_init__(self) -> None:
        normalized_id = CurrencyDefinitionId.of(
            self.currency_definition_id
        )
        normalized_currency = Currency.of(self.currency)
        normalized_name = CurrencyName.of(self.name)
        normalized_symbol = CurrencySymbol.of(self.symbol)
        normalized_type = CurrencyType.parse(
            self.currency_type
        )
        normalized_status = CurrencyStatus.parse(
            self.status
        )
        normalized_minor_units = _normalize_minor_units(
            self.minor_units
        )
        normalized_rounding = CurrencyRoundingMode.parse(
            self.rounding_mode
        )
        normalized_country_codes = CurrencyCountryCodes.of(
            self.country_codes
        )
        normalized_metadata = CurrencyMetadata.of(
            self.metadata
        )
        normalized_version = _normalize_version(
            self.version
        )

        normalized_numeric_code = self._normalize_optional_code(
            self.numeric_code,
            field_name="currency numeric code",
            required_length=3,
            digits_only=True,
        )
        normalized_fund_code = self._normalize_optional_code(
            self.fund_code,
            field_name="currency fund code",
            required_length=3,
            digits_only=False,
        )

        if (
            normalized_currency.minor_units
            != normalized_minor_units
        ):
            raise ValueError(
                "currency definition minor units must match "
                "the canonical Currency minor-units contract"
            )

        object.__setattr__(
            self,
            "currency_definition_id",
            normalized_id,
        )
        object.__setattr__(
            self,
            "currency",
            normalized_currency,
        )
        object.__setattr__(
            self,
            "name",
            normalized_name,
        )
        object.__setattr__(
            self,
            "symbol",
            normalized_symbol,
        )
        object.__setattr__(
            self,
            "currency_type",
            normalized_type,
        )
        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "minor_units",
            normalized_minor_units,
        )
        object.__setattr__(
            self,
            "rounding_mode",
            normalized_rounding,
        )
        object.__setattr__(
            self,
            "country_codes",
            normalized_country_codes,
        )
        object.__setattr__(
            self,
            "numeric_code",
            normalized_numeric_code,
        )
        object.__setattr__(
            self,
            "fund_code",
            normalized_fund_code,
        )
        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
        )
        object.__setattr__(
            self,
            "version",
            normalized_version,
        )

    @staticmethod
    def _normalize_optional_code(
        value: object,
        *,
        field_name: str,
        required_length: int,
        digits_only: bool,
    ) -> str | None:
        if value is None:
            return None

        normalized = _normalize_required_text(
            value,
            field_name=field_name,
            maximum_length=required_length,
        ).upper()

        if len(normalized) != required_length:
            raise ValueError(
                f"{field_name} must contain exactly "
                f"{required_length} characters"
            )

        if digits_only and not normalized.isdigit():
            raise ValueError(
                f"{field_name} must contain only digits"
            )

        if (
            not digits_only
            and (
                not normalized.isalpha()
                or not normalized.isascii()
            )
        ):
            raise ValueError(
                f"{field_name} must contain only "
                "ASCII alphabetic characters"
            )

        return normalized

    @classmethod
    def create(
        cls,
        *,
        currency_definition_id: object,
        currency: object,
        name: object,
        symbol: object,
        currency_type: object,
        status: object = CurrencyStatus.DRAFT,
        minor_units: object | None = None,
        rounding_mode: object = CurrencyRoundingMode.HALF_EVEN,
        country_codes: object = None,
        numeric_code: object = None,
        fund_code: object = None,
        metadata: object = None,
    ) -> Self:
        normalized_currency = Currency.of(currency)

        return cls(
            currency_definition_id=CurrencyDefinitionId.of(
                currency_definition_id
            ),
            currency=normalized_currency,
            name=CurrencyName.of(name),
            symbol=CurrencySymbol.of(symbol),
            currency_type=CurrencyType.parse(
                currency_type
            ),
            status=CurrencyStatus.parse(status),
            minor_units=(
                normalized_currency.minor_units
                if minor_units is None
                else _normalize_minor_units(minor_units)
            ),
            rounding_mode=CurrencyRoundingMode.parse(
                rounding_mode
            ),
            country_codes=CurrencyCountryCodes.of(
                country_codes
            ),
            numeric_code=numeric_code,
            fund_code=fund_code,
            metadata=CurrencyMetadata.of(metadata),
            version=1,
        )

    @property
    def is_active(self) -> bool:
        return self.status is CurrencyStatus.ACTIVE

    @property
    def is_fiat(self) -> bool:
        return self.currency_type is CurrencyType.FIAT

    @property
    def code(self) -> str:
        return self.currency.code

    def supports_country(
        self,
        country_code: object,
    ) -> bool:
        return self.country_codes.contains(country_code)

    def _require_non_retired(self) -> None:
        if self.status is CurrencyStatus.RETIRED:
            raise ValueError(
                "retired currency definition does not permit "
                "further changes"
            )

    def _metadata_with_lifecycle(
        self,
        *,
        action: str,
        reason: object = None,
    ) -> CurrencyMetadata:
        updates: dict[str, Any] = {
            "lifecycle_action": action,
        }

        if reason is not None:
            updates["lifecycle_reason"] = (
                _normalize_required_text(
                    reason,
                    field_name=(
                        "currency lifecycle reason"
                    ),
                    maximum_length=500,
                )
            )

        return self.metadata.with_updates(updates)

    def _with_change(
        self,
        *,
        status: CurrencyStatus | None = None,
        name: CurrencyName | None = None,
        symbol: CurrencySymbol | None = None,
        country_codes: CurrencyCountryCodes | None = None,
        metadata: CurrencyMetadata | None = None,
    ) -> Self:
        return replace(
            self,
            status=(
                self.status
                if status is None
                else status
            ),
            name=(
                self.name
                if name is None
                else name
            ),
            symbol=(
                self.symbol
                if symbol is None
                else symbol
            ),
            country_codes=(
                self.country_codes
                if country_codes is None
                else country_codes
            ),
            metadata=(
                self.metadata
                if metadata is None
                else metadata
            ),
            version=self.version + 1,
        )

    def activate(
        self,
        *,
        reason: object = None,
    ) -> Self:
        """Activate a draft currency definition."""

        self._require_non_retired()

        if self.status is not CurrencyStatus.DRAFT:
            raise ValueError(
                "currency activation requires draft status"
            )

        return self._with_change(
            status=CurrencyStatus.ACTIVE,
            metadata=self._metadata_with_lifecycle(
                action="activate",
                reason=reason,
            ),
        )

    def suspend(
        self,
        *,
        reason: object,
    ) -> Self:
        """Suspend an active currency definition."""

        self._require_non_retired()

        if self.status is not CurrencyStatus.ACTIVE:
            raise ValueError(
                "currency suspension requires active status"
            )

        return self._with_change(
            status=CurrencyStatus.SUSPENDED,
            metadata=self._metadata_with_lifecycle(
                action="suspend",
                reason=reason,
            ),
        )

    def reactivate(
        self,
        *,
        reason: object = None,
    ) -> Self:
        """Return a suspended definition to active status."""

        self._require_non_retired()

        if self.status is not CurrencyStatus.SUSPENDED:
            raise ValueError(
                "currency reactivation requires "
                "suspended status"
            )

        return self._with_change(
            status=CurrencyStatus.ACTIVE,
            metadata=self._metadata_with_lifecycle(
                action="reactivate",
                reason=reason,
            ),
        )

    def retire(
        self,
        *,
        reason: object,
    ) -> Self:
        """Permanently retire a non-retired definition."""

        self._require_non_retired()

        if self.status not in {
            CurrencyStatus.DRAFT,
            CurrencyStatus.ACTIVE,
            CurrencyStatus.SUSPENDED,
        }:
            raise ValueError(
                "currency retirement requires draft, "
                "active, or suspended status"
            )

        return self._with_change(
            status=CurrencyStatus.RETIRED,
            metadata=self._metadata_with_lifecycle(
                action="retire",
                reason=reason,
            ),
        )

    def update_name(
        self,
        name: object,
    ) -> Self:
        """Replace the display name immutably."""

        self._require_non_retired()
        normalized_name = CurrencyName.of(name)

        if normalized_name == self.name:
            raise ValueError(
                "currency definition update must change name"
            )

        return self._with_change(
            name=normalized_name,
        )

    def update_symbol(
        self,
        symbol: object,
    ) -> Self:
        """Replace the display symbol immutably."""

        self._require_non_retired()
        normalized_symbol = CurrencySymbol.of(symbol)

        if normalized_symbol == self.symbol:
            raise ValueError(
                "currency definition update must change symbol"
            )

        return self._with_change(
            symbol=normalized_symbol,
        )

    def update_country_codes(
        self,
        country_codes: object,
    ) -> Self:
        """Replace supported country codes immutably."""

        self._require_non_retired()
        normalized_codes = CurrencyCountryCodes.of(
            country_codes
        )

        if normalized_codes == self.country_codes:
            raise ValueError(
                "currency definition update must change "
                "country codes"
            )

        return self._with_change(
            country_codes=normalized_codes,
        )

    def update_metadata(
        self,
        metadata: object,
    ) -> Self:
        """Replace non-sensitive currency metadata."""

        self._require_non_retired()
        normalized_metadata = CurrencyMetadata.of(
            metadata
        )

        if normalized_metadata == self.metadata:
            raise ValueError(
                "currency definition update must change "
                "metadata"
            )

        return self._with_change(
            metadata=normalized_metadata,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "currency_definition_id": (
                self.currency_definition_id.value
            ),
            "currency": self.currency.canonical_dict(),
            "name": self.name.value,
            "symbol": self.symbol.value,
            "currency_type": self.currency_type.value,
            "status": self.status.value,
            "minor_units": self.minor_units,
            "rounding_mode": self.rounding_mode.value,
            "country_codes": list(
                self.country_codes.canonical()
            ),
            "numeric_code": self.numeric_code,
            "fund_code": self.fund_code,
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "version": self.version,
        }



@dataclass(frozen=True, slots=True, order=True)
class CurrencyRegistryId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required_text(
                self.value,
                field_name="currency registry id",
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
                field_name="currency registry id",
                maximum_length=_MAX_IDENTIFIER_LENGTH,
            )
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class CurrencyRegistry:
    """Immutable canonical collection of currency definitions.

    The registry owns deterministic definition lookup and uniqueness
    enforcement only. It does not own persistence, provider, wallet,
    ledger, FX, settlement, or transaction authority.
    """

    currency_registry_id: CurrencyRegistryId
    definitions: tuple[CurrencyDefinition, ...] = ()
    metadata: CurrencyMetadata = field(
        default_factory=CurrencyMetadata
    )
    version: int = 1

    def __post_init__(self) -> None:
        normalized_id = CurrencyRegistryId.of(
            self.currency_registry_id
        )

        try:
            raw_definitions = tuple(self.definitions)
        except TypeError as exc:
            raise TypeError(
                "currency registry definitions must be iterable"
            ) from exc

        normalized_definitions: list[CurrencyDefinition] = []

        for definition in raw_definitions:
            if not isinstance(definition, CurrencyDefinition):
                raise TypeError(
                    "currency registry definitions must contain "
                    "CurrencyDefinition values"
                )

            normalized_definitions.append(definition)

        ordered = tuple(
            sorted(
                normalized_definitions,
                key=lambda item: (
                    item.currency.code,
                    item.currency_definition_id.value,
                ),
            )
        )

        self._validate_uniqueness(ordered)

        normalized_metadata = CurrencyMetadata.of(
            self.metadata
        )
        normalized_version = _normalize_version(
            self.version
        )

        object.__setattr__(
            self,
            "currency_registry_id",
            normalized_id,
        )
        object.__setattr__(
            self,
            "definitions",
            ordered,
        )
        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
        )
        object.__setattr__(
            self,
            "version",
            normalized_version,
        )

    @staticmethod
    def _validate_uniqueness(
        definitions: tuple[CurrencyDefinition, ...],
    ) -> None:
        definition_ids: set[str] = set()
        currency_codes: set[str] = set()
        numeric_codes: set[str] = set()

        for definition in definitions:
            definition_id = (
                definition.currency_definition_id.value
            )
            currency_code = definition.currency.code

            if definition_id in definition_ids:
                raise ValueError(
                    "currency registry contains duplicate "
                    f"definition id: {definition_id}"
                )

            if currency_code in currency_codes:
                raise ValueError(
                    "currency registry contains duplicate "
                    f"currency code: {currency_code}"
                )

            definition_ids.add(definition_id)
            currency_codes.add(currency_code)

            if definition.numeric_code is not None:
                if definition.numeric_code in numeric_codes:
                    raise ValueError(
                        "currency registry contains duplicate "
                        f"numeric code: {definition.numeric_code}"
                    )

                numeric_codes.add(definition.numeric_code)

    @classmethod
    def create(
        cls,
        *,
        currency_registry_id: object,
        definitions: object = (),
        metadata: object = None,
    ) -> Self:
        if definitions is None:
            normalized_definitions: tuple[
                CurrencyDefinition,
                ...,
            ] = ()
        else:
            try:
                normalized_definitions = tuple(
                    definitions  # type: ignore[arg-type]
                )
            except TypeError as exc:
                raise TypeError(
                    "currency registry definitions "
                    "must be iterable"
                ) from exc

        return cls(
            currency_registry_id=CurrencyRegistryId.of(
                currency_registry_id
            ),
            definitions=normalized_definitions,
            metadata=CurrencyMetadata.of(metadata),
            version=1,
        )

    @property
    def size(self) -> int:
        return len(self.definitions)

    @property
    def is_empty(self) -> bool:
        return not self.definitions

    def __len__(self) -> int:
        return self.size

    def __iter__(self):
        return iter(self.definitions)

    def get_by_id(
        self,
        currency_definition_id: object,
    ) -> CurrencyDefinition | None:
        normalized_id = CurrencyDefinitionId.of(
            currency_definition_id
        )

        for definition in self.definitions:
            if (
                definition.currency_definition_id
                == normalized_id
            ):
                return definition

        return None

    def require_by_id(
        self,
        currency_definition_id: object,
    ) -> CurrencyDefinition:
        definition = self.get_by_id(
            currency_definition_id
        )

        if definition is None:
            normalized_id = CurrencyDefinitionId.of(
                currency_definition_id
            )

            raise KeyError(
                "currency definition not found for id: "
                f"{normalized_id.value}"
            )

        return definition

    def get_by_code(
        self,
        currency: object,
    ) -> CurrencyDefinition | None:
        normalized_currency = Currency.of(currency)

        for definition in self.definitions:
            if definition.currency == normalized_currency:
                return definition

        return None

    def require_by_code(
        self,
        currency: object,
    ) -> CurrencyDefinition:
        normalized_currency = Currency.of(currency)
        definition = self.get_by_code(
            normalized_currency
        )

        if definition is None:
            raise KeyError(
                "currency definition not found for code: "
                f"{normalized_currency.code}"
            )

        return definition

    def contains_code(
        self,
        currency: object,
    ) -> bool:
        return self.get_by_code(currency) is not None

    def contains_id(
        self,
        currency_definition_id: object,
    ) -> bool:
        return (
            self.get_by_id(currency_definition_id)
            is not None
        )

    def active_definitions(
        self,
    ) -> tuple[CurrencyDefinition, ...]:
        return tuple(
            definition
            for definition in self.definitions
            if definition.status is CurrencyStatus.ACTIVE
        )

    def definitions_for_country(
        self,
        country_code: object,
        *,
        active_only: bool = False,
    ) -> tuple[CurrencyDefinition, ...]:
        if not isinstance(active_only, bool):
            raise TypeError(
                "active_only must be a boolean"
            )

        normalized_country_code = _normalize_country_code(
            country_code
        )

        return tuple(
            definition
            for definition in self.definitions
            if definition.supports_country(
                normalized_country_code
            )
            and (
                not active_only
                or definition.status
                is CurrencyStatus.ACTIVE
            )
        )

    def definitions_by_type(
        self,
        currency_type: object,
        *,
        active_only: bool = False,
    ) -> tuple[CurrencyDefinition, ...]:
        if not isinstance(active_only, bool):
            raise TypeError(
                "active_only must be a boolean"
            )

        normalized_type = CurrencyType.parse(
            currency_type
        )

        return tuple(
            definition
            for definition in self.definitions
            if definition.currency_type is normalized_type
            and (
                not active_only
                or definition.status
                is CurrencyStatus.ACTIVE
            )
        )

    def register(
        self,
        definition: CurrencyDefinition,
    ) -> Self:
        if not isinstance(definition, CurrencyDefinition):
            raise TypeError(
                "currency registry registration requires "
                "a CurrencyDefinition"
            )

        if self.contains_id(
            definition.currency_definition_id
        ):
            raise ValueError(
                "currency registry already contains "
                "the definition id"
            )

        if self.contains_code(definition.currency):
            raise ValueError(
                "currency registry already contains "
                "the currency code"
            )

        if definition.numeric_code is not None:
            for existing in self.definitions:
                if (
                    existing.numeric_code
                    == definition.numeric_code
                ):
                    raise ValueError(
                        "currency registry already contains "
                        "the numeric code"
                    )

        return replace(
            self,
            definitions=(
                *self.definitions,
                definition,
            ),
            version=self.version + 1,
        )

    def update_definition(
        self,
        definition: CurrencyDefinition,
    ) -> Self:
        if not isinstance(definition, CurrencyDefinition):
            raise TypeError(
                "currency registry update requires "
                "a CurrencyDefinition"
            )

        existing = self.get_by_id(
            definition.currency_definition_id
        )

        if existing is None:
            raise KeyError(
                "currency registry cannot update "
                "an unknown definition"
            )

        if definition.currency != existing.currency:
            raise ValueError(
                "currency registry update must preserve "
                "the canonical currency code"
            )

        if definition == existing:
            raise ValueError(
                "currency registry update must change "
                "the definition"
            )

        for other in self.definitions:
            if (
                other.currency_definition_id
                == definition.currency_definition_id
            ):
                continue

            if (
                definition.numeric_code is not None
                and other.numeric_code
                == definition.numeric_code
            ):
                raise ValueError(
                    "currency registry update would duplicate "
                    "a numeric code"
                )

        updated_definitions = tuple(
            definition
            if (
                item.currency_definition_id
                == definition.currency_definition_id
            )
            else item
            for item in self.definitions
        )

        return replace(
            self,
            definitions=updated_definitions,
            version=self.version + 1,
        )

    def update_metadata(
        self,
        metadata: object,
    ) -> Self:
        normalized_metadata = CurrencyMetadata.of(
            metadata
        )

        if normalized_metadata == self.metadata:
            raise ValueError(
                "currency registry update must change metadata"
            )

        return replace(
            self,
            metadata=normalized_metadata,
            version=self.version + 1,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "currency_registry_id": (
                self.currency_registry_id.value
            ),
            "definitions": [
                definition.canonical_dict()
                for definition in self.definitions
            ],
            "metadata": dict(
                self.metadata.canonical_dict()
            ),
            "version": self.version,
        }



_STANDARD_CURRENCY_ROWS: tuple[
    tuple[
        str,
        str,
        str,
        tuple[str, ...],
        str,
    ],
    ...,
] = (
    (
        "AUD",
        "Australian Dollar",
        "$",
        ("AU",),
        "036",
    ),
    (
        "BIF",
        "Burundian Franc",
        "FBu",
        ("BI",),
        "108",
    ),
    (
        "CAD",
        "Canadian Dollar",
        "C$",
        ("CA",),
        "124",
    ),
    (
        "CDF",
        "Congolese Franc",
        "FC",
        ("CD",),
        "976",
    ),
    (
        "EUR",
        "Euro",
        "€",
        (
            "AT",
            "BE",
            "DE",
            "ES",
            "FI",
            "FR",
            "IE",
            "IT",
            "LU",
            "NL",
            "PT",
        ),
        "978",
    ),
    (
        "GBP",
        "Pound Sterling",
        "£",
        ("GB",),
        "826",
    ),
    (
        "KES",
        "Kenyan Shilling",
        "KSh",
        ("KE",),
        "404",
    ),
    (
        "MWK",
        "Malawian Kwacha",
        "MK",
        ("MW",),
        "454",
    ),
    (
        "NZD",
        "New Zealand Dollar",
        "NZ$",
        ("NZ",),
        "554",
    ),
    (
        "RWF",
        "Rwandan Franc",
        "FRw",
        ("RW",),
        "646",
    ),
    (
        "TZS",
        "Tanzanian Shilling",
        "TSh",
        ("TZ",),
        "834",
    ),
    (
        "UGX",
        "Ugandan Shilling",
        "USh",
        ("UG",),
        "800",
    ),
    (
        "USD",
        "US Dollar",
        "$",
        ("US",),
        "840",
    ),
    (
        "ZAR",
        "South African Rand",
        "R",
        ("ZA",),
        "710",
    ),
    (
        "ZMW",
        "Zambian Kwacha",
        "ZK",
        ("ZM",),
        "967",
    ),
)


def _build_standard_currency_definitions(
) -> tuple[CurrencyDefinition, ...]:
    definitions = tuple(
        CurrencyDefinition.create(
            currency_definition_id=f"currency-{code}",
            currency=code,
            name=name,
            symbol=symbol,
            currency_type=CurrencyType.FIAT,
            status=CurrencyStatus.ACTIVE,
            country_codes=country_codes,
            numeric_code=numeric_code,
            metadata={
                "catalogue": "novapay-standard",
                "source": "canonical",
            },
        )
        for (
            code,
            name,
            symbol,
            country_codes,
            numeric_code,
        ) in _STANDARD_CURRENCY_ROWS
    )

    return tuple(
        sorted(
            definitions,
            key=lambda definition: definition.code,
        )
    )


STANDARD_CURRENCY_DEFINITIONS: tuple[
    CurrencyDefinition,
    ...,
] = _build_standard_currency_definitions()


def standard_currency_definitions(
) -> tuple[CurrencyDefinition, ...]:
    """Return the immutable standard NovaPay catalogue."""

    return tuple(STANDARD_CURRENCY_DEFINITIONS)


def standard_currency_registry(
    *,
    currency_registry_id: object = (
        "novapay-standard-currency-registry"
    ),
    metadata: object = None,
) -> CurrencyRegistry:
    """Construct a fresh immutable standard currency registry."""

    registry_metadata = {
        "catalogue": "novapay-standard",
        "definition_count": len(
            STANDARD_CURRENCY_DEFINITIONS
        ),
    }

    if metadata is not None:
        if not isinstance(metadata, Mapping):
            raise TypeError(
                "standard currency registry metadata "
                "must be a mapping"
            )

        registry_metadata.update(metadata)

    return CurrencyRegistry.create(
        currency_registry_id=currency_registry_id,
        definitions=STANDARD_CURRENCY_DEFINITIONS,
        metadata=registry_metadata,
    )


__all__ = [
    "CurrencyCountryCodes",
    "CurrencyDefinition",
    "CurrencyDefinitionId",
    "CurrencyMetadata",
    "CurrencyName",
    "CurrencyRegistry",
    "CurrencyRegistryId",
    "CurrencyRoundingMode",
    "CurrencyStatus",
    "CurrencySymbol",
    "CurrencyType",
    "STANDARD_CURRENCY_DEFINITIONS",
    "standard_currency_definitions",
    "standard_currency_registry",
]
