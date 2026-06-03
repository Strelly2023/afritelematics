from .services import classify_deployment_readiness, evaluate_production_readiness


def build_readiness_certificate_payload(certificate, pilot):
    readiness = certificate.validation_summary or evaluate_production_readiness(pilot)

    return {
        "authority": "production_readiness_certificate",
        "certificate_id": str(certificate.certificate_id),
        "pilot_id": certificate.pilot_id,
        "issued_at": certificate.issued_at.isoformat(),
        "readiness_score": certificate.readiness_score,
        "certified": certificate.certified,
        "replay_verified": certificate.replay_verified,
        "deployment_classification": classify_deployment_readiness(pilot, readiness),
        "checks": readiness.get("checks", []),
    }
