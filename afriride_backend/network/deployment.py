from django.utils import timezone
from evidence.models import EventLog

from certification.models import ProductionReadinessCertificate


def validate_region_launch(region, certificate):
    if not isinstance(certificate, ProductionReadinessCertificate):
        return {
            "passed": False,
            "reason": "invalid_certificate",
        }

    checks = {
        "production_certificate": certificate.certified,
        "replay_verified": certificate.replay_verified,
        "readiness_score": certificate.readiness_score >= 100,
        "region_inactive": not region.active,
    }

    return {
        "passed": all(checks.values()),
        "checks": checks,
    }


def activate_region(region, certificate, actor=None):
    validation = validate_region_launch(region, certificate)
    if not validation["passed"]:
        raise ValueError("Region launch gates not satisfied")

    region.active = True
    region.launched_at = timezone.now()
    region.save(update_fields=["active", "launched_at"])

    EventLog.objects.create(
        event_type="region_activated",
        actor=actor,
        metadata={
            "region_id": region.id,
            "region_code": region.code,
            "certificate_id": str(certificate.certificate_id),
            "readiness_score": certificate.readiness_score,
            "authority": "regional_deployment_gate",
        },
    )

    return region
