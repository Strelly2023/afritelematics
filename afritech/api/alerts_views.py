import logging
import time
from typing import Dict, Any, List

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


# =====================================================
# ✅ IN-MEMORY ALERT STORAGE (Replace with DB / Redis later)
# =====================================================

ALERT_LOG: List[Dict[str, Any]] = []

MAX_ALERTS = 500


# =====================================================
# ✅ ALERT LOGGER
# =====================================================

def log_alert(alert: Dict[str, Any]):
    """
    Store alert in memory (FIFO buffer).
    """

    try:
        # ✅ enrich alert automatically
        alert_entry = {
            "timestamp": time.time(),
            **alert,
        }

        ALERT_LOG.append(alert_entry)

        # ✅ prevent memory overflow
        if len(ALERT_LOG) > MAX_ALERTS:
            ALERT_LOG.pop(0)

    except Exception:
        logger.exception("[ALERT_LOG_ERROR]")


# =====================================================
# ✅ ALERTS API VIEW
# =====================================================

@api_view(["GET"])
def alerts_view(request):
    """
    Return recent alerts for dashboard.

    Query params:
        ?limit=50
        ?severity=CRITICAL
    """

    try:
        limit = int(request.GET.get("limit", 100))
        severity_filter = request.GET.get("severity")

        # ✅ safe limit bounds
        limit = max(1, min(limit, 500))

        alerts = ALERT_LOG[-limit:]

        # ✅ filter by severity
        if severity_filter:
            alerts = [
                a for a in alerts
                if a.get("severity") == severity_filter.upper()
            ]

        # ✅ reverse order (latest first)
        alerts = list(reversed(alerts))

        return Response({
            "count": len(alerts),
            "alerts": alerts,
        })

    except Exception:
        logger.exception("[ALERTS_VIEW_ERROR]")

        return Response(
            {"error": "Failed to fetch alerts"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
