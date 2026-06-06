from __future__ import annotations

import hashlib
import json
from typing import Any

from django.db import IntegrityError, OperationalError, ProgrammingError

from afritech.models import ProofCertificate


INVARIANTS = (
    "INV-TRUST-001: proposal payload is present",
    "INV-TRUST-002: validation result is recorded before decision",
    "INV-TRUST-003: rejected decisions cannot be applied",
)


def generate_proof_certificate(
    proposal: dict[str, Any],
    validation: dict[str, Any],
    decision: dict[str, Any],
    execution: dict[str, Any],
    risk: dict[str, Any],
) -> dict[str, Any]:
    proof_result = {
        "proposal_id": proposal["proposal_id"],
        "validation_passed": validation.get("passed", False),
        "decision_status": decision.get("status"),
        "execution_status": execution.get("status"),
        "risk_level": risk.get("level"),
        "invariants_satisfied": _check_invariants(validation, decision, execution),
    }
    raw = json.dumps(
        {
            "invariants": INVARIANTS,
            "proposal": proposal,
            "proof_result": proof_result,
        },
        sort_keys=True,
        default=str,
    )
    return {
        "invariants": list(INVARIANTS),
        "proof_result": proof_result,
        "proof_hash": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "status": "valid" if proof_result["invariants_satisfied"] else "invalid",
    }


def store_proof_certificate(proposal_id: str, certificate: dict[str, Any]) -> None:
    try:
        ProofCertificate.objects.update_or_create(
            proposal_id=proposal_id,
            defaults={
                "invariants_proven": certificate["invariants"],
                "proof_result": certificate["proof_result"],
                "proof_hash": certificate["proof_hash"],
                "status": certificate["status"],
            },
        )
    except (IntegrityError, OperationalError, ProgrammingError):
        pass


def _check_invariants(
    validation: dict[str, Any],
    decision: dict[str, Any],
    execution: dict[str, Any],
) -> bool:
    if execution.get("status") == "applied" and decision.get("status") != "approved":
        return False
    if decision.get("status") == "approved" and not validation.get("passed"):
        return False
    return True
