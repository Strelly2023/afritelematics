from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from afritech.simulation.distributed.network_trace import NetworkTrace


class MessageScheduler:
    def schedule(
        self,
        messages: Iterable[Mapping[str, Any]],
    ) -> tuple[dict[str, Any], ...]:
        """Return canonical message order independent of arrival order."""

        return tuple(
            dict(message)
            for message in sorted(
                messages,
                key=lambda message: (
                    int(message["timestamp"]),
                    str(message["id"]),
                    NetworkTrace.hash_trace(dict(message)),
                ),
            )
        )
