"""NovaRide Operations Layer aggregation and governed commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from afritech.novaride_runtime.common.errors import AuthorityDenied
from afritech.novaride_runtime.events.hashing import canonical_hash
from afritech.novaride_runtime.models import CircuitBreakerState, DegradedMode, RuntimeContext
from afritech.novaride_runtime.services import NovaRideRuntime, _json


class ConflictResolution(StrEnum):
    SERVER = "server"
    CLIENT_MERGEABLE = "client_mergeable"
    MANUAL_REVIEW = "manual_review"


@dataclass(slots=True)
class OperationsEvidenceReceipt:
    command: str
    subject: str
    reason: str
    approval_reference: str | None
    evidence_hash: str


@dataclass(slots=True)
class OperationsLayerService:
    runtime: NovaRideRuntime
    circuit_overrides: dict[str, CircuitBreakerState] = field(default_factory=dict)
    drained_providers: set[str] = field(default_factory=set)
    low_priority_sync_paused: bool = False
    degraded_mode: DegradedMode = DegradedMode.NORMAL

    def resilience_status(self) -> dict[str, Any]:
        return {
            "resilience": self.runtime.resilience.status(),
            "degraded_mode": self.degraded_mode.value,
            "low_priority_sync_paused": self.low_priority_sync_paused,
            "drained_providers": sorted(self.drained_providers),
            "circuits": {key: value.value for key, value in self.circuit_overrides.items()},
        }

    def providers(self) -> list[dict[str, Any]]:
        health = self.runtime.repositories.provider_health.list()
        names = {record.provider for record in health}.union(self.drained_providers)
        return [
            {
                "provider": name,
                "drained": name in self.drained_providers,
                "latest_health": _json(
                    next((record for record in reversed(health) if record.provider == name), None)
                ),
            }
            for name in sorted(names)
        ]

    def provider_routes(self) -> list[dict[str, Any]]:
        return [_json(route) for route in self.runtime.repositories.provider_routes.list()]

    def conflicts(self) -> list[dict[str, Any]]:
        return [_json(conflict) for conflict in self.runtime.repositories.conflict_records.list()]

    def failovers(self) -> list[dict[str, Any]]:
        return [_json(event) for event in self.runtime.repositories.failover_events.list()]

    def evidence(self) -> list[dict[str, Any]]:
        return [_json(record) for record in self.runtime.repositories.resilience_evidence.list()]

    def offline_queues(self) -> dict[str, Any]:
        operations = self.runtime.repositories.offline_operations.list()
        return {
            "depth": len([item for item in operations if item.status.startswith("QUEUED")]),
            "awaiting_authority": len(
                [item for item in operations if item.status == "AWAITING_AUTHORITATIVE_ACK"]
            ),
            "operations": [_json(item) for item in operations],
        }

    def governed_command(
        self,
        context: RuntimeContext,
        *,
        command: str,
        subject: str,
        reason: str,
        approval_reference: str | None = None,
        high_risk: bool = False,
    ) -> OperationsEvidenceReceipt:
        if (
            "OPERATOR" not in {role.upper() for role in context.roles}
            and context.actor_type.value != "OPERATOR"
        ):
            raise AuthorityDenied("operations_command_requires_operator")
        if high_risk and not approval_reference:
            raise AuthorityDenied("approval_reference_required")
        payload = {
            "command": command,
            "subject": subject,
            "reason": reason,
            "approval_reference": approval_reference,
            "correlation_id": context.correlation_id,
        }
        return OperationsEvidenceReceipt(
            command, subject, reason, approval_reference, canonical_hash(payload)
        )

    def drain_provider(
        self,
        context: RuntimeContext,
        provider: str,
        *,
        reason: str,
        approval_reference: str | None = None,
    ) -> OperationsEvidenceReceipt:
        receipt = self.governed_command(
            context,
            command="drain_provider",
            subject=provider,
            reason=reason,
            approval_reference=approval_reference,
        )
        self.drained_providers.add(provider)
        return receipt

    def restore_provider(
        self, context: RuntimeContext, provider: str, *, reason: str
    ) -> OperationsEvidenceReceipt:
        receipt = self.governed_command(
            context, command="restore_provider", subject=provider, reason=reason
        )
        self.drained_providers.discard(provider)
        return receipt

    def set_circuit(
        self,
        context: RuntimeContext,
        circuit: str,
        state: CircuitBreakerState,
        *,
        reason: str,
        approval_reference: str | None = None,
    ) -> OperationsEvidenceReceipt:
        receipt = self.governed_command(
            context,
            command=f"circuit_{state.value.lower()}",
            subject=circuit,
            reason=reason,
            approval_reference=approval_reference,
            high_risk=circuit.startswith("emergency") and state == CircuitBreakerState.OPEN,
        )
        self.circuit_overrides[circuit] = state
        return receipt
