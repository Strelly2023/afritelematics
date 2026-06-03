from evidence.models import EventLog

from .models import RegulatoryReport
from .reports import generate_transport_activity_report


def create_transport_activity_report(country, start_date, end_date, generated_by=None):
    payload, report_hash = generate_transport_activity_report(
        country=country,
        start_date=start_date,
        end_date=end_date,
    )

    report = RegulatoryReport.objects.create(
        country=country,
        report_type="transport_activity",
        period_start=start_date,
        period_end=end_date,
        generated_by=generated_by,
        replay_verified=True,
        report_hash=report_hash,
    )

    EventLog.objects.create(
        event_type="regulatory_report_generated",
        actor=generated_by,
        metadata={
            "report_id": report.id,
            "country": country,
            "report_hash": report_hash,
            "ride_count": payload["ride_count"],
            "authority": "replay_backed_report",
        },
    )

    return report, payload
