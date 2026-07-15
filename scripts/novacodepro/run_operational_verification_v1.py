#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from afritech.novacodepro.operational_verification.service import OperationalVerificationService


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", required=True)
    parser.add_argument("--release", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--evidence-dir", default="reports/novacodepro/operational-verification")
    args = parser.parse_args()

    service = OperationalVerificationService()
    program = service.create_program({"release_id": args.release, "environment": args.environment})
    run = service.execute_program(program["id"])
    service.collect_development_evidence("operational-verification-v1", "repository automation", args.release, run["id"], args.environment)
    prr = service.generate_prr_package(args.release, args.environment)
    report = {
        "version": "1.0",
        "repository": {"implemented": True, "tests_passed": None, "tests_failed": None, "portal_build": None, "migration_status": "created"},
        "observability": {"configured": True, "executed": False, "verified": False, "provider": "configured", "evidence_refs": []},
        "accessibility": {"configured": True, "executed": False, "verified": False, "wcag_level": "AA", "critical_violations": None, "serious_violations": None, "human_screen_reader_validation": "PENDING", "evidence_refs": []},
        "visual_regression": {"configured": True, "executed": False, "verified": False, "approved_baseline": False, "regressions": None, "evidence_refs": []},
        "digital_ux_twin": {"configured": True, "telemetry_connected": False, "telemetry_fresh": False, "executed": False, "verified": False, "evidence_refs": []},
        "prr": {"package_generated": True, "package_signed": True, "recommendation": prr["recommendation"], "approved": False, "evidence_refs": []},
        "executive": {"approval_requested": False, "approved": False, "approver_id": None, "approver_role": None, "signature": None, "evidence_refs": []},
        "ga": {"eligible": False, "authorized": False, "active": False, "reason": "Live evidence and governance approvals pending"},
        "payments": {"current_state": "DISABLED", "finance_approved": False, "risk_approved": False, "provider_certified": False, "settlement_verified": False, "reconciliation_verified": False, "fraud_verified": False, "real_payments_enabled": False},
        "honest_status": {"repository": "OPERATIONAL_VERIFICATION_AUTOMATION_V1_IMPLEMENTED", "live_environment": "EVIDENCE_PENDING", "governance": "APPROVAL_PENDING"},
    }
    out = Path(args.evidence_dir) / "operational-verification-v1-summary.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(str(report) + "\n")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
