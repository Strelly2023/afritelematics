import time
import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

from afritech.security.anomaly import (
    REQUEST_TIMESTAMPS,
    LATENCY_TRACKER,
    FAILURE_TRACKER,
)
from afritech.security.rate_limit import CLIENT_LIMITS
from afritech.security.ip_control import BLOCKED_IPS


logger = logging.getLogger(__name__)


@api_view(["GET"])
def metrics_view(request):
    """
    Production-grade metrics endpoint for observability dashboard.

    Provides:
    - per-client usage stats
    - latency metrics
    - failure rates
    - rate limits
    - blocked IP visibility
    """

    try:
        now = time.time()

        clients_data = []
        total_requests = 0
        total_failures = 0

        # =====================================================
        # ✅ CLIENT METRICS
        # =====================================================
        for client, timestamps in REQUEST_TIMESTAMPS.items():

            # ✅ Recent requests (within window)
            requests_count = len(timestamps)

            latencies = LATENCY_TRACKER.get(client, [])
            failures = FAILURE_TRACKER.get(client, [])

            avg_latency = (
                sum(latencies) / len(latencies)
                if latencies else 0
            )

            max_latency = max(latencies) if latencies else 0

            failure_count = len(failures)

            total_requests += requests_count
            total_failures += failure_count

            # ✅ Health status classification
            health = "healthy"

            if failure_count > 5:
                health = "critical"
            elif failure_count > 2:
                health = "warning"

            clients_data.append({
                "client": client,
                "requests": requests_count,
                "failures": failure_count,
                "avg_latency_ms": round(avg_latency, 2),
                "max_latency_ms": round(max_latency, 2),
                "rate_limit": CLIENT_LIMITS.get(client, 60),
                "health": health,
            })

        # =====================================================
        # ✅ BLOCKED IP DETAILS
        # =====================================================
        blocked_ips_data = []

        for ip, expiry in BLOCKED_IPS.items():
            remaining = max(0, int(expiry - now))

            blocked_ips_data.append({
                "ip": ip,
                "blocked": remaining > 0,
                "expires_in_seconds": remaining,
            })

        # =====================================================
        # ✅ SUMMARY (FOR DASHBOARD)
        # =====================================================
        summary = {
            "total_clients": len(clients_data),
            "total_requests": total_requests,
            "total_failures": total_failures,
            "blocked_ips": len(blocked_ips_data),
            "timestamp": int(now),
        }

        return Response({
            "summary": summary,
            "clients": clients_data,
            "blocked_ips": blocked_ips_data,
        })

    except Exception as e:
        logger.exception("[METRICS_ERROR]")

        return Response({
            "error": "Failed to load metrics"
        }, status=500)
