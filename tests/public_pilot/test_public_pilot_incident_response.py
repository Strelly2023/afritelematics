from __future__ import annotations

import pytest

from tests.public_pilot._helpers import read_text


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_incident_response]


def test_public_pilot_incident_response_documented() -> None:
    text = read_text("docs/public_pilot/PUBLIC_PILOT_INCIDENT_RESPONSE.md")
    for phrase in (
        "severity levels",
        "escalation path",
        "payment incidents",
        "safety incidents",
        "identity fraud incidents",
        "emergency contacts",
        "rollback triggers",
    ):
        assert phrase in text.lower()
