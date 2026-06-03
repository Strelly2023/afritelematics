import logging
import uuid
from typing import Dict, Any

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_integrity_alert(
    event_type: str,
    details: Dict[str, Any],
    severity: str = "HIGH",
):
    """
    Central alert dispatcher for integrity/security events.

    Args:
        event_type: Type of alert (e.g. FULL_PROOF_TAMPER_DETECTED)
        details: Context data (client, IP, payload info, etc.)
        severity: LOW | MEDIUM | HIGH | CRITICAL

    Features:
        ✔ Structured logging
        ✔ Unique alert ID (traceability)
        ✔ Safe execution (never crashes caller)
        ✔ Extensible integrations
    """

    try:
        # =====================================================
        # ✅ BUILD ALERT OBJECT
        # =====================================================
        alert = {
            "id": str(uuid.uuid4()),
            "timestamp": timezone.now().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "service": "afritech-audit",
            "details": details or {},
        }

        # =====================================================
        # ✅ STRUCTURED LOGGING
        # =====================================================
        log_message = f"🚨 INTEGRITY ALERT [{severity}] {event_type}"

        if severity == "CRITICAL":
            logger.critical(log_message, extra={"alert": alert})
        elif severity == "HIGH":
            logger.error(log_message, extra={"alert": alert})
        elif severity == "MEDIUM":
            logger.warning(log_message, extra={"alert": alert})
        else:
            logger.info(log_message, extra={"alert": alert})

        # =====================================================
        # ✅ OPTIONAL: EMAIL ALERTS
        # =====================================================
        if severity in ("HIGH", "CRITICAL") and getattr(settings, "ALERT_EMAIL_ENABLED", False):
            try:
                from django.core.mail import send_mail

                send_mail(
                    subject=f"[ALERT] {event_type}",
                    message=str(alert),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=getattr(settings, "ALERT_EMAIL_RECIPIENTS", []),
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Email alert failed: {e}")

        # =====================================================
        # ✅ OPTIONAL: WEBHOOK (Slack / Monitoring)
        # =====================================================
        webhook_url = getattr(settings, "ALERT_WEBHOOK_URL", None)

        if webhook_url:
            try:
                import requests

                requests.post(
                    webhook_url,
                    json=alert,
                    timeout=2,
                )
            except Exception as e:
                logger.error(f"Webhook alert failed: {e}")

        # =====================================================
        # ✅ OPTIONAL: FUTURE EXTENSIONS
        # =====================================================
        # - push to Kafka
        # - store in DB (Alert model)
        # - send SMS
        # - integrate with Prometheus / Grafana

        return alert

    except Exception as e:
        # ✅ NEVER break main flow
        logger.exception("Integrity alert system failure")

        return {
            "error": "alert_dispatch_failed",
            "event_type": event_type,
        }
