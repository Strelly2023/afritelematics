"""Activation certificate generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import hashlib
import json


def _sha(value: dict[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True, slots=True)
class ActivationCertificate:
    certificate_type: str
    product_code: str
    product_version: str
    environment: str
    region: str
    status: str
    image_digest: str
    module_checksum: str
    configuration_checksum: str
    infrastructure_checksum: str
    route_plan_checksum: str
    migration_checksum: str
    verification_status: str
    restart_recovery_status: str
    rollback_status: str
    evidence_root_hash: str
    approved_by: str
    activated_at: str


def build_activation_certificate(*, product_code: str, product_version: str, environment: str, region: str, image_digest: str, module_checksum: str, configuration_checksum: str, infrastructure_checksum: str, route_plan_checksum: str, migration_checksum: str, verification_status: str, restart_recovery_status: str, rollback_status: str, approved_by: str, evidence_payload: dict[str, Any]) -> ActivationCertificate:
    return ActivationCertificate(
        certificate_type="NOVATECH_OPERATIONAL_RUNTIME_ACTIVATION",
        product_code=product_code,
        product_version=product_version,
        environment=environment,
        region=region,
        status="ACTIVE",
        image_digest=image_digest,
        module_checksum=module_checksum,
        configuration_checksum=configuration_checksum,
        infrastructure_checksum=infrastructure_checksum,
        route_plan_checksum=route_plan_checksum,
        migration_checksum=migration_checksum,
        verification_status=verification_status,
        restart_recovery_status=restart_recovery_status,
        rollback_status=rollback_status,
        evidence_root_hash=_sha(evidence_payload),
        approved_by=approved_by,
        activated_at=datetime.now(timezone.utc).isoformat(),
    )

