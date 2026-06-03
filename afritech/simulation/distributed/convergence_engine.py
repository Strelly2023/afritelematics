from __future__ import annotations

from typing import Any

from afritech.simulation.validation_receipt import stable_hash


class ConvergenceError(RuntimeError):
    pass


class ConvergenceEngine:
    def converge(
        self,
        partitions: tuple[tuple[dict[str, Any], ...], ...],
    ) -> tuple[dict[str, Any], ...]:
        seen: set[str] = set()
        merged: list[dict[str, Any]] = []

        for partition in partitions:
            for event in partition:
                partition_id = event.get("partition_id")
                if not isinstance(partition_id, int) or partition_id < 0:
                    raise ConvergenceError("partition identity mismatch")

                event_id = self._event_identity(event)
                if event_id in seen:
                    raise ConvergenceError("duplicate authority branch")
                seen.add(event_id)
                merged.append(dict(event))

        return tuple(
            sorted(
                merged,
                key=lambda event: (
                    int(event["partition_id"]),
                    int(event["partition_sequence"]),
                    str(event["request_id"]),
                ),
            )
        )

    def convergence_hash(
        self,
        converged_events: tuple[dict[str, Any], ...],
    ) -> str:
        return stable_hash(converged_events)

    def _event_identity(self, event: dict[str, Any]) -> str:
        for key in ("request_id", "trip_id", "ride_id"):
            value = event.get(key)
            if value is not None:
                return f"{key}:{value}"
        raise ConvergenceError("event lacks canonical identity")
