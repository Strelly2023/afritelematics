from .services import evaluate_production_readiness


def executive_readiness_dashboard(pilot, availability_percent=None):
    readiness = evaluate_production_readiness(
        pilot=pilot,
        availability_percent=availability_percent,
    )
    checks = {check["name"]: check for check in readiness["checks"]}
    metrics = pilot.metrics

    return {
        "pilot_id": pilot.id,
        "replay_integrity": checks["replay_integrity"]["details"].get(
            "replay_reconstruction_rate",
            0,
        ),
        "payment_success": metrics.payment_success_rate,
        "fraud_flags": metrics.fraud_flags,
        "driver_utilization": metrics.driver_utilization,
        "availability": checks["operational_stability"]["details"].get(
            "availability_percent",
            0,
        ),
        "readiness_score": readiness["score"],
        "certified": readiness["certified"],
        "checks": readiness["checks"],
    }
