from __future__ import annotations

import pytest

from tests.public_pilot._helpers import read_text


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_incident_response]


def test_public_pilot_disaster_recovery_documented() -> None:
    text = read_text("docs/public_pilot/PUBLIC_PILOT_DISASTER_RECOVERY.md")
    for phrase in (
        "backup policy",
        "restore validation",
        "rollback procedures",
        "emergency disable switches",
        "restore a non-production snapshot",
    ):
        assert phrase in text.lower()
