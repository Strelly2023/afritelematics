import logging
from pathlib import Path
import uuid
import time
from collections import defaultdict

from rest_framework.response import Response
from rest_framework import status

from afritech.api.auth_models import ApiKey
from afritech.monitoring.alerts import send_integrity_alert

# ✅ Security layers
from afritech.security.ip_control import (
    is_rate_limited,
    is_blocked,
    block_ip,
    record_failure,
    is_brute_force,
)

# ✅ Adaptive rate limit
from afritech.security.rate_limit import (
    is_rate_limited as client_rate_limited,
    detect_burst,
    adapt_rate_limit,
)

# ✅ Anomaly detection
from afritech.security.anomaly import (
    record_request,
    record_failure as record_client_failure,
    detect_anomaly,
)

# ✅ ML + AI
from afritech.security.anomaly_ml import predict_anomaly
from afritech.security.ai_anomaly_engine import detect_ai_anomaly


logger = logging.getLogger(__name__)

FAILED_ATTEMPTS = defaultdict(list)

# Allow this legacy module to coexist with the newer afritech/api/auth/
# package-style helpers such as afritech.api.auth.jwt_device_auth.
__path__ = [str(Path(__file__).with_suffix(""))]


def require_api_key(view_func):

    def wrapper(request, *args, **kwargs):

        request_id = str(uuid.uuid4())
        client_ip = request.META.get("REMOTE_ADDR", "unknown")
        start_time = time.time()

        try:
            logger.info(f"[AUTH_START] id={request_id} ip={client_ip}")

            # =====================================================
            # ✅ IP DEFENSE
            # =====================================================
            if is_blocked(client_ip):
                send_integrity_alert(
                    "BLOCKED_IP_ACCESS_ATTEMPT",
                    "HIGH",
                    {"ip": client_ip, "request_id": request_id}
                )
                return Response({"error": "IP blocked"}, status=403)

            if is_rate_limited(client_ip):
                block_ip(client_ip)
                send_integrity_alert(
                    "IP_RATE_LIMIT_EXCEEDED",
                    "HIGH",
                    {"ip": client_ip}
                )
                return Response({"error": "Too many requests"}, status=429)

            # =====================================================
            # ✅ API KEY EXTRACTION
            # =====================================================
            header = request.headers.get("Authorization")

            if not header:
                return Response({"error": "Missing API key"}, status=401)

            if not header.startswith("Api-Key "):
                return Response({"error": "Invalid API key format"}, status=401)

            raw_key = header.split(" ", 1)[1].strip()

            if not raw_key:
                return Response({"error": "Empty API key"}, status=401)

            # =====================================================
            # ✅ HASHED KEY LOOKUP
            # =====================================================
            key_hash = ApiKey.hash_key(raw_key)

            try:
                api_key = ApiKey.objects.get(key_hash=key_hash)

            except ApiKey.DoesNotExist:
                record_failure(client_ip)
                FAILED_ATTEMPTS[client_ip].append(time.time())

                if is_brute_force(client_ip):
                    block_ip(client_ip)

                send_integrity_alert(
                    "INVALID_API_KEY_ATTEMPT",
                    "HIGH",
                    {"ip": client_ip, "request_id": request_id}
                )

                return Response({"error": "Invalid API key"}, status=403)

            # =====================================================
            # ✅ STATUS CHECK (ACTIVE / SUSPENDED / REVOKED)
            # =====================================================
            if not api_key.is_active:
                return Response({"error": "API key revoked"}, status=403)

            if api_key.is_suspended():
                return Response({"error": "API key suspended"}, status=403)

            # =====================================================
            # ✅ CLIENT RATE LIMIT
            # =====================================================
            if client_rate_limited(api_key.name):
                adapt_rate_limit(api_key.name, "abusive")

                send_integrity_alert(
                    "CLIENT_RATE_LIMIT_EXCEEDED",
                    "HIGH",
                    {"client": api_key.name}
                )

                return Response({"error": "Client rate limit exceeded"}, status=429)

            # =====================================================
            # ✅ CONTEXT ATTACHMENT
            # =====================================================
            request.api_client = api_key
            request.request_id = request_id
            request.client_ip = client_ip

            # =====================================================
            # ✅ CALL VIEW (MEASURE PERFORMANCE)
            # =====================================================
            response = view_func(request, *args, **kwargs)

            duration_ms = (time.time() - start_time) * 1000

            # =====================================================
            # ✅ RECORD METRICS
            # =====================================================
            record_request(api_key.name, duration_ms)

            if response.status_code >= 400:
                record_client_failure(api_key.name)
                api_key.record_failure()
            else:
                api_key.reset_failures()
                adapt_rate_limit(api_key.name, "trusted")

            # =====================================================
            # ✅ ANOMALY DETECTION
            # =====================================================
            anomaly = detect_anomaly(api_key.name)

            if anomaly["anomaly"]:
                send_integrity_alert(
                    "ANOMALY_DETECTED",
                    anomaly["severity"],
                    {"client": api_key.name, "details": anomaly}
                )

            # =====================================================
            # ✅ ML ANOMALY
            # =====================================================
            ml_result = predict_anomaly([
                api_key.request_count,
                duration_ms,
                api_key.failure_count,
            ])

            if ml_result:
                send_integrity_alert(
                    "ML_ANOMALY_DETECTED",
                    "CRITICAL",
                    {"client": api_key.name}
                )

            # =====================================================
            # ✅ AI ANOMALY ENGINE
            # =====================================================
            ai_result = detect_ai_anomaly({
                "failure_count": api_key.failure_count,
                "requests": api_key.request_count,
                "latency": duration_ms,
            })

            if ai_result["anomaly"]:
                send_integrity_alert(
                    "AI_ANOMALY_DETECTED",
                    ai_result["risk"],
                    {
                        "client": api_key.name,
                        "score": ai_result["score"],
                        "signals": ai_result.get("signals"),
                    }
                )

            logger.info(
                f"[AUTH_OK] client={api_key.name} "
                f"time={round(duration_ms,2)}ms id={request_id}"
            )

            return response

        except Exception:
            logger.exception(f"[AUTH_ERROR] id={request_id}")

            send_integrity_alert(
                "AUTH_SYSTEM_FAILURE",
                "CRITICAL",
                {"ip": client_ip, "request_id": request_id}
            )

            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return wrapper
