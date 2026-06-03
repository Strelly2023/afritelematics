import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# =====================================================
# ✅ CONFIG
# =====================================================

DEFAULT_RATE_LIMIT = 60     # default requests per window
WINDOW_SECONDS = 60         # time window
MIN_RATE_LIMIT = 10         # lower bound (abusive clients)
MAX_RATE_LIMIT = 500        # upper bound (trusted clients)

ADAPT_STEP = 10             # step for "trusted" growth


# =====================================================
# ✅ STORAGE (replace with Redis in production)
# =====================================================

CLIENT_LIMITS = defaultdict(lambda: DEFAULT_RATE_LIMIT)
CLIENT_REQUESTS = defaultdict(list)   # client -> timestamps


# =====================================================
# ✅ CORE FUNCTIONS
# =====================================================

def get_rate_limit(client_name: str) -> int:
    """
    Get current rate limit for client.
    """
    return CLIENT_LIMITS[client_name]


def record_request(client_name: str):
    """
    Track request timestamps (sliding window).
    """
    now = time.time()

    CLIENT_REQUESTS[client_name].append(now)

    # ✅ Keep only recent requests
    CLIENT_REQUESTS[client_name] = [
        t for t in CLIENT_REQUESTS[client_name]
        if now - t < WINDOW_SECONDS
    ]


def is_rate_limited(client_name: str) -> bool:
    """
    Check if client exceeded adaptive rate limit.
    """
    now = time.time()
    limit = get_rate_limit(client_name)

    # ✅ clean window
    CLIENT_REQUESTS[client_name] = [
        t for t in CLIENT_REQUESTS[client_name]
        if now - t < WINDOW_SECONDS
    ]

    current_requests = len(CLIENT_REQUESTS[client_name])

    if current_requests >= limit:
        logger.warning(
            f"[RATE_LIMIT] client={client_name} "
            f"requests={current_requests}/{limit}"
        )
        adapt_rate_limit(client_name, "abusive")
        return True

    # ✅ record request
    CLIENT_REQUESTS[client_name].append(now)
    return False


# =====================================================
# ✅ ADAPTIVE LOGIC
# =====================================================

def adapt_rate_limit(client_name: str, behavior: str):
    """
    Adjust rate limit dynamically.
    behavior: abusive | trusted | recovering
    """
    current_limit = CLIENT_LIMITS[client_name]

    if behavior == "abusive":
        # 🔻 aggressively reduce
        new_limit = max(MIN_RATE_LIMIT, current_limit // 2)

        logger.warning(
            f"[ADAPT] REDUCE {client_name}: {current_limit} → {new_limit}"
        )

        CLIENT_LIMITS[client_name] = new_limit

    elif behavior == "trusted":
        # 🔺 gradually increase
        new_limit = min(MAX_RATE_LIMIT, current_limit + ADAPT_STEP)

        logger.info(
            f"[ADAPT] INCREASE {client_name}: {current_limit} → {new_limit}"
        )

        CLIENT_LIMITS[client_name] = new_limit

    elif behavior == "recovering":
        # 📉 slow recovery after abuse
        new_limit = min(
            DEFAULT_RATE_LIMIT,
            current_limit + (ADAPT_STEP // 2)
        )

        CLIENT_LIMITS[client_name] = new_limit


# =====================================================
# ✅ BURST DETECTION
# =====================================================

def detect_burst(client_name: str) -> bool:
    """
    Detect sudden short spikes (burst traffic).
    """
    now = time.time()
    window = 5  # seconds

    recent_requests = [
        t for t in CLIENT_REQUESTS[client_name]
        if now - t < window
    ]

    if len(recent_requests) > 20:
        logger.warning(f"[BURST] client={client_name}")
        adapt_rate_limit(client_name, "abusive")
        return True

    return False


# =====================================================
# ✅ RESET / MAINTENANCE
# =====================================================

def reset_client(client_name: str):
    """
    Reset client metrics (manual or automated).
    """
    CLIENT_REQUESTS.pop(client_name, None)
    CLIENT_LIMITS[client_name] = DEFAULT_RATE_LIMIT


def cleanup_inactive_clients(timeout: int = 300):
    """
    Remove inactive clients (avoid memory growth).
    """
    now = time.time()

    for client, timestamps in list(CLIENT_REQUESTS.items()):
        if not timestamps:
            continue

        if now - max(timestamps) > timeout:
            CLIENT_REQUESTS.pop(client, None)
            CLIENT_LIMITS.pop(client, None)


# =====================================================
# ✅ DEBUG / MONITORING
# =====================================================

def get_client_status(client_name: str) -> dict:
    """
    Return current rate and usage stats.
    """
    now = time.time()

    valid_requests = [
        t for t in CLIENT_REQUESTS[client_name]
        if now - t < WINDOW_SECONDS
    ]

    return {
        "client": client_name,
        "current_requests": len(valid_requests),
        "rate_limit": CLIENT_LIMITS[client_name],
        "window_seconds": WINDOW_SECONDS,
    }
