import json
from datetime import datetime


class VisualizationLayerError(Exception):
    """Raised when visualization generation fails"""
    pass


# -----------------------------------------------------------------
# VISUALIZATION LAYER
# -----------------------------------------------------------------

class VisualizationLayer:

    def __init__(self, audit_dashboard, drift_dashboard):
        self.audit_dashboard = audit_dashboard
        self.drift_dashboard = drift_dashboard

    # -----------------------------------------------------------------
    # CORE STATUS WIDGET
    # -----------------------------------------------------------------

    def build_status_widget(self):

        dashboard = self.audit_dashboard.export_dashboard()

        return {
            "type": "status_card",
            "status": dashboard["system_health"]["status"],
            "audit_valid": dashboard["system_health"]["audit_valid"],
            "drift_events": dashboard["system_health"]["drift_events"],
            "last_updated": dashboard["generated_at"]
        }

    # -----------------------------------------------------------------
    # DRIFT TIMELINE CHART
    # -----------------------------------------------------------------

    def build_drift_timeline_chart(self):

        timeline = self.drift_dashboard.build_timeline()

        return {
            "type": "line_chart",
            "title": "Drift Over Time",
            "x_axis": [p["time"] for p in timeline],
            "y_axis": [1 if p["drift"] else 0 for p in timeline],
            "labels": {
                "x": "Time",
                "y": "Drift (1=True, 0=False)"
            }
        }

    # -----------------------------------------------------------------
    # STABILITY METRIC CHART
    # -----------------------------------------------------------------

    def build_stability_chart(self):

        summary = self.drift_dashboard.compute_summary()

        return {
            "type": "bar_chart",
            "title": "System Stability",
            "labels": ["Stable", "Drift"],
            "values": [
                summary["total_executions"] - summary["drift_events"],
                summary["drift_events"]
            ]
        }

    # -----------------------------------------------------------------
    # HOTSPOT HEATMAP
    # -----------------------------------------------------------------

    def build_hotspot_heatmap(self):

        hotspots = self.drift_dashboard.detect_hotspots()

        return {
            "type": "heatmap",
            "title": "Drift Hotspots",
            "data": hotspots
        }

    # -----------------------------------------------------------------
    # RECENT ACTIVITY TABLE
    # -----------------------------------------------------------------

    def build_recent_activity_table(self):

        dashboard = self.audit_dashboard.export_dashboard()

        return {
            "type": "table",
            "title": "Recent Activity",
            "columns": ["entry_hash", "timestamp", "transcript_hash"],
            "rows": dashboard["recent_activity"]
        }

    # -----------------------------------------------------------------
    # AUDIT INTEGRITY PANEL
    # -----------------------------------------------------------------

    def build_audit_panel(self):

        dashboard = self.audit_dashboard.export_dashboard()

        audit = dashboard["audit_status"]

        return {
            "type": "audit_panel",
            "valid": audit["valid"],
            "chain_hash": audit["chain_hash"],
            "issues": audit["issues"]
        }

    # -----------------------------------------------------------------
    # FULL UI DASHBOARD
    # -----------------------------------------------------------------

    def build_full_dashboard(self):

        return {
            "dashboard_type": "AFRITECH_VISUAL_DASHBOARD",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "widgets": [
                self.build_status_widget(),
                self.build_drift_timeline_chart(),
                self.build_stability_chart(),
                self.build_hotspot_heatmap(),
                self.build_recent_activity_table(),
                self.build_audit_panel()
            ]
        }

    # -----------------------------------------------------------------
    # EXPORT AS JSON STRING
    # -----------------------------------------------------------------

    def export_json(self):

        dashboard = self.build_full_dashboard()

        return json.dumps(
            dashboard,
            sort_keys=True,
            indent=2
        )