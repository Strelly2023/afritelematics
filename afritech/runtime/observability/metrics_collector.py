"""
AfriTech Metrics Collector

PURPOSE:
--------
Collects and manages runtime metrics for observability and adaptive systems.

Responsibilities:
- record numeric measurements
- aggregate statistics
- provide summaries
- support performance analysis

CRITICAL LAW:
-------------
Metrics Collector MAY:
- collect numerical data
- aggregate statistics

Metrics Collector may NOT:
- modify execution behavior
- introduce side effects
- break determinism
"""

# ============================================================
# ✅ METRICS COLLECTOR CLASS
# ============================================================

class MetricsCollector:
    """
    Collects and aggregates numeric metrics.

    Each metric:
    - identified by name
    - stores multiple values
    """

    def __init__(self):
        # metric_name → list of numeric values
        self.metrics = {}

    # ========================================================
    # ✅ RECORD METRIC
    # ========================================================

    def record(self, name: str, value: float):
        """
        Record a metric value.

        Example:
            record("latency", 120.5)
        """

        if not isinstance(name, str):
            raise TypeError("Metric name must be string")

        if not isinstance(value, (int, float)):
            raise TypeError("Metric value must be numeric")

        self.metrics.setdefault(name, []).append(float(value))

    # ========================================================
    # ✅ GET RAW METRIC VALUES
    # ========================================================

    def get_metric(self, name: str):
        """
        Retrieve raw values for a metric.
        """

        return list(self.metrics.get(name, []))

    # ========================================================
    # ✅ AGGREGATED METRICS
    # ========================================================

    def summarize_metric(self, name: str):
        """
        Compute summary statistics for a metric.

        Returns:
            {
                count,
                avg,
                min,
                max,
                sum
            }
        """

        values = self.metrics.get(name, [])

        if not values:
            return {
                "count": 0,
                "avg": 0,
                "min": None,
                "max": None,
                "sum": 0,
            }

        total = sum(values)

        return {
            "count": len(values),
            "avg": total / len(values),
            "min": min(values),
            "max": max(values),
            "sum": total,
        }

    # ========================================================
    # ✅ FULL SNAPSHOT
    # ========================================================

    def snapshot(self):
        """
        Return aggregated metrics across all keys.
        """

        return {
            name: self.summarize_metric(name)
            for name in self.metrics.keys()
        }

    # ========================================================
    # ✅ RESET METRICS
    # ============================================================

    def clear(self):
        """
        Reset all metrics.
        """

        self.metrics.clear()

    # ========================================================
    # ✅ METRIC EXISTENCE
    # ============================================================

    def has_metric(self, name: str):
        """
        Check if a metric exists.
        """

        return name in self.metrics

    # ========================================================
    # ✅ BULK RECORD
    # ============================================================

    def record_bulk(self, metrics: dict):
        """
        Record multiple metrics at once.

        Example:
            {"latency": 10, "throughput": 5}
        """

        if not isinstance(metrics, dict):
            raise TypeError("Metrics must be a dictionary")

        for name, value in metrics.items():
            self.record(name, value)

    # ========================================================
    # ✅ TOP METRICS (BY VALUE)
    # ============================================================

    def top_metrics(self, key="avg", top_n=5):
        """
        Return top metrics sorted by chosen stat.

        key: avg, max, min, sum
        """

        snapshot = self.snapshot()

        sorted_metrics = sorted(
            snapshot.items(),
            key=lambda x: x[1].get(key, 0),
            reverse=True,
        )

        return sorted_metrics[:top_n]

    # ========================================================
    # ✅ VALIDATION
    # ============================================================

    def validate(self):
        """
        Validate internal structure.
        """

        if not isinstance(self.metrics, dict):
            raise Exception("[METRICS ERROR] Invalid structure")

        for name, values in self.metrics.items():
            if not isinstance(values, list):
                raise Exception(f"[METRICS ERROR] Invalid list for {name}")

            for v in values:
                if not isinstance(v, (int, float)):
                    raise Exception(
                        f"[METRICS ERROR] Non-numeric value in {name}"
                    )

        return True

    # ========================================================
    # ✅ DETERMINISM CHECK
    # ============================================================

    def validate_determinism(self):
        """
        Ensures snapshot is deterministic (same state → same output).
        """

        snap1 = self.snapshot()
        snap2 = self.snapshot()

        if snap1 != snap2:
            raise Exception("[METRICS ERROR] Non-deterministic metrics output")

        return True

    # ========================================================
    # ✅ DEBUG VIEW
    # ============================================================

    def debug(self):
        """
        Human-readable view.
        """

        return {
            name: {
                "count": len(values),
                "latest": values[-1] if values else None
            }
            for name, values in self.metrics.items()
        }