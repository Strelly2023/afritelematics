import hashlib
import json
from datetime import datetime


class AuditDashboardError(Exception):
    """Raised when audit dashboard generation fails"""
    pass


# -----------------------------------------------------------------
# AUDIT DASHBOARD
# -----------------------------------------------------------------

class AuditDashboard:

    def __init__(self, transcript_store, drift_dashboard, audit_chain):
        self.store = transcript_store
        self.drift_dashboard = drift_dashboard
        self.audit_chain = audit_chain

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
    # CORE METRICS
    # -----------------------------------------------------------------

    def compute_core_metrics(self):

        entries = self.store.get_all_entries()

        total_entries = len(entries)

        latest_entry_hash = (
            entries[-1]["entry_hash"] if entries else "GENESIS"
        )

        return {
            "total_entries": total_entries,
            "latest_entry_hash": latest_entry_hash
        }

    # -----------------------------------------------------------------
    # AUDIT STATUS
    # -----------------------------------------------------------------

    def get_audit_status(self):

        report = self.audit_chain.verify_full_chain()

        return {
            "valid": report.valid,
            "total_entries": report.total_entries,
            "chain_hash": report.details.get("final_chain_hash"),
            "issues": report.details.get("issues")
        }

    # -----------------------------------------------------------------
    # DRIFT ANALYTICS
    # -----------------------------------------------------------------

    def get_drift_analytics(self):

        drift_summary = self.drift_dashboard.compute_summary()
        hotspots = self.drift_dashboard.detect_hotspots()

        return {
            "summary": drift_summary,
            "hotspots": hotspots
        }

    # -----------------------------------------------------------------
    # RECENT ACTIVITY
    # -----------------------------------------------------------------

    def get_recent_activity(self, limit=10):

        entries = self.store.get_all_entries()

        recent = entries[-limit:] if entries else []

        return [
            {
                "entry_hash": e["entry_hash"],
                "timestamp": e["stored_at"],
                "transcript_hash": e["transcript_hash"]
            }
            for e in recent
        ]

    # -----------------------------------------------------------------
    # SYSTEM HEALTH STATUS
    # -----------------------------------------------------------------

    def compute_system_health(self):

        audit = self.get_audit_status()
        drift = self.get_drift_analytics()

        if not audit["valid"]:
            status = "CRITICAL"
        elif drift["summary"]["drift_events"] > 0:
            status = "UNSTABLE"
        else:
            status = "HEALTHY"

        return {
            "status": status,
            "audit_valid": audit["valid"],
            "drift_events": drift["summary"]["drift_events"]
        }

    # -----------------------------------------------------------------
    # FULL DASHBOARD EXPORT
    # -----------------------------------------------------------------

    def export_dashboard(self):

        core = self.compute_core_metrics()
        audit = self.get_audit_status()
        drift = self.get_drift_analytics()
        activity = self.get_recent_activity()
        health = self.compute_system_health()

        dashboard = {
            "system_health": health,
            "core_metrics": core,
            "audit_status": audit,
            "drift_analytics": drift,
            "recent_activity": activity,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }

        dashboard_hash = self.hash_data(dashboard)
        dashboard["dashboard_hash"] = dashboard_hash

        return dashboard