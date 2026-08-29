"""Canonical durable NovaID security-event application authority.

This module is deliberately persistence-thin.  It constructs the existing
SecurityEvent domain model and delegates durability to the authoritative
NovaID unit of work supplied by runtime composition.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from ..domain import SecurityEvent


class SecurityEventAuthority:
    """Record canonical security events through the supplied NovaID UoW."""

    def __init__(self, uow: Any) -> None:
        if uow is None or not callable(
            getattr(uow, "record_security_event", None)
        ):
            raise TypeError(
                "security_event_uow_must_support_record_security_event"
            )
        self._uow = uow

    def record(
        self,
        *,
        event_type: str,
        tenant_id: str,
        actor_type: str,
        actor_id: str,
        subject_type: str,
        subject_id: str,
        outcome: str,
        correlation_id: str,
        request_id: str,
        reason_codes: tuple[str, ...] = (),
        session_id: str = "",
        source: str = "",
        metadata: dict[str, Any] | None = None,
        severity: str = "INFO",
    ) -> SecurityEvent:
        event_metadata = dict(metadata or {})

        # Preserve application-level context not represented as first-class
        # fields by the existing canonical SecurityEvent domain object.
        event_metadata.setdefault("actor_type", actor_type)
        event_metadata.setdefault("subject_type", subject_type)

        if session_id:
            event_metadata.setdefault("session_id", session_id)

        if source:
            event_metadata.setdefault("source", source)

        event = SecurityEvent(
            event_id="se_" + uuid4().hex,
            event_type=event_type,
            severity=severity,
            tenant_id=tenant_id,
            actor_identity_id=actor_id,
            subject_identity_id=subject_id,
            correlation_id=correlation_id,
            request_id=request_id,
            outcome=outcome,
            reason_codes=tuple(reason_codes),
            metadata=event_metadata,
        )

        self._uow.record_security_event(event)
        return event


__all__ = ["SecurityEventAuthority"]
