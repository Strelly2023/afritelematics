"""Generate fail-closed NovaRide operational certification evidence.

The values in this file reflect the commands executed on 2026-07-19. Re-run the
underlying checks and update the inputs before using it for a later release.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "artifacts" / "novaride"
STAMP = "2026-07-19T00:05:00Z"
COMMIT = "63ef5e0c94333d5482ede1c19b13db908ad76e7d"


def write_json(relative: str, payload: object) -> None:
    path = BASE / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(relative: str, title: str, body: str) -> None:
    path = BASE / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


executed = {
    "generated_at": STAMP,
    "source_commit": COMMIT,
    "branch": "feature/novacodepro-unified-platform",
    "dirty_tree": True,
}

write_json(
    "operational/DEPENDENCY_INVENTORY.json",
    {
        **executed,
        "python": {
            "version": "3.11.8",
            "environment": "venv",
            "pip_check": "PASS",
            "psycopg": "3.3.4",
            "redis": "8.0.1",
        },
        "node": {"version": "20.19.5", "npm": "10.8.2"},
        "java": "17.0.9",
        "installed": [
            {
                "package_set": "apps/novaride-operations",
                "packages_added": 27,
                "lockfile_created": True,
                "result": "PASS",
            }
        ],
    },
)
write_text(
    "operational/DEPENDENCY_INSTALLATION_REPORT.md",
    "Dependency installation report",
    "The existing repository `venv` passed `pip check` and supplied psycopg 3.3.4. `npm install --prefix apps/novaride-operations` installed the package's declared dependencies and generated its lockfile. No undeclared runtime package was used.",
)
write_text(
    "operational/DEPENDENCY_SECURITY_REPORT.md",
    "Dependency security report",
    "Operations: 0 vulnerabilities. Rider: 30 total (14 high, 15 moderate, 1 low). Driver: 34 total (17 high, 16 moderate, 1 low). No critical npm finding was reported. High findings are unresolved and block broader release.",
)

write_json(
    "operational/FULL_TEST_RESULTS.json",
    {
        **executed,
        "runs": [
            {
                "suite": "novaride_runtime",
                "command": "venv/bin/python3 -m pytest -q tests/novaride_runtime",
                "passed": 49,
                "failed": 0,
                "skipped": 0,
                "blocked": 0,
                "duration_seconds": 18.09,
                "status": "PASS",
            },
            {
                "suite": "all_novaride_named",
                "command": "rg --files tests -g '*.py' | rg novaride | xargs pytest -q",
                "passed": 119,
                "failed": 0,
                "skipped": 0,
                "blocked": 0,
                "duration_seconds": 42.48,
                "status": "PASS",
            },
            {
                "suite": "security_boundaries",
                "command": "pytest NovaRide security/access/payment/incident/release tests",
                "passed": 8,
                "failed": 0,
                "skipped": 0,
                "blocked": 0,
                "duration_seconds": 4.55,
                "status": "PASS",
            },
        ],
    },
)
write_text(
    "operational/TEST_FAILURE_ANALYSIS.md",
    "Test failure analysis",
    "An initial all-NovaRide run found `test_rider_buttons_are_wired` failing because the Action component removed its handler when disabled. The component now uses the native `disabled` property while retaining `onPress={onPress}`. The complete 119-test set passed after the correction. Repository-wide Ruff remains failed independently.",
)
write_json(
    "operational/TYPECHECK_RESULTS.json",
    {
        **executed,
        "status": "PASS",
        "surfaces": {
            "rider_app": "PASS",
            "driver_app": "PASS",
            "apps/novaride-operations": "PASS",
            "novaride_operations_portal": "PASS",
        },
    },
)
write_json(
    "operational/STATIC_ANALYSIS_RESULTS.json",
    {
        **executed,
        "ruff": {
            "command": ".venv-review/bin/python -m ruff check afritech tests",
            "status": "FAIL",
            "finding_count": 10483,
        },
        "compileall": {"status": "PASS"},
        "git_diff_check": {"status": "PASS"},
    },
)
write_json(
    "operational/API_COLLECTION_RESULTS.json",
    {
        **executed,
        "status": "PASS",
        "evidence": "tests/novaride_runtime contracts and replay API tests included in 49 passing runtime tests",
    },
)
write_json(
    "operational/TEST_COVERAGE_REPORT.json",
    {
        **executed,
        "status": "NOT_EXECUTED",
        "reason": "No coverage command was executed in this certification run",
    },
)

blocked_json = {
    "DATABASE_CONSTRAINT_RESULTS.json": "Docker daemon and isolated PostgreSQL 16 instance unavailable",
    "MOBILE_BUILD_MANIFEST.json": "Approved release signing material and Android toolchain environment unavailable",
    "ENVIRONMENT_INVENTORY.json": "Docker CLI present; daemon unavailable; no production-equivalent deployment started",
    "READINESS_RESULTS.json": "No production-equivalent services running",
    "AUTHORIZATION_MATRIX_RESULTS.json": "Automated role tests passed; demo accounts were not provisioned against a live environment",
    "E2E_SCENARIO_RESULTS.json": "No live rider/driver applications or production-equivalent environment",
    "E2E_TRACE_INDEX.json": "No live E2E traces generated",
    "PAYMENT_E2E_RESULTS.json": "No approved payment sandbox credentials/environment",
    "LEDGER_RECONCILIATION_REPORT.json": "No live sandbox ledger run",
    "REFUND_RESULTS.json": "No live sandbox refund run",
    "LOAD_TEST_RESULTS.json": "No running production-equivalent target",
    "PERFORMANCE_BASELINE.json": "No live load execution",
    "RESILIENCE_MATRIX_RESULTS.json": "No running PostgreSQL/Redis/Kafka/application topology",
    "RECOVERY_TIME_RESULTS.json": "No failover execution",
    "ALERT_VERIFICATION_RESULTS.json": "No live metrics/alert stack",
    "AUTHORIZATION_PENETRATION_RESULTS.json": "Internal automated boundary tests passed; live penetration scenarios not executed",
    "MOBILE_SECURITY_RESULTS.json": "Static manifest checks passed in tests; dynamic binary assessment not executed",
    "EXTERNAL_SECURITY_STATUS.json": "No qualified independent assessor engaged",
    "EXTERNAL_FINDINGS_REGISTER.json": "No external assessment findings supplied",
    "PHYSICAL_DEVICE_MATRIX.json": "No physical devices available; adb daemon could not start in sandbox",
    "DISASTER_RECOVERY_RESULTS.json": "No production-equivalent backup or restore executed",
}
for name, reason in blocked_json.items():
    write_json(f"operational/{name}", {**executed, "status": "BLOCKED", "reason": reason})

write_json(
    "operational/INTERNAL_SECURITY_RESULTS.json",
    {
        **executed,
        "status": "PARTIAL",
        "automated_tests": {"passed": 8, "failed": 0},
        "npm": {"operations_high": 0, "rider_high": 14, "driver_high": 17},
        "external_tools": {
            "sast": "NOT_AVAILABLE",
            "secret_scan": "NOT_AVAILABLE",
            "container_scan": "NOT_AVAILABLE",
        },
    },
)

certificates = {
    "DATABASE_MIGRATION_CERTIFICATE.md": "Blocked. A clean PostgreSQL 16 database and representative upgrade fixture were not provisioned.",
    "DATABASE_SCHEMA_SNAPSHOT.sql": "-- BLOCKED: no clean production-equivalent PostgreSQL schema was created in this run.\n",
    "RIDER_BUILD_CERTIFICATE.md": "Blocked. Current source was not release-signed; release credentials were absent.",
    "DRIVER_BUILD_CERTIFICATE.md": "Blocked. Current source was not release-signed; release credentials were absent.",
    "APK_PUBLICATION_CERTIFICATE.md": "Blocked. No fresh signed artifact was produced or published.",
    "DEPLOYMENT_CERTIFICATE.md": "Blocked. Docker daemon was unavailable and no production-equivalent environment was started.",
    "CONFIGURATION_DIFF_REPORT.md": "No live deployment existed to compare with repository configuration.",
    "SECRETS_VALIDATION_REPORT.md": "No signing or provider secret was printed or committed. External secret-provider operation was not tested.",
    "DEMO_ACCOUNT_CERTIFICATE.md": "Blocked. Demo credentials were not persisted or logged, and accounts were not provisioned without an isolated live environment.",
    "TRIP_LIFECYCLE_CERTIFICATE.md": "Automated lifecycle tests passed; live application certification is blocked.",
    "DISPATCH_CERTIFICATE.md": "Automated dispatch flows passed; live multi-driver certification is blocked.",
    "REALTIME_CERTIFICATE.md": "Blocked. No live WebSocket/Redis environment was running.",
    "PAYMENT_SECURITY_CERTIFICATE.md": "Blocked. Automated payment-safety tests passed, but no approved provider sandbox was available.",
    "CAPACITY_REPORT.md": "Blocked. No production-equivalent target was running.",
    "SOAK_TEST_REPORT.md": "Not executed; no long-running production-equivalent target.",
    "FAILOVER_CERTIFICATE.md": "Blocked. PostgreSQL, Redis, Kafka and workers were not running.",
    "DATA_LOSS_ASSESSMENT.md": "Not assessed through live failure injection.",
    "METRICS_CERTIFICATE.md": "Blocked. No live Prometheus scrape was performed.",
    "TRACE_CERTIFICATE.md": "Blocked. No live OpenTelemetry export was performed.",
    "LOGGING_CERTIFICATE.md": "Static redaction controls exist; live log correlation was not certified.",
    "SECURITY_FINDINGS.md": "High npm findings remain in Rider and Driver dependency trees. External penetration testing and dynamic mobile assessment remain blocked.",
    "EXTERNAL_SECURITY_ASSESSMENT_PACKAGE.md": "Scope: NovaRide APIs, Rider/Driver Android packages, operations surfaces, identity/tenant boundaries, payments, realtime and infrastructure. Required: independent assessor, approved environment, redacted test accounts, rules of engagement, findings report and retest.",
    "RIDER_DEVICE_ACCEPTANCE.md": "Blocked. No real Rider Android device was tested.",
    "DRIVER_DEVICE_ACCEPTANCE.md": "Blocked. No real Driver Android device was tested.",
    "BACKUP_RESTORE_CERTIFICATE.md": "Blocked. No production-equivalent database or object store was available for backup and restore.",
}
for name, body in certificates.items():
    if name.endswith(".sql"):
        path = BASE / "operational" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    else:
        write_text(f"operational/{name}", name.removesuffix(".md").replace("_", " ").title(), body)

sbom = BASE / "operational" / "MOBILE_SBOM" / "README.md"
sbom.parent.mkdir(parents=True, exist_ok=True)
sbom.write_text(
    "# Mobile SBOM\n\nBlocked: no fresh signed Rider or Driver build was produced.\n",
    encoding="utf-8",
)

write_text(
    "pilot/CONTROLLED_PILOT_PLAN.md",
    "Controlled Pilot plan",
    "Entry requires fresh signed builds, production-equivalent deployment, live E2E, payment approval, capacity/resilience evidence, physical devices, security closure, named staff, approved participants, consent, geography, hours, rollback and support coverage.",
)
for name, payload in {
    "CONTROLLED_PILOT_PARTICIPANTS.json": {
        "status": "NOT_EXECUTED",
        "participants": [],
        "reason": "No approved real-user registry supplied",
    },
    "CONTROLLED_PILOT_DAILY_RESULTS.json": {"status": "NOT_EXECUTED", "days": []},
    "CONTROLLED_PILOT_INCIDENT_REGISTER.json": {"status": "NOT_EXECUTED", "incidents": []},
    "CONTROLLED_PILOT_DECISION.json": {"decision": "BLOCKED", "real_users": "NOT_EXECUTED"},
}.items():
    write_json(f"pilot/{name}", {**executed, **payload})
write_text(
    "pilot/CONTROLLED_PILOT_EXIT_REPORT.md",
    "Controlled Pilot exit report",
    "Blocked. Synthetic automated tests are not real-user pilot evidence; required entry gates and approvals are incomplete.",
)

write_text(
    "public-pilot/PUBLIC_PILOT_PLAN.md",
    "Public Pilot plan",
    "Blocked until Controlled Pilot approval, legal/insurance/payment/operating approvals, capacity, support, monitoring, fraud and automatic stop controls are recorded.",
)
for name, payload in {
    "PUBLIC_PILOT_METRICS.json": {"status": "NOT_EXECUTED", "metrics": {}},
    "PUBLIC_PILOT_INCIDENT_REGISTER.json": {"status": "NOT_EXECUTED", "incidents": []},
    "PUBLIC_PILOT_DECISION.json": {"decision": "BLOCKED"},
}.items():
    write_json(f"public-pilot/{name}", {**executed, **payload})
write_text(
    "public-pilot/PUBLIC_PILOT_EXIT_REPORT.md",
    "Public Pilot exit report",
    "Blocked. Controlled Pilot is not approved and no public participants or approvals were supplied.",
)

write_text(
    "prr/NOVARIDE_PRR_CHECKLIST.md",
    "NovaRide PRR checklist",
    "Product: partial. Engineering: partial. Architecture: partial. Security, privacy, compliance, safety, payments, operations, SRE, support, infrastructure, continuity and pilot results: blocked pending executed evidence and named approvers.",
)
write_json(
    "prr/NOVARIDE_PRR_EVIDENCE_INDEX.json",
    {**executed, "status": "PARTIAL", "evidence_root": "artifacts/novaride"},
)
write_json(
    "prr/NOVARIDE_PRR_RISK_REGISTER.json",
    {
        **executed,
        "risks": [
            "Unresolved high npm findings",
            "No signed current builds",
            "No production-equivalent deployment",
            "No live pilot",
            "No external assessment",
            "No human approvals",
        ],
    },
)
write_json("prr/NOVARIDE_PRR_APPROVALS.json", {**executed, "status": "BLOCKED", "approvals": []})
write_text(
    "prr/NOVARIDE_PRR_DECISION.md",
    "NovaRide PRR decision",
    "**BLOCKED.** Mandatory operational evidence and human approvals are absent.",
)

gates = {
    "DEPENDENCIES_COMPLETE": "PARTIAL",
    "FULL_BACKEND_SUITE_PASS": "PASS",
    "FULL_MOBILE_SUITE_PASS": "PASS",
    "API_COLLECTIONS_PASS": "PASS",
    "TYPECHECK_PASS": "PASS",
    "STATIC_ANALYSIS_PASS": "FAIL",
    "DATABASE_MIGRATIONS_PASS": "BLOCKED",
    "RIDER_SIGNED_BUILD_PASS": "BLOCKED",
    "DRIVER_SIGNED_BUILD_PASS": "BLOCKED",
    "APK_DOWNLOAD_VERIFIED": "BLOCKED",
    "PRODUCTION_EQUIVALENT_DEPLOYMENT_PASS": "BLOCKED",
    "DEMO_DRIVER_LOGIN_PASS": "BLOCKED",
    "DEMO_RIDER_LOGIN_PASS": "BLOCKED",
    "ROLE_ISOLATION_PASS": "PARTIAL",
    "LIVE_BOOKING_E2E_PASS": "BLOCKED",
    "LIVE_DISPATCH_E2E_PASS": "BLOCKED",
    "LIVE_TRIP_E2E_PASS": "BLOCKED",
    "LIVE_PAYMENT_E2E_PASS": "BLOCKED",
    "PAYMENT_RECONCILIATION_PASS": "BLOCKED",
    "LOAD_TEST_PASS": "BLOCKED",
    "SOAK_TEST_PASS": "NOT_EXECUTED",
    "POSTGRES_FAILOVER_PASS": "BLOCKED",
    "REDIS_FAILOVER_PASS": "BLOCKED",
    "EVENT_TRANSPORT_FAILOVER_PASS": "BLOCKED",
    "PROCESS_RECOVERY_PASS": "BLOCKED",
    "BACKUP_RESTORE_PASS": "BLOCKED",
    "METRICS_EXPORT_PASS": "BLOCKED",
    "TRACE_EXPORT_PASS": "BLOCKED",
    "ALERT_VERIFICATION_PASS": "BLOCKED",
    "INTERNAL_SECURITY_PASS": "FAIL",
    "EXTERNAL_PENETRATION_TEST_PASS": "BLOCKED",
    "PHYSICAL_RIDER_DEVICE_PASS": "BLOCKED",
    "PHYSICAL_DRIVER_DEVICE_PASS": "BLOCKED",
    "CONTROLLED_PILOT_PASS": "BLOCKED",
    "PUBLIC_PILOT_PASS": "BLOCKED",
    "PRR_APPROVED": "BLOCKED",
    "GA_APPROVED": "BLOCKED",
    "PRODUCTION_READY": "BLOCKED",
}
write_json("ga/NOVARIDE_GA_GATE_MATRIX.json", {**executed, "gates": gates})
write_json(
    "ga/NOVARIDE_GA_EVIDENCE_INDEX.json",
    {**executed, "evidence_root": "artifacts/novaride", "status": "PARTIAL"},
)
write_json(
    "ga/NOVARIDE_GA_RELEASE_MANIFEST.json",
    {**executed, "status": "BLOCKED", "release_artifacts": []},
)
write_text(
    "ga/NOVARIDE_GA_ROLLBACK_PLAN.md",
    "NovaRide GA rollback plan",
    "No GA deployment exists. Before release, define immutable prior artifacts, database compatibility, traffic rollback, feature flags, payment shutdown, communications, owners and tested recovery objectives.",
)
write_text("ga/NOVARIDE_GA_DECISION.md", "NovaRide GA decision", "**BLOCKED.** GA is not approved.")

write_json(
    "final/NOVARIDE_OPERATIONAL_RELEASE_MANIFEST.json",
    {
        **executed,
        "decision": "BLOCKED",
        "current_signed_builds": None,
        "deployment": None,
        "pilot": "NOT_EXECUTED",
        "prr": "BLOCKED",
        "ga": "BLOCKED",
    },
)
write_text(
    "final/NOVARIDE_FINAL_BLOCKERS.md",
    "NovaRide final blockers",
    "1. Resolve repository Ruff failures and Rider/Driver high dependency findings.\n2. Run clean PostgreSQL migrations and production-equivalent PostgreSQL/Redis/Kafka deployment.\n3. Create and verify fresh release-signed branded builds.\n4. Execute live E2E, payment sandbox, load, soak, failover, observability and backup/restore.\n5. Complete independent security review and physical-device acceptance.\n6. Complete real Controlled and Public Pilots.\n7. Record PRR, legal, safety, compliance, operational and executive approvals.",
)
write_json(
    "final/NOVARIDE_FINAL_DECISION.json",
    {
        **executed,
        "decision": "BLOCKED",
        "reason": "Mandatory operational, external, physical-device, pilot and approval gates are incomplete",
        "gates": gates,
    },
)
write_text(
    "final/NOVARIDE_FINAL_RELEASE_REPORT.md",
    "NovaRide final release report",
    "Automated NovaRide tests and all four TypeScript surfaces pass after one Rider action-wiring correction and operations dependency completion. Repository-wide static analysis fails; high mobile dependency findings remain. No current signed build, production-equivalent deployment, live payment/E2E, load/failover/restore, external security assessment, physical-device run, real-user pilot or human approval exists. Final decision: **BLOCKED**.",
)

hash_path = BASE / "final" / "NOVARIDE_EVIDENCE_HASHES.sha256"
lines = []
for path in sorted(BASE.rglob("*")):
    if path.is_file() and path != hash_path:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(ROOT)}")
hash_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"Generated {len(lines) + 1} evidence files under {BASE}")
