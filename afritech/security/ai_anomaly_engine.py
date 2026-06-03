import logging

logger = logging.getLogger(__name__)


# =====================================================
# ✅ AI ANOMALY DETECTION ENGINE
# =====================================================

def detect_ai_anomaly(context: dict) -> dict:
    """
    AI-style anomaly detection engine.

    context example:
    {
        "failure_count": int,
        "requests": int,
        "latency": float,
        "ip_reputation": optional int,
    }

    Returns:
    {
        anomaly: bool,
        risk: str,
        score: int,
        reason: str,
        signals: dict
    }
    """

    try:
        # =====================================================
        # ✅ SAFE INPUT EXTRACTION
        # =====================================================
        failure_count = context.get("failure_count", 0)
        requests = context.get("requests", 0)
        latency = context.get("latency", 0)
        ip_reputation = context.get("ip_reputation", 0)  # optional signal

        score = 0
        signals = {}

        # =====================================================
        # ✅ SIGNAL 1: FAILURE PATTERN (CRITICAL)
        # =====================================================
        if failure_count > 10:
            score += 7
            signals["failures"] = "extreme"
        elif failure_count > 5:
            score += 5
            signals["failures"] = "high"
        elif failure_count > 2:
            score += 2
            signals["failures"] = "moderate"

        # =====================================================
        # ✅ SIGNAL 2: REQUEST VOLUME
        # =====================================================
        if requests > 500:
            score += 5
            signals["traffic"] = "extreme"
        elif requests > 200:
            score += 3
            signals["traffic"] = "high"
        elif requests > 100:
            score += 1
            signals["traffic"] = "elevated"

        # =====================================================
        # ✅ SIGNAL 3: LATENCY BEHAVIOR
        # =====================================================
        if latency > 500:
            score += 4
            signals["latency"] = "critical"
        elif latency > 200:
            score += 2
            signals["latency"] = "high"

        # =====================================================
        # ✅ SIGNAL 4: IP REPUTATION (OPTIONAL)
        # =====================================================
        if ip_reputation < -5:
            score += 4
            signals["ip_reputation"] = "bad"
        elif ip_reputation < 0:
            score += 2
            signals["ip_reputation"] = "suspicious"

        # =====================================================
        # ✅ RISK CLASSIFICATION
        # =====================================================
        if score >= 9:
            return {
                "anomaly": True,
                "risk": "CRITICAL",
                "score": score,
                "reason": "Severe threat detected (multi-signal anomaly)",
                "signals": signals,
            }

        if score >= 6:
            return {
                "anomaly": True,
                "risk": "HIGH",
                "score": score,
                "reason": "High-risk suspicious behavior",
                "signals": signals,
            }

        if score >= 3:
            return {
                "anomaly": True,
                "risk": "MEDIUM",
                "score": score,
                "reason": "Moderate anomaly detected",
                "signals": signals,
            }

        # ✅ Normal
        return {
            "anomaly": False,
            "risk": "LOW",
            "score": score,
            "reason": "Normal behavior",
            "signals": signals,
        }

    except Exception as e:
        logger.exception("AI anomaly detection failure")

        return {
            "anomaly": False,
            "risk": "UNKNOWN",
            "score": 0,
            "reason": "Detection error",
            "error": str(e),
        }