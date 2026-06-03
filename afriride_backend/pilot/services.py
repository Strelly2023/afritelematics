from evidence.models import EventLog
from payments.models import Payment
from trust.models import TrustProfile

from .evidence import collect_ride_evidence
from .models import PilotCertificate, PilotEvidence, PilotMetrics
from .safety import safety_status


MIN_COMPLETED_RIDES = 100
MIN_REPLAY_VERIFICATION_RATE = 95
MIN_PAYMENT_SUCCESS_RATE = 95
def calculate_payment_success_rate(rides):
    ride_ids = [ride.id for ride in rides]
    if not ride_ids:
        return 0

    payments = Payment.objects.filter(ride_id__in=ride_ids)
    total = payments.count()
    if total == 0:
        return 0

    captured = payments.filter(status="captured").count()
    return round((captured / total) * 100, 2)


def calculate_fraud_flags(rides):
    driver_ids = [ride.driver_id for ride in rides if getattr(ride, "driver_id", None)]
    if not driver_ids:
        return 0

    return sum(
        profile.fraud_flags
        for profile in TrustProfile.objects.filter(user_id__in=driver_ids)
    )


def refresh_pilot_metrics(pilot, rides):
    for ride in rides:
        collect_ride_evidence(pilot=pilot, ride=ride)

    evidence = PilotEvidence.objects.filter(pilot=pilot)
    total = evidence.count()
    replay_verified = evidence.filter(replay_verified=True).count()
    completed = replay_verified
    payment_success_rate = calculate_payment_success_rate(rides)
    fraud_flags = calculate_fraud_flags(rides)

    metrics, _ = PilotMetrics.objects.update_or_create(
        pilot=pilot,
        defaults={
            "total_rides": total,
            "completed_rides": completed,
            "replay_verified_rides": replay_verified,
            "fraud_flags": fraud_flags,
            "payment_success_rate": payment_success_rate,
        },
    )

    EventLog.objects.create(
        event_type="pilot_metrics_refreshed",
        metadata={
            "pilot_id": pilot.id,
            "total_rides": total,
            "replay_verified_rides": replay_verified,
            "payment_success_rate": payment_success_rate,
            "fraud_flags": fraud_flags,
        },
    )

    return metrics


def pilot_success_gates(metrics):
    replay_rate = (
        (metrics.replay_verified_rides / metrics.completed_rides) * 100
        if metrics.completed_rides
        else 0
    )
    safety = safety_status(metrics.fraud_flags)

    gates = {
        "completed_100_rides": metrics.completed_rides >= MIN_COMPLETED_RIDES,
        "replay_verification_95_percent": replay_rate >= MIN_REPLAY_VERIFICATION_RATE,
        "payment_success_95_percent": metrics.payment_success_rate >= MIN_PAYMENT_SUCCESS_RATE,
        "no_critical_fraud_event": safety["status"] == "clear",
        "driver_satisfaction_target": (
            metrics.driver_satisfaction >= metrics.driver_satisfaction_target
        ),
        "rider_satisfaction_target": (
            metrics.rider_satisfaction >= metrics.rider_satisfaction_target
        ),
    }

    return {
        "gates": gates,
        "passed": all(gates.values()),
        "replay_verification_rate": round(replay_rate, 2),
        "safety": safety,
    }


def issue_pilot_certificate(pilot):
    metrics = pilot.metrics
    gate_result = pilot_success_gates(metrics)
    if not gate_result["passed"]:
        raise ValueError("Pilot success gates not satisfied")

    certificate, _ = PilotCertificate.objects.update_or_create(
        pilot=pilot,
        defaults={
            "ride_count": metrics.completed_rides,
            "replay_verification_rate": gate_result["replay_verification_rate"],
            "payment_success_rate": metrics.payment_success_rate,
            "fraud_flags": metrics.fraud_flags,
        },
    )
    pilot.status = "pilot_certified"
    pilot.save(update_fields=["status"])

    EventLog.objects.create(
        event_type="pilot_certificate_issued",
        metadata={
            "pilot_id": pilot.id,
            "certificate_id": certificate.id,
            "ride_count": certificate.ride_count,
            "replay_verification_rate": certificate.replay_verification_rate,
        },
    )

    return certificate
