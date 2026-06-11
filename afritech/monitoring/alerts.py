import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)


def _maybe_django_settings():
    try:
        from django.conf import settings  # pragma: no cover - exercised in Django runtime
    except ModuleNotFoundError:
        return None
    except Exception:
        return None

    try:
        if not settings.configured:
            return None
    except Exception:
        return None

    return settings


def _runtime_timestamp() -> str:
    try:
        from django.utils import timezone as django_timezone  # pragma: no cover - exercised in Django runtime
    except ModuleNotFoundError:
        return datetime.now(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()
    return django_timezone.now().isoformat()


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def send_integrity_alert(
    event_type: str,
    severity: str = "HIGH",
    details: Dict[str, Any] | None = None,
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
        # Backward compatibility for older callsites that passed details second.
        if isinstance(severity, dict):
            details = severity
            severity = "HIGH"

        settings = _maybe_django_settings()

        # =====================================================
        # ✅ BUILD ALERT OBJECT
        # =====================================================
        alert = {
            "id": str(uuid.uuid4()),
            "timestamp": _runtime_timestamp(),
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
        email_enabled = getattr(settings, "ALERT_EMAIL_ENABLED", False) if settings else _env_flag("ALERT_EMAIL_ENABLED")
        if severity in ("HIGH", "CRITICAL") and email_enabled and settings:
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
        webhook_url = getattr(settings, "ALERT_WEBHOOK_URL", None) if settings else os.environ.get("ALERT_WEBHOOK_URL")

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
