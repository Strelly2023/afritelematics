from regulatory.models import RegulatoryReport


def audit_regulatory_report(report_id):
    report = RegulatoryReport.objects.get(id=report_id)
    return {
        "authority": "compliance_audit_projection",
        "report_id": report.id,
        "country": report.country,
        "report_type": report.report_type,
        "replay_verified": report.replay_verified,
        "report_hash": report.report_hash,
        "audit_status": "eligible" if report.replay_verified else "blocked",
    }
