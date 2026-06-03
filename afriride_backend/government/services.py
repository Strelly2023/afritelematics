from django.utils import timezone
from evidence.models import EventLog

from .integrations import submit_to_partner


def submit_regulatory_report(submission, actor=None):
    if not submission.partner.active:
        raise ValueError("Government partner is not active")
    if not submission.report.replay_verified:
        raise ValueError("Cannot submit report without replay verification")

    result = submit_to_partner(submission.partner, submission.report)
    submission.status = "prepared" if not result["transmitted"] else "submitted"
    submission.submitted_at = timezone.now()
    submission.submission_reference = submission.report.report_hash
    submission.save(
        update_fields=["status", "submitted_at", "submission_reference"],
    )

    EventLog.objects.create(
        event_type="government_submission_prepared",
        actor=actor,
        metadata={
            "submission_id": submission.id,
            "partner_id": submission.partner_id,
            "report_id": submission.report_id,
            "report_hash": submission.report.report_hash,
            "transmitted": result["transmitted"],
            "authority": "external_reporting_only",
        },
    )

    return submission
