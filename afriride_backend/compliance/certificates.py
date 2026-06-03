from regulatory.models import RegulatoryReport


def build_regulatory_certificate(report_id):
    report = RegulatoryReport.objects.get(id=report_id)
    if not report.replay_verified:
        raise ValueError("Cannot certify regulatory report without replay verification")

    return {
        "authority": "regulatory_report_certificate",
        "report_id": report.id,
        "country": report.country,
        "report_type": report.report_type,
        "period_start": str(report.period_start),
        "period_end": str(report.period_end),
        "report_hash": report.report_hash,
        "replay_verified": True,
        "certification_status": "REPORT_CERTIFIED_FOR_EXPORT",
    }
