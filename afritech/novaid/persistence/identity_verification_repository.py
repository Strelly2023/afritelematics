"""Canonical identity-verification persistence contract.

This module defines the storage-neutral repository boundary for the
NovaID identity-verification aggregate.

The contract deliberately contains no SQLite, PostgreSQL, ORM, API,
or runtime-specific behaviour. Concrete adapters must preserve the
same tenant isolation, concurrency, and event-ordering semantics.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from afritech.novaid.domain import (
    IdentityVerificationEvidence,
    IdentityVerificationOutcomeEvent,
    IdentityVerificationRecord,
    RequestContext,
)


@runtime_checkable
class IdentityVerificationRepository(Protocol):
    """Storage-neutral identity-verification repository.

    Required invariants
    -------------------
    * All reads are scoped by ``RequestContext.tenant_id``.
    * Cross-tenant reads fail closed.
    * Aggregate updates use optimistic concurrency.
    * Outcome events are immutable and append-only.
    * Event lists are returned in deterministic occurrence order.
    * Implementations must not persist raw biometric material.
    """

    def add_identity_verification_evidence(
        self,
        evidence: IdentityVerificationEvidence,
    ) -> None:
        """Persist one immutable verification-evidence record."""

    def get_identity_verification_evidence(
        self,
        context: RequestContext,
        evidence_id: str,
    ) -> IdentityVerificationEvidence:
        """Return tenant-scoped evidence or fail closed."""

    def identity_verification_evidence_exists(
        self,
        context: RequestContext,
        evidence_id: str,
    ) -> bool:
        """Return whether tenant-scoped evidence exists."""

    def add_identity_verification(
        self,
        verification: IdentityVerificationRecord,
    ) -> None:
        """Persist a new identity-verification aggregate."""

    def get_identity_verification(
        self,
        context: RequestContext,
        verification_id: str,
    ) -> IdentityVerificationRecord:
        """Return a tenant-scoped verification aggregate."""

    def get_identity_verification_by_workflow(
        self,
        context: RequestContext,
        workflow_id: str,
    ) -> IdentityVerificationRecord:
        """Return the verification associated with a workflow."""

    def identity_verification_exists(
        self,
        context: RequestContext,
        verification_id: str,
    ) -> bool:
        """Return whether a tenant-scoped verification exists."""

    def update_identity_verification(
        self,
        context: RequestContext,
        verification: IdentityVerificationRecord,
        *,
        expected_version: int,
    ) -> None:
        """Update an aggregate using optimistic concurrency."""

    def add_identity_verification_outcome_event(
        self,
        event: IdentityVerificationOutcomeEvent,
    ) -> None:
        """Append one immutable verification outcome event."""

    def get_identity_verification_outcome_event(
        self,
        context: RequestContext,
        event_id: str,
    ) -> IdentityVerificationOutcomeEvent:
        """Return one tenant-scoped outcome event."""

    def list_identity_verification_outcome_events(
        self,
        context: RequestContext,
        verification_id: str,
    ) -> list[IdentityVerificationOutcomeEvent]:
        """Return outcome events in deterministic occurrence order."""


__all__ = [
    "IdentityVerificationRepository",
]
