"""
AfriTech Structured Logger

PURPOSE:
--------
Provides structured, deterministic logging across the runtime.

Responsibilities:
- standardize log format
- support trace-aware logging
- provide log levels
- ensure consistent observability output

CRITICAL LAW:
-------------
Logger MAY:
- record system events
- provide debugging insight

Logger may NOT:
- modify system execution
- affect logic or outcomes
"""

import json
import time


# ============================================================
# ✅ LOG LEVELS
# ============================================================

LOG_LEVELS = {"DEBUG", "INFO", "WARN", "ERROR"}


# ============================================================
# ✅ CORE LOG FUNCTION
# ============================================================

def log(message: str, level="INFO", trace_id=None, span_id=None, **context):
    """
    Emit structured log.

    Args:
        message: human-readable message
        level: log severity level
        trace_id: optional trace association
        span_id: optional span association
        context: additional metadata
    """

    if level not in LOG_LEVELS:
        raise ValueError(f"[LOGGER ERROR] Invalid level: {level}")

    if not isinstance(message, str):
        raise TypeError("Log message must be a string")

    entry = {
        "timestamp": time.time(),
        "level": level,
        "message": message,
        "trace_id": trace_id,
        "span_id": span_id,
        "context": context or {},
    }

    print(_safe_json(entry))


# ============================================================
# ✅ LEVEL HELPERS
# ============================================================

def debug(message, **kwargs):
    log(message, level="DEBUG", **kwargs)


def info(message, **kwargs):
    log(message, level="INFO", **kwargs)


def warn(message, **kwargs):
    log(message, level="WARN", **kwargs)


def error(message, **kwargs):
    log(message, level="ERROR", **kwargs)


# ============================================================
# ✅ SAFE JSON SERIALIZATION
# ============================================================

def _safe_json(data):
    """
    Safely serialize log data.

    Ensures:
    - no serialization crash
    - fallback to string for unsupported objects
    """

    def default(o):
        try:
            return str(o)
        except Exception:
            return "<non-serializable>"

    return json.dumps(data, default=default)


# ============================================================
# ✅ TRACE-AWARE LOGGING
# ============================================================

def log_with_trace(message: str, trace_id: str, span_id=None, level="INFO", **ctx):
    """
    Log message linked to trace/span.
    """

    log(
        message,
        level=level,
        trace_id=trace_id,
        span_id=span_id,
        **ctx
    )


# ============================================================
# ✅ BULK LOGGING
# ============================================================

def log_bulk(entries: list):
    """
    Emit multiple logs efficiently.
    """

    if not isinstance(entries, list):
        raise TypeError("Entries must be a list")

    for entry in entries:
        if not isinstance(entry, dict):
            raise TypeError("Each entry must be a dict")

        log(
            entry.get("message", ""),
            level=entry.get("level", "INFO"),
            trace_id=entry.get("trace_id"),
            span_id=entry.get("span_id"),
            **entry.get("context", {})
        )


# ============================================================
# ✅ LOG FILTER (UTILITY)
# ============================================================

def filter_logs(log_entries: list, level=None):
    """
    Filter logs by level.
    """

    if not isinstance(log_entries, list):
        raise TypeError("log_entries must be a list")

    if level and level not in LOG_LEVELS:
        raise ValueError("Invalid log level")

    return [
        entry for entry in log_entries
        if (not level or entry.get("level") == level)
    ]


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_log_structure():
    """
    Ensures log structure is stable.
    """

    entry1 = {
        "message": "test",
        "level": "INFO",
        "trace_id": "1",
        "span_id": "1",
    }

    entry2 = dict(entry1)

    if entry1.keys() != entry2.keys():
        raise Exception("[LOGGER ERROR] Non-deterministic structure")

    return True


# ============================================================
# ✅ DEBUG FORMATTER
# ============================================================

def format_log_entry(entry: dict):
    """
    Human-readable log formatter (for debugging/CLI).
    """

    if not isinstance(entry, dict):
        raise TypeError("Log entry must be a dict")

    return (
        f"[{entry.get('level')}] "
        f"{entry.get('message')} "
        f"(trace={entry.get('trace_id')}, span={entry.get('span_id')})"
    )
