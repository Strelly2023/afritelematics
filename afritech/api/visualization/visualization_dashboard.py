import hashlib
import json
from datetime import datetime


class VisualizationDashboardError(Exception):
    """Raised when visualization dashboard generation fails"""
    pass


# -----------------------------------------------------------------
# VISUALIZATION DASHBOARD (UNIFIED AUDIT + DRIFT)
# -----------------------------------------------------------------

class VisualizationDashboard:

    def __init__(self, audit_dashboard, drift_dashboard):
        self.audit_dashboard = audit_dashboard
        self.drift_dashboard = drift_dashboard

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
    # HEALTH OVERVIEW (TOP PANEL)
    # -----------------------------------------------------------------

    def build_health_overview(self):

        audit_data = self.audit_dashboard.export_dashboard()

        return {
            "type": "health_overview",
            "status": audit_data["system_health"]["status"],
            "audit_valid": audit_data["system_health"]["audit_valid"],
            "drift_events": audit_data["system_health"]["drift_events"],
            "total_entries": audit_data["core_metrics"]["total_entries"],
            "last_updated": audit_data["generated_at"]
        }

    # -----------------------------------------------------------------
    # AUDIT INTEGRITY PANEL
    # -----------------------------------------------------------------

    def build_audit_integrity_panel(self):

        audit_data = self.audit_dashboard.export_dashboard()

        audit = audit_data["audit_status"]

        return {
            "type": "audit_integrity",
            "valid": audit["valid"],
            "chain_hash": audit["chain_hash"],
            "issues": audit["issues"]
        }

    # -----------------------------------------------------------------
    # DRIFT TIMELINE (PRIMARY CHART)
    # -----------------------------------------------------------------

    def build_drift_timeline(self):

        timeline = self.drift_dashboard.build_timeline()

        return {
            "type": "timeline_chart",
            "title": "Drift Timeline",
            "series": [
                {
                    "time": p["time"],
                    "value": 1 if p["drift"] else 0
                }
                for p in timeline
            ]
        }

    # -----------------------------------------------------------------
    # STABILITY BREAKDOWN
    # -----------------------------------------------------------------

    def build_stability_breakdown(self):

        summary = self.drift_dashboard.compute_summary()

        stable = summary["total_executions"] - summary["drift_events"]

        return {
            "type": "stability_chart",
            "labels": ["Stable", "Drift"],
            "values": [stable, summary["drift_events"]],
            "stability_ratio": summary["stability_ratio"]
        }

    # -----------------------------------------------------------------
    # DRIFT HOTSPOTS PANEL
    # -----------------------------------------------------------------

    def build_hotspot_panel(self):

        hotspots = self.drift_dashboard.detect_hotspots()

        return {
            "type": "hotspot_panel",
            "hotspots": hotspots,
            "count": len(hotspots)
        }

    # -----------------------------------------------------------------
    # ACTIVITY STREAM
    # -----------------------------------------------------------------

    def build_activity_stream(self):

        audit_data = self.audit_dashboard.export_dashboard()

        return {
            "type": "activity_stream",
            "entries": audit_data["recent_activity"]
        }

    # -----------------------------------------------------------------
    # METRICS PANEL
    # -----------------------------------------------------------------

    def build_metrics_panel(self):

        audit_data = self.audit_dashboard.export_dashboard()
        drift_summary = self.drift_dashboard.compute_summary()

        return {
            "type": "metrics_panel",
            "metrics": {
                "total_executions": drift_summary["total_executions"],
                "drift_events": drift_summary["drift_events"],
                "stability_ratio": drift_summary["stability_ratio"],
                "latest_entry_hash": audit_data["core_metrics"]["latest_entry_hash"]
            }
        }

    # -----------------------------------------------------------------
    # FULL DASHBOARD
    # -----------------------------------------------------------------

    def build_dashboard(self):

        dashboard = {
            "dashboard_type": "AFRITECH_AUDIT_DRIFT_DASHBOARD",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "panels": [
                self.build_health_overview(),
                self.build_audit_integrity_panel(),
                self.build_metrics_panel(),
                self.build_drift_timeline(),
                self.build_stability_breakdown(),
                self.build_hotspot_panel(),
                self.build_activity_stream()
            ]
        }

        dashboard_hash = self.hash_data(dashboard)
        dashboard["dashboard_hash"] = dashboard_hash

        return dashboard

    # -----------------------------------------------------------------
    # EXPORT JSON (UI READY)
    # -----------------------------------------------------------------

    def export_json(self):

        return json.dumps(
            self.build_dashboard(),
            sort_keys=True,
            indent=2
        )