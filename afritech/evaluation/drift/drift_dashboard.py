import hashlib
import json
from datetime import datetime


class DriftDashboardError(Exception):
    """Raised when drift dashboard analysis fails"""
    pass


# -----------------------------------------------------------------
# DRIFT ANALYTICS DASHBOARD
# -----------------------------------------------------------------

class DriftDashboard:

    def __init__(self, transcript_store):
        self.store = transcript_store

    # -----------------------------------------------------------------
    # CANONICAL UTIL
    # -----------------------------------------------------------------

    def canonical_json(self, data):
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        )

    def hash_data(self, data):
        return hashlib.sha256(
            self.canonical_json(data).encode()
        ).hexdigest()

    # -----------------------------------------------------------------
    # LOAD TRANSCRIPTS
    # -----------------------------------------------------------------

    def load_transcripts(self):

        entries = self.store.get_all_entries()

        if not entries:
            return []

        return entries

    # -----------------------------------------------------------------
    # DRIFT SERIES ANALYSIS
    # -----------------------------------------------------------------

    def compute_drift_series(self):

        entries = self.load_transcripts()

        series = []
        previous_hash = None

        for index, entry in enumerate(entries):

            current_hash = entry["transcript_hash"]

            drift = False
            if previous_hash:
                drift = (previous_hash != current_hash)

            series.append({
                "index": index,
                "transcript_hash": current_hash,
                "drift_from_previous": drift,
                "timestamp": entry["stored_at"],
                "entry_hash": entry["entry_hash"]
            })

            previous_hash = current_hash

        return series

    # -----------------------------------------------------------------
    # DRIFT SUMMARY
    # -----------------------------------------------------------------

    def compute_summary(self):

        series = self.compute_drift_series()

        total = len(series)
        drift_events = sum(1 for x in series if x["drift_from_previous"])

        stability_ratio = (
            (total - drift_events) / total if total > 0 else 1.0
        )

        return {
            "total_executions": total,
            "drift_events": drift_events,
            "stability_ratio": stability_ratio
        }

    # -----------------------------------------------------------------
    # DRIFT CLUSTERS
    # -----------------------------------------------------------------

    def detect_drift_clusters(self):

        series = self.compute_drift_series()
        clusters = []

        current_cluster = []

        for point in series:

            if point["drift_from_previous"]:
                current_cluster.append(point)
            else:
                if current_cluster:
                    clusters.append(current_cluster)
                    current_cluster = []

        if current_cluster:
            clusters.append(current_cluster)

        return clusters

    # -----------------------------------------------------------------
    # HOTSPOT DETECTION
    # -----------------------------------------------------------------

    def detect_hotspots(self):

        clusters = self.detect_drift_clusters()

        hotspots = []

        for cluster in clusters:

            if len(cluster) > 1:
                hotspots.append({
                    "size": len(cluster),
                    "start_index": cluster[0]["index"],
                    "end_index": cluster[-1]["index"],
                    "timestamps": [c["timestamp"] for c in cluster]
                })

        return hotspots

    # -----------------------------------------------------------------
    # TIMELINE VIEW
    # -----------------------------------------------------------------

    def build_timeline(self):

        series = self.compute_drift_series()

        return [
            {
                "time": point["timestamp"],
                "drift": point["drift_from_previous"]
            }
            for point in series
        ]

    # -----------------------------------------------------------------
    # FULL DASHBOARD EXPORT
    # -----------------------------------------------------------------

    def export_dashboard(self):

        series = self.compute_drift_series()
        summary = self.compute_summary()
        clusters = self.detect_drift_clusters()
        hotspots = self.detect_hotspots()

        dashboard = {
            "summary": summary,
            "drift_series": series,
            "clusters": clusters,
            "hotspots": hotspots,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }

        dashboard_hash = self.hash_data(dashboard)
        dashboard["dashboard_hash"] = dashboard_hash

        return dashboard