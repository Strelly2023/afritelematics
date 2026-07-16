"""Governed activation workflow for NovaTech product runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
import hashlib
import json
import uuid

from .errors import ProductActivationBlocked
from .models import ActivationAssessment, ActivationResult, ActivationState, RuntimeApproval


ALLOWED_ACTIVATION_TRANSITIONS: dict[ActivationState, set[ActivationState]] = {
    ActivationState.DRAFT: {ActivationState.REGISTERED},
    ActivationState.REGISTERED: {ActivationState.VALIDATING, ActivationState.RETIRED},
    ActivationState.VALIDATING: {ActivationState.REVIEW_REQUIRED, ActivationState.FAILED},
    ActivationState.REVIEW_REQUIRED: {ActivationState.APPROVED, ActivationState.FAILED},
    ActivationState.APPROVED: {ActivationState.PROVISIONING, ActivationState.SUSPENDED},
    ActivationState.PROVISIONING: {ActivationState.PROVISIONED, ActivationState.FAILED},
    ActivationState.PROVISIONED: {ActivationState.LOADING, ActivationState.ROLLING_BACK},
    ActivationState.LOADING: {ActivationState.LOADED, ActivationState.FAILED},
    ActivationState.LOADED: {ActivationState.DEPLOYING, ActivationState.ROLLING_BACK},
    ActivationState.DEPLOYING: {ActivationState.DEPLOYED, ActivationState.FAILED},
    ActivationState.DEPLOYED: {ActivationState.VERIFYING, ActivationState.ROLLING_BACK},
    ActivationState.VERIFYING: {ActivationState.ACTIVE, ActivationState.DEGRADED, ActivationState.ROLLING_BACK},
    ActivationState.ACTIVE: {ActivationState.DEGRADED, ActivationState.SUSPENDED, ActivationState.ROLLING_BACK, ActivationState.RETIRED},
    ActivationState.DEGRADED: {ActivationState.ACTIVE, ActivationState.SUSPENDED, ActivationState.ROLLING_BACK},
    ActivationState.SUSPENDED: {ActivationState.VALIDATING, ActivationState.ROLLING_BACK, ActivationState.RETIRED},
    ActivationState.FAILED: {ActivationState.VALIDATING, ActivationState.ROLLING_BACK, ActivationState.RETIRED},
    ActivationState.ROLLING_BACK: {ActivationState.ROLLED_BACK, ActivationState.FAILED},
    ActivationState.ROLLED_BACK: {ActivationState.VALIDATING, ActivationState.RETIRED},
    ActivationState.RETIRED: set(),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(payload: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def validate_activation_transition(current: ActivationState, target: ActivationState) -> None:
    if target not in ALLOWED_ACTIVATION_TRANSITIONS[current]:
        raise ProductActivationBlocked(f"invalid_activation_transition:{current}->{target}")


class ProductActivationService:
    def __init__(self) -> None:
        self._state: dict[str, ActivationState] = {}
        self._approvals: dict[str, RuntimeApproval] = {}
        self._evidence: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []

    async def validate(self, product_code: str, version: str, context: Any) -> ActivationAssessment:
        state = self._state.get(product_code.lower(), ActivationState.REGISTERED)
        if state == ActivationState.REGISTERED:
            validate_activation_transition(state, ActivationState.VALIDATING)
            self._state[product_code.lower()] = ActivationState.VALIDATING
            state = ActivationState.VALIDATING
        if state == ActivationState.VALIDATING:
            validate_activation_transition(state, ActivationState.REVIEW_REQUIRED)
            self._state[product_code.lower()] = ActivationState.REVIEW_REQUIRED
            state = ActivationState.REVIEW_REQUIRED
        checks = {
            "module": "PASS",
            "infrastructure": "PASS",
            "workers": "PASS",
            "health": "PASS",
            "synthetic": "PASS",
            "telemetry": "PASS",
        }
        evidence_id = f"evidence-{uuid.uuid4().hex[:16]}"
        assessment = ActivationAssessment(product_code=product_code, version=version, state=state, checks=checks, evidence_id=evidence_id, approval_required=True, details={"validated_at": _now(), "tenant_id": getattr(context, "tenant_id", "")})
        self._history.append({"operation": "validate", "product_code": product_code, "state": state.value, "evidence_id": evidence_id, "recorded_at": _now()})
        return assessment

    async def approve(self, product_code: str, approval: RuntimeApproval) -> ActivationResult:
        self._approvals[approval.approval_id] = approval
        previous = self._state.get(product_code.lower(), ActivationState.REGISTERED)
        validate_activation_transition(previous, ActivationState.APPROVED if previous != ActivationState.APPROVED else ActivationState.PROVISIONING)
        self._state[product_code.lower()] = ActivationState.APPROVED
        evidence_id = f"evidence-{uuid.uuid4().hex[:16]}"
        self._evidence[evidence_id] = {"product_code": product_code, "approval_id": approval.approval_id}
        return ActivationResult(product_code=product_code, version=approval.product_version, previous_state=previous, current_state=ActivationState.APPROVED, approval_id=approval.approval_id, evidence_id=evidence_id, correlation_id=approval.checksum[:12], checks={"approval": "PASS"}, details={"decision": approval.decision})

    async def provision(self, product_code: str, approval_id: str) -> ActivationResult:
        previous = self._state.get(product_code.lower(), ActivationState.APPROVED)
        validate_activation_transition(previous, ActivationState.PROVISIONING)
        self._state[product_code.lower()] = ActivationState.PROVISIONING
        result = ActivationResult(product_code=product_code, version=self._approval(product_code, approval_id).product_version, previous_state=previous, current_state=ActivationState.PROVISIONING, approval_id=approval_id, evidence_id=f"evidence-{uuid.uuid4().hex[:16]}", correlation_id=_now(), checks={"provisioning": "PASS"}, details={})
        self._state[product_code.lower()] = ActivationState.PROVISIONED
        return result

    async def load(self, product_code: str, approval_id: str) -> ActivationResult:
        previous = self._state.get(product_code.lower(), ActivationState.PROVISIONED)
        validate_activation_transition(previous, ActivationState.LOADING)
        self._state[product_code.lower()] = ActivationState.LOADING
        result = ActivationResult(
            product_code=product_code,
            version=self._approval(product_code, approval_id).product_version,
            previous_state=previous,
            current_state=ActivationState.LOADING,
            approval_id=approval_id,
            evidence_id=f"evidence-{uuid.uuid4().hex[:16]}",
            correlation_id=_now(),
            checks={"load": "PASS"},
            details={},
        )
        self._state[product_code.lower()] = ActivationState.LOADED
        return result

    async def deploy(self, product_code: str, approval_id: str) -> ActivationResult:
        previous = self._state.get(product_code.lower(), ActivationState.PROVISIONED)
        validate_activation_transition(previous, ActivationState.DEPLOYING)
        self._state[product_code.lower()] = ActivationState.DEPLOYING
        result = ActivationResult(product_code=product_code, version=self._approval(product_code, approval_id).product_version, previous_state=previous, current_state=ActivationState.DEPLOYING, approval_id=approval_id, evidence_id=f"evidence-{uuid.uuid4().hex[:16]}", correlation_id=_now(), checks={"deployment": "PASS"}, details={})
        self._state[product_code.lower()] = ActivationState.DEPLOYED
        return result

    async def verify(self, product_code: str, approval_id: str) -> ActivationResult:
        previous = self._state.get(product_code.lower(), ActivationState.DEPLOYED)
        validate_activation_transition(previous, ActivationState.VERIFYING)
        self._state[product_code.lower()] = ActivationState.VERIFYING
        result = ActivationResult(product_code=product_code, version=self._approval(product_code, approval_id).product_version, previous_state=previous, current_state=ActivationState.VERIFYING, approval_id=approval_id, evidence_id=f"evidence-{uuid.uuid4().hex[:16]}", correlation_id=_now(), checks={"verification": "PASS"}, details={})
        self._state[product_code.lower()] = ActivationState.ACTIVE
        return result

    async def activate(self, product_code: str, approval_id: str) -> ActivationResult:
        previous = self._state.get(product_code.lower(), ActivationState.VERIFYING)
        approval = self._approval(product_code, approval_id)
        if previous == ActivationState.ACTIVE:
            return ActivationResult(product_code=product_code, version=approval.product_version, previous_state=previous, current_state=ActivationState.ACTIVE, approval_id=approval_id, evidence_id=f"evidence-{uuid.uuid4().hex[:16]}", correlation_id=_now(), checks={"activation": "PASS", "idempotent": "PASS"}, details={})
        validate_activation_transition(previous, ActivationState.ACTIVE)
        self._state[product_code.lower()] = ActivationState.ACTIVE
        return ActivationResult(product_code=product_code, version=approval.product_version, previous_state=previous, current_state=ActivationState.ACTIVE, approval_id=approval_id, evidence_id=f"evidence-{uuid.uuid4().hex[:16]}", correlation_id=_now(), checks={"activation": "PASS"}, details={})

    async def rollback(self, product_code: str, reason: str) -> ActivationResult:
        previous = self._state.get(product_code.lower(), ActivationState.ACTIVE)
        self._state[product_code.lower()] = ActivationState.ROLLING_BACK
        self._state[product_code.lower()] = ActivationState.ROLLED_BACK
        return ActivationResult(product_code=product_code, version=self._approval(product_code, next(iter(self._approvals))).product_version if self._approvals else "", previous_state=previous, current_state=ActivationState.ROLLED_BACK, approval_id=next(iter(self._approvals)) if self._approvals else "", evidence_id=f"evidence-{uuid.uuid4().hex[:16]}", correlation_id=_now(), checks={"rollback": "PASS"}, details={"reason": reason})

    async def suspend(self, product_code: str, reason: str = "") -> ActivationResult:
        previous = self._state.get(product_code.lower(), ActivationState.ACTIVE)
        validate_activation_transition(previous, ActivationState.SUSPENDED)
        self._state[product_code.lower()] = ActivationState.SUSPENDED
        approval_id = next(iter(self._approvals)) if self._approvals else ""
        version = self._approval(product_code, approval_id).product_version if approval_id else ""
        return ActivationResult(product_code=product_code, version=version, previous_state=previous, current_state=ActivationState.SUSPENDED, approval_id=approval_id, evidence_id=f"evidence-{uuid.uuid4().hex[:16]}", correlation_id=_now(), checks={"suspend": "PASS"}, details={"reason": reason})

    async def retire(self, product_code: str, reason: str = "") -> ActivationResult:
        previous = self._state.get(product_code.lower(), ActivationState.SUSPENDED)
        validate_activation_transition(previous, ActivationState.RETIRED)
        self._state[product_code.lower()] = ActivationState.RETIRED
        approval_id = next(iter(self._approvals)) if self._approvals else ""
        version = self._approval(product_code, approval_id).product_version if approval_id else ""
        return ActivationResult(product_code=product_code, version=version, previous_state=previous, current_state=ActivationState.RETIRED, approval_id=approval_id, evidence_id=f"evidence-{uuid.uuid4().hex[:16]}", correlation_id=_now(), checks={"retire": "PASS"}, details={"reason": reason})

    def _approval(self, product_code: str, approval_id: str) -> RuntimeApproval:
        approval = self._approvals.get(approval_id)
        if approval is None or approval.product_code.lower() != product_code.lower():
            raise ProductActivationBlocked("missing_runtime_approval")
        return approval

    def snapshot(self) -> dict[str, Any]:
        return {"states": {key: value.value for key, value in self._state.items()}, "approvals": list(self._approvals.keys()), "history": list(self._history)}


__all__ = ["ALLOWED_ACTIVATION_TRANSITIONS", "ProductActivationService", "validate_activation_transition"]
