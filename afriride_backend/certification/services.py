from evidence.models import EventLog

from .models import ProductionReadinessCertificate
from .validators import (
    validate_compliance,
    validate_financial_integrity,
    validate_fraud_integrity,
    validate_payment_integrity,
    validate_replay_integrity,
    validate_route_integrity,
    validate_uptime,
)


def evaluate_production_readiness(pilot, availability_percent=None):
    checks = [
        validate_replay_integrity(pilot),
        validate_payment_integrity(pilot),
        validate_route_integrity(pilot),
        validate_fraud_integrity(pilot),
        validate_uptime(pilot, availability_percent=availability_percent),
        validate_financial_integrity(pilot),
        validate_compliance(pilot),
    ]

    passed_count = sum(1 for check in checks if check["passed"])
    score = round((passed_count / len(checks)) * 100, 2)
    certified = passed_count == len(checks)

    return {
        "pilot_id": pilot.id,
        "certified": certified,
        "score": score,
        "checks": checks,
    }


def classify_deployment_readiness(pilot, readiness_result):
    if pilot.status in {"pilot_ready", "pilot_failed"}:
        return "not_ready"
    if (
        pilot.status in {"pilot_executed", "pilot_verified", "pilot_certified"}
        and not readiness_result["certified"]
    ):
        return "pilot_ready"
    if readiness_result["certified"]:
        return "production_ready"
    return "not_ready"


def create_production_readiness_certificate(pilot, availability_percent=None):
    readiness = evaluate_production_readiness(
        pilot=pilot,
        availability_percent=availability_percent,
    )
    certificate = ProductionReadinessCertificate.objects.create(
        pilot_id=pilot.id,
        readiness_score=readiness["score"],
        certified=readiness["certified"],
        replay_verified=any(
            check["name"] == "replay_integrity" and check["passed"]
            for check in readiness["checks"]
        ),
        validation_summary=readiness,
    )

    EventLog.objects.create(
        event_type="production_readiness_evaluated",
        metadata={
            "pilot_id": pilot.id,
            "certificate_id": str(certificate.certificate_id),
            "readiness_score": certificate.readiness_score,
            "certified": certificate.certified,
            "classification": classify_deployment_readiness(pilot, readiness),
        },
    )

    return certificate
