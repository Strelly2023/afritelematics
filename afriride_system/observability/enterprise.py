"""Enterprise operational metrics aggregation."""

from __future__ import annotations

from collections import defaultdict, deque
from threading import RLock
from time import perf_counter
from typing import Any

from starlette.requests import Request

from afriride_system.operations.fleet_twin import build_fleet_twin
from afriride_system.payments.modern import PaymentRepository


class ApiMetrics:
    def __init__(self) -> None:
        self._latencies: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=2000))
        self._statuses: dict[int, int] = defaultdict(int)
        self._lock = RLock()

    def observe(self, path: str, status: int, milliseconds: float) -> None:
        route = _route_family(path)
        with self._lock:
            self._latencies[route].append(milliseconds)
            self._statuses[status] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            routes = {
                route: {
                    "count": len(values),
                    "p50_ms": _percentile(values, 0.50),
                    "p95_ms": _percentile(values, 0.95),
                    "p99_ms": _percentile(values, 0.99),
                }
                for route, values in self._latencies.items()
            }
            statuses = dict(self._statuses)
        return {"routes": routes, "status_counts": statuses}


api_metrics = ApiMetrics()


async def api_metrics_middleware(request: Request, call_next):
    started = perf_counter()
    response = await call_next(request)
    api_metrics.observe(request.url.path, response.status_code, (perf_counter() - started) * 1000)
    return response


def enterprise_dashboard(gateway, trust_metrics: dict[str, Any]) -> dict[str, Any]:
    twin = build_fleet_twin(gateway)
    telemetry = gateway.fleet_operations_repository.telemetry()
    accuracy = [float(row["accuracy_m"]) for row in telemetry if row["accuracy_m"] is not None]
    outbox = gateway.push_outbox_repository
    pending = outbox.pending(1000)
    with outbox.storage.connect() as connection:
        notification_rows = connection.execute(
            "SELECT status, COUNT(*) AS count FROM mobile_push_outbox GROUP BY status"
        ).fetchall()
    return {
        "contract": "afriride.observability.v1",
        "fleet_health": twin["fleet_health"],
        "dispatch_latency": api_metrics.snapshot()["routes"].get("/v1/operations", {}),
        "queue_depth": twin["queue_lengths"],
        "notification_delivery": {
            "by_status": {row["status"]: row["count"] for row in notification_rows},
            "pending": len(pending),
        },
        "gps_quality": {
            "samples": len(accuracy),
            "average_accuracy_m": round(sum(accuracy) / len(accuracy), 2) if accuracy else None,
            "poor_samples": sum(value > 100 for value in accuracy),
        },
        "api_latency": api_metrics.snapshot(),
        "payment_health": PaymentRepository(gateway.storage).health(),
        "trust_metrics": trust_metrics,
    }


def _route_family(path: str) -> str:
    parts = path.rstrip("/").split("/")
    return "/" + "/".join(parts[1:3]) if len(parts) > 2 else path


def _percentile(values, percentile: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * percentile))
    return round(ordered[index], 2)
