import logging
import time
from collections import defaultdict
from statistics import mean

logger = logging.getLogger(__name__)


# =====================================================
# ✅ CONFIG
# =====================================================

WINDOW_SECONDS = 60
MAX_HISTORY = 200

REQUEST_TIMESTAMPS = defaultdict(list)   # client -> timestamps
LATENCY_TRACKER = defaultdict(list)      # client -> latencies
FAILURE_TRACKER = defaultdict(list)      # client -> timestamps


# =====================================================
# ✅ RECORD METRICS
# =====================================================

def record_request(client_name: str, duration_ms: float):
    """
    Record request metrics with sliding window cleanup.
    """
    now = time.time()

    # ✅ Track request timestamps
    REQUEST_TIMESTAMPS[client_name].append(now)
    REQUEST_TIMESTAMPS[client_name] = [
        t for t in REQUEST_TIMESTAMPS[client_name]
        if now - t < WINDOW_SECONDS
    ]

    # ✅ Track latency
    LATENCY_TRACKER[client_name].append(duration_ms)
    LATENCY_TRACKER[client_name] = LATENCY_TRACKER[client_name][-MAX_HISTORY:]


def record_failure(client_name: str):
    """
    Track failed events for anomaly enrichment.
    """
    now = time.time()

    FAILURE_TRACKER[client_name].append(now)
    FAILURE_TRACKER[client_name] = [
        t for t in FAILURE_TRACKER[client_name]
        if now - t < WINDOW_SECONDS
    ]


# =====================================================
# ✅ ANOMALY DETECTION
# =====================================================

def detect_anomaly(client_name: str) -> dict:
    """
    Enhanced statistical anomaly detection engine.
    """

    now = time.time()

    reqs = len(REQUEST_TIMESTAMPS[client_name])
    failures = len(FAILURE_TRACKER[client_name])
    latencies = LATENCY_TRACKER[client_name]

    result = {
        "anomaly": False,
        "severity": None,
        "reason": None,
        "metrics": {
            "requests": reqs,
            "failures": failures,
            "avg_latency": mean(latencies) if latencies else 0,
            "max_latency": max(latencies) if latencies else 0
        }
    }

    # =====================================================
    # ✅ RULE 1: HIGH TRAFFIC SPIKE
    # =====================================================
    if reqs > 100:
        result.update({
            "anomaly": True,
            "severity": "HIGH",
            "reason": "High request volume spike"
        })

    # =====================================================
    # ✅ RULE 2: BRUTE FORCE BEHAVIOR
    # =====================================================
    if failures > 5:
        result.update({
            "anomaly": True,
            "severity": "CRITICAL",
            "reason": "Repeated failure pattern detected"
        })

    # =====================================================
    # ✅ RULE 3: HIGH AVERAGE LATENCY
    # =====================================================
    if latencies:
        avg_latency = mean(latencies)

        if avg_latency > 200:
            result.update({
                "anomaly": True,
                "severity": "MEDIUM",
                "reason": "High average latency"
            })

    # =====================================================
    # ✅ RULE 4: LATENCY SPIKE
    # =====================================================
    if latencies:
        max_latency = max(latencies)

        if max_latency > 500:
            result.update({
                "anomaly": True,
                "severity": "HIGH",
                "reason": "Latency spike detected"
            })

    return result


# =====================================================
# ✅ ML FEATURE EXTRACTION
# =====================================================

def extract_features(client_name: str) -> list:
    """
    Prepare features for ML model.
    """
    latencies = LATENCY_TRACKER[client_name]

    return [
        len(REQUEST_TIMESTAMPS[client_name]),
        len(FAILURE_TRACKER[client_name]),
        mean(latencies) if latencies else 0,
    ]


# =====================================================
# ✅ AI SCORING ENGINE (RULE-BASED)
# =====================================================

def detect_ai_anomaly(client_name: str) -> dict:
    """
    AI-style anomaly scoring (extendable to ML models).
    """

    features = extract_features(client_name)
    requests, failures, latency = features

    score = 0

    if requests > 100:
        score += 3

    if failures > 5:
        score += 5

    if latency > 200:
        score += 2

    if score >= 7:
        return {
            "anomaly": True,
            "severity": "CRITICAL",
            "score": score,
            "reason": "High-risk behavioral anomaly"
        }

    if score >= 4:
        return {
            "anomaly": True,
            "severity": "HIGH",
            "score": score,
            "reason": "Suspicious behavior pattern"
        }

    return {
        "anomaly": False,
        "score": score
    }