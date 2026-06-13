"""Monitoring helpers for AfriPay Django API."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.utils import timezone

from afriride_system.django_app.apps.afripay.models import (
    APIKeyCredential,
    EventRecord,
    IdempotencyKey,
    LiquidityPool,
    OAuthClient,
    PaymentRoute,
    Transaction,
)


@dataclass(frozen=True)
class MonitoringSnapshot:
    counters: dict[str, int]
    histograms: dict[str, list[float]]
    alerts: tuple[dict[str, Any], ...]


def build_snapshot() -> MonitoringSnapshot:
    tx_counts = Counter(Transaction.objects.values_list("status", flat=True))
    route_latencies = list(
        PaymentRoute.objects.exclude(latency_ms__isnull=True).values_list("latency_ms", flat=True)
    )
    alert_items = list(_alerts_from_pools()) + list(_alerts_from_auth()) + list(_alerts_from_data())
    counters = {
        "transactions_total": Transaction.objects.count(),
        "routes_total": PaymentRoute.objects.count(),
        "events_total": EventRecord.objects.count(),
        "idempotency_keys_total": IdempotencyKey.objects.count(),
        "oauth_clients_total": OAuthClient.objects.count(),
        "api_keys_total": APIKeyCredential.objects.count(),
        "transactions_success_total": tx_counts.get("success", 0),
        "transactions_failed_total": tx_counts.get("failed", 0),
        "transactions_pending_total": tx_counts.get("pending", 0),
    }
    histograms = {
        "route_latency_ms": [float(latency) for latency in route_latencies],
    }
    return MonitoringSnapshot(counters=counters, histograms=histograms, alerts=tuple(alert_items))


def prometheus_text() -> str:
    snapshot = build_snapshot()
    lines = [
        "# HELP afripay_transactions_total Total AfriPay transactions by status.",
        "# TYPE afripay_transactions_total counter",
    ]
    for key, value in snapshot.counters.items():
        lines.append(f"afripay_{key} {value}")
    if snapshot.histograms["route_latency_ms"]:
        count = len(snapshot.histograms["route_latency_ms"])
        total = sum(snapshot.histograms["route_latency_ms"])
        lines.append("# HELP afripay_route_latency_ms Route latency histogram surrogate.")
        lines.append("# TYPE afripay_route_latency_ms summary")
        lines.append(f"afripay_route_latency_ms_count {count}")
        lines.append(f"afripay_route_latency_ms_sum {total}")
    for alert in snapshot.alerts:
        labels = ",".join(f'{key}="{value}"' for key, value in alert["labels"].items())
        lines.append(f"afripay_alert{{{labels}}} {alert['value']}")
    return "\n".join(lines) + "\n"


def _alerts_from_pools() -> list[dict[str, Any]]:
    alerts = []
    for pool in LiquidityPool.objects.all():
        if pool.available_balance <= pool.low_watermark:
            alerts.append(
                {
                    "name": "low_liquidity",
                    "value": 1,
                    "labels": {
                        "provider": pool.provider,
                        "currency": pool.currency,
                        "pool_id": pool.pool_id,
                    },
                }
            )
    return alerts


def _alerts_from_auth() -> list[dict[str, Any]]:
    alerts = []
    now = timezone.now()
    for client in OAuthClient.objects.filter(is_active=False):
        alerts.append(
            {
                "name": "oauth_client_inactive",
                "value": 1,
                "labels": {"client_id": client.client_id, "name": client.name},
            }
        )
    for key in APIKeyCredential.objects.filter(is_active=False):
        alerts.append(
            {
                "name": "api_key_inactive",
                "value": 1,
                "labels": {"key_id": key.key_id, "name": key.name},
            }
        )
    for key in APIKeyCredential.objects.filter(suspended_until__gt=now):
        alerts.append(
            {
                "name": "api_key_suspended",
                "value": 1,
                "labels": {"key_id": key.key_id, "name": key.name},
            }
        )
    return alerts


def _alerts_from_data() -> list[dict[str, Any]]:
    alerts = []
    expired_keys = IdempotencyKey.objects.filter(expires_at__lt=timezone.now()).count()
    if expired_keys:
        alerts.append(
            {
                "name": "expired_idempotency_keys",
                "value": expired_keys,
                "labels": {"bucket": "idempotency"},
            }
        )
    return alerts
