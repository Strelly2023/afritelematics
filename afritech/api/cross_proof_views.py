import logging
import time

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from afritech.api.auth import require_api_key
from afritech.services.cross_proof_verifier import verify_cross_system_proof
from afritech.monitoring.alerts import send_integrity_alert


logger = logging.getLogger(__name__)


# =====================================================
# ✅ VERIFY CROSS-SYSTEM PROOF
# =====================================================

@api_view(["POST"])
@require_api_key
def verify_cross_proof_view(request):
    """
    Verify cross-system proof (ADR-0014 compliant).

    Features:
    - Zero-trust verification
    - Full pipeline validation (Merkle + Signature)
    - Security alerting
    - Request tracing
    - Performance monitoring
    """

    start_time = time.perf_counter()

    try:
        api_key = request.api_client
        client_name = api_key.name
        client_ip = request.client_ip
        request_id = request.request_id

        logger.info(
            f"[CROSS_PROOF] START client={client_name} "
            f"ip={client_ip} id={request_id}"
        )

        # =====================================================
        # ✅ INPUT VALIDATION
        # =====================================================
        proof = request.data

        if not proof:
            return Response(
                {"error": "Empty request body"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(proof, dict):
            return Response(
                {"error": "Invalid proof format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =====================================================
        # ✅ VERIFY PROOF
        # =====================================================
        is_valid = verify_cross_system_proof(proof)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # =====================================================
        # 🚨 FAILURE HANDLING
        # =====================================================
        if not is_valid:
            api_key.record_failure()

            send_integrity_alert(
                event_type="CROSS_PROOF_VERIFICATION_FAILED",
                severity="CRITICAL",
                details={
                    "client": client_name,
                    "ip": client_ip,
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                    "failure_count": api_key.failure_count,
                },
            )

            logger.warning(
                f"[CROSS_PROOF_FAIL] client={client_name} "
                f"id={request_id}"
            )

        else:
            # ✅ reset failures on success
            api_key.reset_failures()

        # =====================================================
        # ⚡ PERFORMANCE MONITORING
        # =====================================================
        if duration_ms > 120:
            send_integrity_alert(
                event_type="SLOW_CROSS_PROOF_VERIFICATION",
                severity="MEDIUM",
                details={
                    "client": client_name,
                    "duration_ms": duration_ms,
                },
            )

        # =====================================================
        # ✅ SUCCESS LOG
        # =====================================================
        logger.info(
            f"[CROSS_PROOF_RESULT] valid={is_valid} "
            f"time={duration_ms}ms client={client_name} "
            f"id={request_id}"
        )

        # =====================================================
        # ✅ RESPONSE
        # =====================================================
        return Response(
            {
                "valid": is_valid,
                "type": "cross_system_proof",
                "client": client_name,
                "duration_ms": duration_ms,
                "request_id": request_id,
            },
            status=status.HTTP_200_OK,
        )

    except Exception:
        logger.exception("[CROSS_PROOF_ERROR]")

        send_integrity_alert(
            event_type="CROSS_PROOF_INTERNAL_ERROR",
            severity="CRITICAL",
            details={
                "client": getattr(request, "api_client", None)
                and request.api_client.name,
                "request_id": getattr(request, "request_id", None),
            },
        )

        return Response(
            {"error": "Internal verification error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
