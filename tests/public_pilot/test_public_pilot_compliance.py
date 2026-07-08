from __future__ import annotations

import pytest

from tests.public_pilot._helpers import read_text


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_compliance]


def test_public_pilot_compliance_documented() -> None:
    text = read_text("docs/public_pilot/PUBLIC_PILOT_COMPLIANCE.md")
    for phrase in (
        "KYC",
        "KYB",
        "AML/CTF",
        "sanctions",
        "privacy",
        "retention",
        "consent",
    ):
        assert phrase.lower() in text.lower()
