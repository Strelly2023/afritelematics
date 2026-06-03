"""
AfriTech Observability Exporters

PURPOSE:
--------
Provides mechanisms to export observability data externally.

Responsibilities:
- export traces, metrics, logs
- support multiple output targets
- ensure non-intrusive data export
- enable integration with dashboards and monitoring systems

CRITICAL LAW:
-------------
Exporters MAY:
- output observability data

Exporters may NOT:
- modify runtime behavior
- alter execution data
"""

import json
import time
import os


# ============================================================
# ✅ EXPORT TO CONSOLE
# ============================================================

def export_to_console(snapshot: dict):
    """
    Print observability snapshot to console.
    """

    if not isinstance(snapshot, dict):
        raise TypeError("Snapshot must be a dictionary")

    print(json.dumps(snapshot, indent=2))


# ============================================================
# ✅ EXPORT TO FILE
# ============================================================

def export_to_file(snapshot: dict, path="observability.json"):
    """
    Save snapshot to a file.
    """

    if not isinstance(snapshot, dict):
        raise TypeError("Snapshot must be a dictionary")

    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)


# ============================================================
# ✅ APPEND TO FILE (LOGGING MODE)
# ============================================================

def append_to_file(snapshot: dict, path="observability.log"):
    """
    Append snapshot as a single-line JSON entry.
    Useful for continuous logging.
    """

    if not isinstance(snapshot, dict):
        raise TypeError("Snapshot must be a dictionary")

    with open(path, "a") as f:
        f.write(json.dumps(snapshot) + "\n")


# ============================================================
# ✅ EXPORT TRACES ONLY
# ============================================================

def export_traces(traces: dict, path="traces.json"):
    """
    Export only trace data.
    """

    if not isinstance(traces, dict):
        raise TypeError("Traces must be a dictionary")

    with open(path, "w") as f:
        json.dump(traces, f, indent=2)


# ============================================================
# ✅ EXPORT METRICS ONLY
# ============================================================

def export_metrics(metrics: dict, path="metrics.json"):
    """
    Export only metrics.
    """

    if not isinstance(metrics, dict):
        raise TypeError("Metrics must be a dictionary")

    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)


# ============================================================
# ✅ TIMESTAMPED EXPORT
# ============================================================

def export_with_timestamp(snapshot: dict, directory="exports"):
    """
    Save snapshot with timestamp-based filename.
    """

    if not isinstance(snapshot, dict):
        raise TypeError("Snapshot must be a dictionary")

    os.makedirs(directory, exist_ok=True)

    filename = f"{int(time.time())}.json"
    path = os.path.join(directory, filename)

    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)

    return path


# ============================================================
# ✅ EXPORT SUMMARY
# ============================================================

def export_summary(snapshot: dict, path="summary.json"):
    """
    Export simplified summary:
    - trace count
    - metrics keys
    """

    if not isinstance(snapshot, dict):
        raise TypeError("Snapshot must be a dictionary")

    summary = {
        "trace_count": len(snapshot.get("traces", {})),
        "metric_keys": list(snapshot.get("metrics", {}).keys()),
        "active_traces": len(snapshot.get("active_traces", {})),
    }

    with open(path, "w") as f:
        json.dump(summary, f, indent=2)

    return summary


# ============================================================
# ✅ SAFE EXPORT (NO FAILURE)
# ============================================================

def safe_export(func, *args, **kwargs):
    """
    Wrap exporter calls to prevent crashes.
    """

    try:
        return func(*args, **kwargs)

    except Exception as e:
        print(f"[EXPORT ERROR] {str(e)}")
        return None


# ============================================================
# ✅ BULK EXPORT
# ============================================================

def export_all(snapshot: dict, base_path="observability"):
    """
    Export full observability snapshot into multiple files.

    Creates:
    - traces.json
    - metrics.json
    - full_snapshot.json
    """

    if not isinstance(snapshot, dict):
        raise TypeError("Snapshot must be a dictionary")

    os.makedirs(base_path, exist_ok=True)

    full_path = os.path.join(base_path, "full_snapshot.json")
    traces_path = os.path.join(base_path, "traces.json")
    metrics_path = os.path.join(base_path, "metrics.json")

    export_to_file(snapshot, full_path)
    export_traces(snapshot.get("traces", {}), traces_path)
    export_metrics(snapshot.get("metrics", {}), metrics_path)

    return {
        "full": full_path,
        "traces": traces_path,
        "metrics": metrics_path,
    }


# ============================================================
# ✅ VALIDATION
# ============================================================

def validate_export(snapshot: dict):
    """
    Ensure snapshot can be exported safely.
    """

    if not isinstance(snapshot, dict):
        raise TypeError("Snapshot must be a dictionary")

    try:
        json.dumps(snapshot)
    except Exception:
        raise Exception("[EXPORT ERROR] Snapshot is not serializable")

    return True


# ============================================================
# ✅ DEBUG EXPORT VIEW
# ============================================================

def debug_export(snapshot: dict):
    """
    Lightweight debug export preview.
    """

    return {
        "traces": len(snapshot.get("traces", {})),
        "metrics": len(snapshot.get("metrics", {})),
        "active_traces": len(snapshot.get("active_traces", {})),
    }