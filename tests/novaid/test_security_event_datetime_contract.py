from datetime import datetime
from typing import Any
from uuid import uuid4

from afritech.novaid.application.authentication import (
    DurableAuthenticationService,
)
from afritech.novaid.domain import SecurityEvent


def uid() -> str:
    return str(uuid4())


class CapturingUnitOfWork:
    def __init__(self) -> None:
        self.events: list[SecurityEvent] = []

    def record_security_event(self, event: SecurityEvent) -> None:
        self.events.append(event)


def test_authentication_security_event_uses_canonical_datetime_contract() -> None:
    store = CapturingUnitOfWork()

    service = DurableAuthenticationService(
        store,  # type: ignore[arg-type]
        pepper=b"security-event-contract-pepper-value",
    )

    service._event(
        event_type="IDENTITY_REGISTRATION_CREATED",
        tenant=uid(),
        actor=uid(),
        subject=uid(),
        correlation=uid(),
        request=uid(),
    )

    assert len(store.events) == 1

    event = store.events[0]

    assert isinstance(event, SecurityEvent)
    assert isinstance(event.occurred_at, datetime)
    assert isinstance(event.recorded_at, datetime)
    assert isinstance(event.reason_codes, tuple)
    assert event.outcome == "SUCCESS"
