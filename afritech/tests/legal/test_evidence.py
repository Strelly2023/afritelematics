from __future__ import annotations

import pytest

from afritech.legal.evidence import export_legal_evidence_bundle
from afritech.trust_kernel.events import process_command
from afritech.trust_kernel.policy import Command


@pytest.mark.django_db
def test_legal_export_requires_replayable_evidence_and_signatures():
    event = process_command(
        Command(
            event_type="TripCompleted",
            actor_id="driver:D001",
            subject_id="ride:legal",
            payload={"ride_id": "ride:legal", "status": "completed"},
            signature={"signature_mode": "development_adapter"},
            witnesses=(
                {"verifier_node": "observer-a", "signature": "sig-a"},
                {"verifier_node": "observer-b", "signature": "sig-b"},
            ),
        )
    )

    export = export_legal_evidence_bundle(
        event_id=str(event.event_id),
        jurisdiction="AU-VIC",
        compliance_tags=("pilot", "mobility"),
    )

    assert export.jurisdiction == "AU-VIC"
    assert len(export.export_hash) == 64
    assert export.signatures[0]["type"] == "witness_signature"
