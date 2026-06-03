import time
import logging
from collections import defaultdict
from statistics import mean

logger = logging.getLogger(__name__)

# =====================================================
# ✅ CONFIG (base defaults)
# =====================================================

BASE_RATE_LIMIT = 60
WINDOW_SECONDS = 60
BLOCK_DURATION = 300
MAX_FAILURES = 10

# Adaptive bounds
MIN_RATE_LIMIT = 10
MAX_RATE_LIMIT = 500

# =====================================================
# ✅ STORAGE (replace with Redis in production)
# =====================================================

REQUEST_LOG = defaultdict(list)      # ip -> timestamps
FAILED_LOG = defaultdict(list)       # ip -> timestamps
BLOCKED_IPS = {}                     # ip -> unblock_time

CLIENT_LIMITS = defaultdict(lambda: BASE_RATE_LIMIT)
LATENCY_TRACKER = defaultdict(list)


# =====================================================
# ✅ ADAPTIVE RATE LIMIT
# =====================================================

def get_rate_limit(ip: str) -> int:
    return CLIENT_LIMITS[ip]


def adapt_rate_limit(ip: str, behavior: str):
    """
    Adjust rate limit dynamically.
    """
    if behavior == "abusive":
        CLIENT_LIMITS[ip] = max(MIN_RATE_LIMIT, CLIENT_LIMITS[ip] // 2)
    elif behavior == "trusted":
        CLIENT_LIMITS[ip] = min(MAX_RATE_LIMIT, CLIENT_LIMITS[ip] + 10)


# =====================================================
# ✅ RATE LIMITING (ADAPTIVE)
# =====================================================

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    limit = get_rate_limit(ip)

    REQUEST_LOG[ip] = [
        t for t in REQUEST_LOG[ip]
        if now - t < WINDOW_SECONDS
    ]

    if len(REQUEST_LOG[ip]) >= limit:
        adapt_rate_limit(ip, "abusive")
        return True

    REQUEST_LOG[ip].append(now)
    return False


# =====================================================
# ✅ FAILURE TRACKING
# =====================================================

def record_failure(ip: str):
    now = time.time()

    FAILED_LOG[ip].append(now)

    FAILED_LOG[ip] = [
        t for t in FAILED_LOG[ip]
        if now - t < WINDOW_SECONDS
    ]

    adapt_rate_limit(ip, "abusive")


def is_brute_force(ip: str) -> bool:
    return len(FAILED_LOG[ip]) >= MAX_FAILURES


# =====================================================
# ✅ BLOCKING
# =====================================================

def block_ip(ip: str):
    BLOCKED_IPS[ip] = time.time() + BLOCK_DURATION


def is_blocked(ip: str) -> bool:
    if ip not in BLOCKED_IPS:
        return False

    if time.time() > BLOCKED_IPS[ip]:
        del BLOCKED_IPS[ip]
        adapt_rate_limit(ip, "trusted")
        return False

    return True


# =====================================================
# ✅ ANOMALY DETECTION (STATISTICAL)
# =====================================================

def record_latency(ip: str, duration_ms: float):
    LATENCY_TRACKER[ip].append(duration_ms)

    # Keep recent values
    LATENCY_TRACKER[ip] = LATENCY_TRACKER[ip][-100:]


def detect_anomaly(ip: str) -> dict:
    data = LATENCY_TRACKER[ip]

    if len(data) < 5:
        return {"anomaly": False}

    avg_latency = mean(data)

    if avg_latency > 200:
        return {
            "anomaly": True,
            "reason": "High latency anomaly"
        }

    if len(REQUEST_LOG[ip]) > 100:
        return {
            "anomaly": True,
            "reason": "High request volume"
        }

    return {"anomaly": False}


# =====================================================
# ✅ ML-READY HOOK (FEATURE EXTRACTOR)
# =====================================================

def extract_features(ip: str) -> list:
    return [
        len(REQUEST_LOG[ip]),
        len(FAILED_LOG[ip]),
        mean(LATENCY_TRACKER[ip]) if LATENCY_TRACKER[ip] else 0
    ]


# =====================================================
# ✅ AI ANOMALY SCORING
# =====================================================

def detect_ai_anomaly(ip: str) -> dict:
    features = extract_features(ip)

    requests, failures, latency = features

    score = 0

    if requests > 100:
        score += 3

    if failures > 5:
        score += 5

    if latency > 200:
        score += 2

    if score >= 7:
        return {"anomaly": True, "risk": "CRITICAL"}

    if score >= 4:
        return {"anomaly": True, "risk": "HIGH"}

    return {"anomaly": False}


# =====================================================
# ✅ CLEANUP / RESET
# =====================================================

def cleanup_ip(ip: str):
    REQUEST_LOG.pop(ip, None)
    FAILED_LOG.pop(ip, None)
    LATENCY_TRACKER.pop(ip, None)


def reset_all():
    REQUEST_LOG.clear()
    FAILED_LOG.clear()
    LATENCY_TRACKER.clear()
    BLOCKED_IPS.clear()
    CLIENT_LIMITS.clear()


# =====================================================
# ✅ DEBUG STATUS
# =====================================================

def get_ip_status(ip: str) -> dict:
    now = time.time()

    return {
        "ip": ip,
        "blocked": is_blocked(ip),
        "requests": len(REQUEST_LOG[ip]),
        "failures": len(FAILED_LOG[ip]),
        "rate_limit": CLIENT_LIMITS[ip],
        "latency_avg": (
            mean(LATENCY_TRACKER[ip]) if LATENCY_TRACKER[ip] else 0
        ),
        "block_expires_in": (
            int(BLOCKED_IPS[ip] - now)
            if ip in BLOCKED_IPS else 0
        )
    }