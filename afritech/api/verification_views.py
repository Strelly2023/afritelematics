import time
import logging
from collections import defaultdict

from rest_framework.decorators import api_view

from rest_framework.response import Response
from rest_framework import status

from afritech.api.auth import require_api_key
from afritech.services.audit_proof_verifier import (
    verify_audit_proof,
    verify_log_proof,
)
from afritech.monitoring.alerts import send_integrity_alert

# ✅ Anomaly systems
from afritech.security.anomaly import (
    record_request,
    record_failure,
    detect_anomaly,
    detect_ai_anomaly,
)

# ✅ ML system
from afritech.security.anomaly_ml import predict_anomaly

# ✅ Adaptive rate feedback
from afritech.security.rate_limit import adapt_rate_limit


logger = logging.getLogger(__name__)


# =====================================================
# ✅ VERIFY FULL PROOF
# =====================================================
@api_view(["POST"])
@require_api_key
def verify_proof_view(request):

    start_time = time.perf_counter()

    try:
        api_key = request.api_client
        client_name = api_key.name
        client_ip = request.client_ip
        request_id = request.request_id

        logger.info(
            f"[FULL_PROOF] START client={client_name} ip={client_ip} id={request_id}"
        )

        proof_data = request.data

        if not proof_data:
            return Response(
                {"error": "Empty request body"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =====================================================
        # ✅ VERIFY
        # =====================================================
        is_valid = verify_audit_proof(proof_data)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # =====================================================
        # 🚨 FAILURE / SUCCESS HANDLING
        # =====================================================
        if not is_valid:
            api_key.record_failure()
            record_failure(client_name)

            adapt_rate_limit(client_name, "abusive")

            send_integrity_alert(
                "FULL_PROOF_TAMPER_DETECTED",
                "CRITICAL",
                {
                    "client": client_name,
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                    "failures": api_key.failure_count,
                },
            )
        else:
            api_key.reset_failures()
            adapt_rate_limit(client_name, "trusted")

        # =====================================================
        # 📊 RECORD METRICS
        # =====================================================
        record_request(client_name, duration_ms)

        # =====================================================
        # 🧠 STATISTICAL ANOMALY
        # =====================================================
        anomaly = detect_anomaly(client_name)

        if anomaly["anomaly"]:
            send_integrity_alert(
                "ANOMALY_DETECTED",
                anomaly["severity"],
                {
                    "client": client_name,
                    "details": anomaly,
                },
            )

        # =====================================================
        # 🤖 ML ANOMALY
        # =====================================================
        ml_flag = predict_anomaly([
            api_key.request_count,
            duration_ms,
            api_key.failure_count,
        ])

        if ml_flag:
            send_integrity_alert(
                "ML_ANOMALY_DETECTED",
                "CRITICAL",
                {"client": client_name}
            )

        # =====================================================
        # 🧠 AI ANOMALY ENGINE
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
                    "client": client_name,
                    "score": ai_result["score"],
                    "signals": ai_result.get("signals"),
                },
            )

        # =====================================================
        # ⚡ PERFORMANCE ALERT
        # =====================================================
        if duration_ms > 100:
            send_integrity_alert(
                "SLOW_FULL_PROOF_VERIFICATION",
                "MEDIUM",
                {"client": client_name, "duration_ms": duration_ms},
            )

        logger.info(
            f"[FULL_PROOF] RESULT={is_valid} TIME={duration_ms}ms CLIENT={client_name}"
        )

        return Response(
            {
                "valid": is_valid,
                "type": "full_proof",
                "client": client_name,
                "duration_ms": duration_ms,
                "request_id": request_id,
            },
            status=status.HTTP_200_OK,
        )

    except Exception:
        logger.exception("FULL_PROOF_ERROR")

        send_integrity_alert(
            "FULL_PROOF_INTERNAL_ERROR",
            "HIGH",
            {
                "client": getattr(request, "api_client", None)
                and request.api_client.name,
                "request_id": getattr(request, "request_id", None),
            },
        )

        return Response(
            {"error": "Internal verification error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# =====================================================
# ✅ VERIFY LOG PROOF
# =====================================================
@api_view(["POST"])
@require_api_key
def verify_log_proof_view(request):

    start_time = time.perf_counter()

    try:
        api_key = request.api_client
        client_name = api_key.name
        client_ip = request.client_ip
        request_id = request.request_id

        logger.info(
            f"[LOG_PROOF] START client={client_name} ip={client_ip} id={request_id}"
        )

        proof_data = request.data

        if not proof_data:
            return Response(
                {"error": "Empty request body"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =====================================================
        # ✅ VERIFY
        # =====================================================
        is_valid = verify_log_proof(proof_data)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # =====================================================
        # 🚨 FAILURE / SUCCESS HANDLING
        # =====================================================
        if not is_valid:
            api_key.record_failure()
            record_failure(client_name)

            adapt_rate_limit(client_name, "abusive")

            send_integrity_alert(
                "LOG_PROOF_TAMPER_DETECTED",
                "CRITICAL",
                {
                    "client": client_name,
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                },
            )
        else:
            api_key.reset_failures()
            adapt_rate_limit(client_name, "trusted")

        # =====================================================
        # 📊 RECORD METRICS
        # =====================================================
        record_request(client_name, duration_ms)

        # =====================================================
        # 🧠 ANOMALY
        # =====================================================
        anomaly = detect_anomaly(client_name)

        if anomaly["anomaly"]:
            send_integrity_alert(
                "ANOMALY_DETECTED",
                anomaly["severity"],
                {"client": client_name, "details": anomaly},
            )

        # =====================================================
        # 🤖 ML
        # =====================================================
        if predict_anomaly([
            api_key.request_count,
            duration_ms,
            api_key.failure_count,
        ]):
            send_integrity_alert(
                "ML_ANOMALY_DETECTED",
                "CRITICAL",
                {"client": client_name},
            )

        # =====================================================
        # 🧠 AI ENGINE
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
                    "client": client_name,
                    "score": ai_result["score"],
                },
            )

        # =====================================================
        # ⚡ PERFORMANCE ALERT
        # =====================================================
        if duration_ms > 50:
            send_integrity_alert(
                "SLOW_LOG_PROOF_VERIFICATION",
                "LOW",
                {"client": client_name, "duration_ms": duration_ms},
            )

        logger.info(
            f"[LOG_PROOF] RESULT={is_valid} TIME={duration_ms}ms CLIENT={client_name}"
        )

        return Response(
            {
                "valid": is_valid,
                "type": "log_proof",
                "client": client_name,
                "duration_ms": duration_ms,
                "request_id": request_id,
            }
        )

    except Exception:
        logger.exception("LOG_PROOF_ERROR")

        send_integrity_alert(
            "LOG_PROOF_INTERNAL_ERROR",
            "HIGH",
            {
                "client": getattr(request, "api_client", None)
                and request.api_client.name,
                "request_id": getattr(request, "request_id", None),
            },
        )

        return Response(
            {"error": "Internal verification error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
