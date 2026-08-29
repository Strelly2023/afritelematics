"""PostgreSQL persistence for NovaRide delivery execution.

NovaRide currently exposes one logistics persistence contract:

    RuntimeRepositories.deliveries

Broader logistics, freight, shipment, manifest, route, warehouse, and
supply-chain responsibilities remain outside this NovaRide persistence slice.

The canonical ``delivery_orders`` table predates the aggregate fields
``schema_version`` and ``chain_of_custody``. Both values are persisted inside
the existing ``package_metadata`` JSONB document under reserved NovaRide keys,
allowing full aggregate round-trip without introducing another migration.
"""

from __future__ import annotations

from typing import Any, Mapping

from afritech.novaride_runtime.models import (
    AddressRef,
    DeliveryOrder,
    LogisticsState,
)
from afritech.novaride_runtime.persistence.postgres.base_repository import (
    PostgresAggregateRepository,
    SyncPostgresConnection,
)
from afritech.novaride_runtime.persistence.postgres.unit_of_work import (
    PostgresUnitOfWork,
    PostgresUnitOfWorkConfig,
)


_SCHEMA_VERSION_KEY = "__novaride_schema_version"
_CHAIN_OF_CUSTODY_KEY = "__novaride_chain_of_custody"


def _mapping(
    value: Any,
    *,
    field: str,
) -> dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, Mapping):
        return dict(value)

    raise ValueError(
        f"postgres_{field}_invalid:"
        f"{type(value).__name__}"
    )


def _address_to_json(
    value: AddressRef | None,
    *,
    field: str,
) -> dict[str, Any]:
    if value is None:
        raise ValueError(
            f"postgres_delivery_{field}_required"
        )

    result: dict[str, Any] = {}

    for name in (
        "label",
        "latitude",
        "longitude",
        "place_id",
        "metadata",
    ):
        if not hasattr(value, name):
            continue

        candidate = getattr(
            value,
            name,
        )

        if candidate is not None:
            result[name] = candidate

    if not result and hasattr(
        value,
        "__dict__",
    ):
        result = {
            key: item
            for key, item in vars(value).items()
            if not key.startswith("_")
        }

    if not result:
        result = {
            "label": str(value),
        }

    return result


def _address_from_json(
    value: Any,
    *,
    field: str,
) -> AddressRef:
    payload = _mapping(
        value,
        field=f"delivery_{field}",
    )

    label = payload.get(
        "label",
        payload.get(
            "address",
            payload.get(
                "name",
                "",
            ),
        ),
    )

    try:
        return AddressRef(
            label=str(label),
            latitude=payload.get(
                "latitude"
            ),
            longitude=payload.get(
                "longitude"
            ),
            place_id=payload.get(
                "place_id"
            ),
            metadata=payload.get(
                "metadata",
                {},
            ),
        )
    except TypeError:
        return AddressRef(
            str(label)
        )


def _encode_metadata(
    order: DeliveryOrder,
) -> dict[str, Any]:
    metadata = dict(
        order.package_metadata
    )

    if _SCHEMA_VERSION_KEY in metadata:
        raise ValueError(
            "delivery_package_metadata_"
            "reserved_schema_version_key"
        )

    if _CHAIN_OF_CUSTODY_KEY in metadata:
        raise ValueError(
            "delivery_package_metadata_"
            "reserved_chain_of_custody_key"
        )

    metadata[_SCHEMA_VERSION_KEY] = (
        order.schema_version
    )

    metadata[_CHAIN_OF_CUSTODY_KEY] = list(
        order.chain_of_custody
    )

    return metadata


def _decode_metadata(
    value: Any,
) -> tuple[
    dict[str, Any],
    str,
    tuple[str, ...],
]:
    metadata = _mapping(
        value,
        field="delivery_package_metadata",
    )

    schema_version = str(
        metadata.pop(
            _SCHEMA_VERSION_KEY,
            "2026.2",
        )
    )

    raw_chain = metadata.pop(
        _CHAIN_OF_CUSTODY_KEY,
        (),
    )

    if raw_chain is None:
        chain: tuple[str, ...] = ()
    elif isinstance(
        raw_chain,
        (list, tuple),
    ):
        chain = tuple(
            str(item)
            for item in raw_chain
        )
    else:
        raise ValueError(
            "postgres_delivery_chain_of_custody_invalid:"
            f"{type(raw_chain).__name__}"
        )

    return (
        metadata,
        schema_version,
        chain,
    )


def _encode_delivery(
    order: DeliveryOrder,
) -> Mapping[str, Any]:
    return {
        "order_id": order.id,
        "tenant_id": order.tenant_id,
        "organization_id": (
            order.organization_id
        ),
        "region_code": order.region_code,
        "sender_id": order.sender_id,
        "recipient_name": (
            order.recipient_name
        ),
        "pickup": _address_to_json(
            order.pickup,
            field="pickup",
        ),
        "dropoff": _address_to_json(
            order.dropoff,
            field="dropoff",
        ),
        "package_metadata": (
            _encode_metadata(order)
        ),
        "state": order.state.value,
        "aggregate_version": (
            order.aggregate_version
        ),
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


def _decode_delivery(
    row: Mapping[str, Any],
) -> DeliveryOrder:
    (
        package_metadata,
        schema_version,
        chain_of_custody,
    ) = _decode_metadata(
        row.get(
            "package_metadata"
        )
    )

    return DeliveryOrder(
        id=str(
            row["order_id"]
        ),
        tenant_id=str(
            row["tenant_id"]
        ),
        organization_id=str(
            row["organization_id"]
        ),
        region_code=str(
            row["region_code"]
        ),
        aggregate_version=int(
            row["aggregate_version"]
        ),
        schema_version=(
            schema_version
        ),
        created_at=row[
            "created_at"
        ],
        updated_at=row[
            "updated_at"
        ],
        sender_id=str(
            row["sender_id"]
        ),
        recipient_name=str(
            row["recipient_name"]
        ),
        pickup=_address_from_json(
            row["pickup"],
            field="pickup",
        ),
        dropoff=_address_from_json(
            row["dropoff"],
            field="dropoff",
        ),
        package_metadata=(
            package_metadata
        ),
        state=LogisticsState(
            str(row["state"])
        ),
        chain_of_custody=(
            chain_of_custody
        ),
    )


class PostgresDeliveryRepository(
    PostgresAggregateRepository[
        DeliveryOrder
    ]
):
    """Synchronous NovaRide delivery-order repository."""

    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="delivery_orders",
            id_column="order_id",
            to_record=_encode_delivery,
            from_record=_decode_delivery,
        )


__all__ = [
    "PostgresDeliveryRepository",
    "PostgresUnitOfWork",
    "PostgresUnitOfWorkConfig",
]
