from earnings.models import DriverEarning
from gps.models import LocationEvidence
from payments.models import Payment
from pilot.models import PilotEvidence
from regulatory.models import RegulatoryReport
from trust.models import TrustProfile


def readiness_check(name, passed, details=None):
    return {
        "name": name,
        "passed": bool(passed),
        "details": details or {},
    }


def _pilot_ride_ids(pilot):
    return list(
        PilotEvidence.objects.filter(pilot=pilot).values_list("ride_id", flat=True)
    )


def validate_replay_integrity(pilot):
    evidence = PilotEvidence.objects.filter(pilot=pilot)
    total = evidence.count()
    verified = evidence.filter(replay_verified=True).count()
    rate = round((verified / total) * 100, 2) if total else 0

    return readiness_check(
        "replay_integrity",
        total > 0 and rate == 100,
        {
            "total_evidence_records": total,
            "verified_records": verified,
            "replay_reconstruction_rate": rate,
            "required_rate": 100,
        },
    )


def validate_payment_integrity(pilot):
    ride_ids = _pilot_ride_ids(pilot)
    payments = Payment.objects.filter(ride_id__in=ride_ids)
    total = payments.count()
    failed = payments.exclude(status="captured").count()

    return readiness_check(
        "payment_integrity",
        bool(ride_ids) and total == len(ride_ids) and failed == 0,
        {
            "ride_count": len(ride_ids),
            "payment_count": total,
            "non_captured_payments": failed,
        },
    )


def validate_route_integrity(pilot):
    ride_ids = _pilot_ride_ids(pilot)
    missing = [
        ride_id
        for ride_id in ride_ids
        if not LocationEvidence.objects.filter(ride_id=ride_id).exists()
    ]

    return readiness_check(
        "route_integrity",
        bool(ride_ids) and not missing,
        {
            "ride_count": len(ride_ids),
            "missing_gps_evidence_ride_ids": missing,
        },
    )


def validate_fraud_integrity(pilot):
    ride_ids = _pilot_ride_ids(pilot)
    driver_ids = (
        PilotEvidence.objects.filter(pilot=pilot)
        .exclude(ride__driver_id__isnull=True)
        .values_list("ride__driver_id", flat=True)
    )
    fraud_flags = sum(
        profile.fraud_flags
        for profile in TrustProfile.objects.filter(user_id__in=list(driver_ids))
    )

    return readiness_check(
        "fraud_integrity",
        fraud_flags == 0,
        {
            "ride_count": len(ride_ids),
            "fraud_flags": fraud_flags,
            "required_unresolved_critical_fraud": 0,
        },
    )


def validate_uptime(pilot, availability_percent=None):
    availability = (
        availability_percent
        if availability_percent is not None
        else getattr(getattr(pilot, "metrics", None), "service_availability", 0)
    )

    return readiness_check(
        "operational_stability",
        availability >= 99,
        {
            "availability_percent": availability,
            "required_percent": 99,
        },
    )


def validate_financial_integrity(pilot):
    ride_ids = _pilot_ride_ids(pilot)
    payments = Payment.objects.filter(ride_id__in=ride_ids, status="captured")
    earnings = DriverEarning.objects.filter(ride_id__in=ride_ids)
    payment_ride_ids = set(payments.values_list("ride_id", flat=True))
    earning_ride_ids = set(earnings.values_list("ride_id", flat=True))
    mismatched = sorted(payment_ride_ids.symmetric_difference(earning_ride_ids))

    return readiness_check(
        "financial_integrity",
        bool(ride_ids) and not mismatched and payments.count() == len(ride_ids),
        {
            "ride_count": len(ride_ids),
            "captured_payment_count": payments.count(),
            "earning_count": earnings.count(),
            "mismatched_ride_ids": mismatched,
        },
    )


def validate_compliance(pilot):
    reports = RegulatoryReport.objects.filter(
        created_at__date__gte=pilot.start_date,
        created_at__date__lte=pilot.end_date,
        replay_verified=True,
    )

    return readiness_check(
        "compliance_integrity",
        reports.exists(),
        {
            "verified_report_count": reports.count(),
            "period_start": str(pilot.start_date),
            "period_end": str(pilot.end_date),
        },
    )
