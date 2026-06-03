from .models import PilotEvidence


def daily_operations_report(pilot, date):
    evidence = PilotEvidence.objects.filter(
        pilot=pilot,
        created_at__date=date,
    )
    rides = evidence.count()
    replay_verified = evidence.filter(replay_verified=True).count()
    metrics = pilot.metrics

    return {
        "date": str(date),
        "pilot_id": pilot.id,
        "rides": rides,
        "completed": replay_verified,
        "replay_verified": replay_verified,
        "verification_rate": round((replay_verified / rides) * 100, 2) if rides else 0,
        "fraud_flags": metrics.fraud_flags,
        "payment_success_rate": metrics.payment_success_rate,
    }


def pilot_status_report(pilot):
    from .services import pilot_success_gates

    metrics = pilot.metrics
    gates = pilot_success_gates(metrics)

    return {
        "pilot_id": pilot.id,
        "name": pilot.name,
        "city": pilot.city,
        "status": pilot.status,
        "metrics": {
            "total_rides": metrics.total_rides,
            "completed_rides": metrics.completed_rides,
            "replay_verified_rides": metrics.replay_verified_rides,
            "fraud_flags": metrics.fraud_flags,
            "payment_success_rate": metrics.payment_success_rate,
            "service_availability": metrics.service_availability,
            "driver_utilization": metrics.driver_utilization,
            "driver_satisfaction": metrics.driver_satisfaction,
            "driver_satisfaction_target": metrics.driver_satisfaction_target,
            "rider_satisfaction": metrics.rider_satisfaction,
            "rider_satisfaction_target": metrics.rider_satisfaction_target,
        },
        "success_gates": gates,
    }
