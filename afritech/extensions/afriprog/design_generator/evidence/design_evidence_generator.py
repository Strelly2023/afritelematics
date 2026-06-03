from __future__ import annotations

import hashlib
import json

from afritech.extensions.afriprog.evidence.evidence_model import EvidenceRecord


class DesignEvidenceGenerator:
    """Generate evidence records for design proposals."""

    PHASE = "PHASE_3_PROPOSAL_ONLY"

    def from_design(self, design) -> EvidenceRecord:
        payload = design.canonical_dict()
        material = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16].upper()

        return EvidenceRecord(
            evidence_id=f"EVIDENCE-DESIGN-{digest}",
            phase=self.PHASE,
            source="evidence_generator",
            status="proposal_only",
            subject=design.intent,
            payload=payload,
        )
