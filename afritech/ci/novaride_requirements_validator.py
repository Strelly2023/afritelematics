"""Validate the canonical NovaRide enterprise requirements catalogue."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOGUE = ROOT / "docs/novaride/requirements/NOVARIDE_REQUIREMENTS.yaml"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_FIELDS = {
    "id", "title", "description", "objective", "phase", "domains", "priority",
    "owner", "status", "risk", "acceptance_criteria", "architecture_links",
    "implementation_links", "test_links", "security_links", "evidence_links",
    "release_gates", "approval_state", "introduced_commit", "validated_commit", "gap",
}
ALLOWED_STATUS = {"implemented", "partial", "planned", "deferred", "external_blocked"}
REQUIRED_DOMAINS = {
    "rider_onboarding", "driver_onboarding", "fleet_onboarding", "corporate_onboarding",
    "identity_verification", "vehicle_verification", "licensing", "insurance",
    "background_checks", "authentication", "passkeys", "mfa", "session_management",
    "rbac", "abac", "tenant_isolation", "ride_quoting", "immediate_rides",
    "scheduled_rides", "multi_stop_rides", "recurring_rides", "accessibility_rides",
    "airport_rides", "event_rides", "corporate_rides", "fleet_rides", "dispatch",
    "reassignment", "driver_queues", "geofencing", "surge_pricing", "surge_suppression",
    "emergency_overrides", "driver_wait_time_compensation", "rider_no_show",
    "driver_no_show", "trip_cancellation", "cancellation_fees", "trip_completion", "tipping",
    "payment_authorisation", "payment_capture", "payment_settlement", "cash_handling",
    "refunds", "partial_refunds", "disputes", "chargebacks", "reconciliation",
    "driver_earnings", "payouts", "tax_documents", "receipts", "safety_incidents", "sos",
    "misconduct_reports", "evidence_collection", "case_management", "suspensions", "appeals",
    "fraud_investigations", "fleet_management", "vehicle_inspections", "maintenance",
    "telematics", "corporate_policy", "partner_operations", "government_reporting",
    "analytics", "ai_ml_governance", "performance", "reliability", "availability",
    "scalability", "accessibility", "privacy", "security", "audit", "retention",
    "localisation", "multi_currency", "multi_region", "disaster_recovery", "release_governance",
}


@dataclass(frozen=True)
class ValidationReport:
    catalogue: str
    requirement_count: int
    domain_count: int
    phases: list[int]
    errors: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_catalogue(path: Path = DEFAULT_CATALOGUE) -> ValidationReport:
    errors: list[str] = []
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return ValidationReport(str(path), 0, 0, [], ["catalogue must be a mapping"])
    requirements = payload.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        return ValidationReport(str(path), 0, 0, [], ["requirements must be a non-empty list"])
    ids: set[str] = set()
    domains: set[str] = set()
    phases: set[int] = set()
    for index, item in enumerate(requirements):
        label = f"requirements[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be a mapping")
            continue
        missing = sorted(REQUIRED_FIELDS - set(item))
        if missing:
            errors.append(f"{label} missing fields: {', '.join(missing)}")
        req_id = item.get("id")
        if not isinstance(req_id, str) or not req_id.startswith("NR-"):
            errors.append(f"{label} has invalid id")
        elif req_id in ids:
            errors.append(f"duplicate requirement id: {req_id}")
        else:
            ids.add(req_id)
        phase = item.get("phase")
        if not isinstance(phase, int) or not 1 <= phase <= 11:
            errors.append(f"{req_id or label} has invalid phase")
        else:
            phases.add(phase)
        req_domains = item.get("domains")
        if not isinstance(req_domains, list) or not req_domains or not all(isinstance(v, str) for v in req_domains):
            errors.append(f"{req_id or label} domains must be a non-empty string list")
        else:
            domains.update(req_domains)
        status = item.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{req_id or label} has invalid status: {status}")
        for field in ("owner", "approval_state", "gap"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{req_id or label} requires {field}")
        criteria = item.get("acceptance_criteria")
        if not isinstance(criteria, list) or not criteria:
            errors.append(f"{req_id or label} requires acceptance criteria")
        for field in ("architecture_links", "implementation_links", "test_links", "security_links", "evidence_links"):
            links = item.get(field)
            if not isinstance(links, list):
                errors.append(f"{req_id or label} {field} must be a list")
                continue
            for link in links:
                if not isinstance(link, str) or not link.strip():
                    errors.append(f"{req_id or label} has invalid {field} entry")
                elif not (ROOT / link).exists():
                    errors.append(f"{req_id or label} broken {field}: {link}")
        if status == "implemented":
            for field in ("implementation_links", "test_links", "security_links", "evidence_links"):
                if not item.get(field):
                    errors.append(f"{req_id or label} implemented status requires {field}")
        for field in ("introduced_commit", "validated_commit"):
            value = item.get(field)
            if value is not None and (not isinstance(value, str) or not SHA_RE.fullmatch(value)):
                errors.append(f"{req_id or label} has invalid {field}")
    missing_domains = sorted(REQUIRED_DOMAINS - domains)
    if missing_domains:
        errors.append("catalogue missing domains: " + ", ".join(missing_domains))
    missing_phases = sorted(set(range(1, 12)) - phases)
    if missing_phases:
        errors.append("catalogue missing phases: " + ", ".join(str(value) for value in missing_phases))
    try:
        catalogue_name = str(path.relative_to(ROOT))
    except ValueError:
        catalogue_name = str(path)
    return ValidationReport(catalogue_name, len(requirements), len(domains), sorted(phases), errors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = validate_catalogue(args.catalogue)
    if args.json:
        print(json.dumps({**asdict(report), "valid": report.valid}, indent=2, sort_keys=True))
    elif report.valid:
        print(f"NOVARIDE_REQUIREMENTS: PASS requirements={report.requirement_count} domains={report.domain_count} phases={report.phases}")
    else:
        print("NOVARIDE_REQUIREMENTS: FAIL")
        for error in report.errors:
            print(f"- {error}")
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
