from __future__ import annotations

from typing import Any

from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


class EventStreamingService:
    """Kafka-like durable event stream surface backed by the control store."""

    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()

    def create_topic(
        self,
        *,
        organization_id: str,
        topic_name: str,
        description: str = "",
        retention_days: int = 0,
        backend_name: str = "db-stream",
        provider: str = "sqlite",
        region: str = "global",
        partitions: int = 1,
    ) -> dict[str, Any]:
        self.repository.register_stream_backend(
            organization_id=organization_id,
            backend_name=backend_name,
            provider=provider,
            region=region,
            partitions=partitions,
        )
        return self.repository.store_stream_topic(
            organization_id=organization_id,
            topic_name=topic_name,
            description=description,
            retention_days=retention_days,
        )

    def topics(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_stream_topics(organization_id=organization_id)

    def backends(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_stream_backends(organization_id=organization_id)

    def register_backend(
        self,
        *,
        organization_id: str,
        backend_name: str,
        provider: str,
        region: str,
        partitions: int,
    ) -> dict[str, Any]:
        return self.repository.register_stream_backend(
            organization_id=organization_id,
            backend_name=backend_name,
            provider=provider,
            region=region,
            partitions=partitions,
        )

    def scale_backend(
        self,
        *,
        organization_id: str,
        backend_name: str,
        partitions: int,
    ) -> dict[str, Any]:
        backend = next(
            (
                item
                for item in self.repository.list_stream_backends(organization_id=organization_id)
                if item["backend_name"] == backend_name
            ),
            None,
        )
        if backend is None:
            raise KeyError(backend_name)
        return self.repository.register_stream_backend(
            organization_id=organization_id,
            backend_name=backend_name,
            provider=backend["provider"],
            region=backend["region"],
            partitions=partitions,
            status=backend["status"],
        )

    def publish(
        self,
        *,
        organization_id: str,
        topic_name: str,
        event_type: str,
        payload: dict[str, Any],
        partition_key: str = "",
        headers: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.repository.publish_stream_event(
            organization_id=organization_id,
            topic_name=topic_name,
            event_type=event_type,
            payload=payload,
            partition_key=partition_key,
            headers=headers,
        )

    def consume(
        self,
        *,
        organization_id: str | None = None,
        topic_name: str | None = None,
        after_offset: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return self.repository.list_stream_events(
            organization_id=organization_id,
            topic_name=topic_name,
            after_offset=after_offset,
            limit=limit,
        )


__all__ = ["EventStreamingService"]
