"""Partner SDK for NovaTrust public verification artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import request

from afritech.core_platform.signing import verify_packet_signature


@dataclass(frozen=True)
class NovaTrustVerificationResult:
    trust_id: str
    verified: bool
    explorer_url: str
    pdf_url: str
    bundle_url: str
    control_count: int

    def canonical(self) -> dict[str, Any]:
        return {
            "trust_id": self.trust_id,
            "verified": self.verified,
            "explorer_url": self.explorer_url,
            "pdf_url": self.pdf_url,
            "bundle_url": self.bundle_url,
            "control_count": self.control_count,
        }


class NovaTrustClient:
    """Small dependency-free client for the public NovaTrust contract."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def explorer_url(self, trust_id: str) -> str:
        return f"{self.base_url}/trust/explorer/{trust_id}"

    def audit_pdf_url(self, trust_id: str) -> str:
        return f"{self.explorer_url(trust_id)}/audit.pdf"

    def bundle_url(self, trust_id: str) -> str:
        return f"{self.explorer_url(trust_id)}/bundle.zip"

    def fetch_packet(self, trust_id: str) -> dict[str, Any]:
        return self._get_json(self.explorer_url(trust_id))

    def fetch_signature(self, trust_id: str) -> dict[str, Any]:
        return self._get_json(f"{self.explorer_url(trust_id)}/signature")

    def fetch_compliance_report(self, trust_id: str) -> dict[str, Any]:
        return self._get_json(f"{self.explorer_url(trust_id)}/compliance-report")

    def fetch_anchor(self, trust_id: str) -> dict[str, Any]:
        return self._get_json(f"{self.explorer_url(trust_id)}/anchor")

    def fetch_optional_blockchain_anchor(self, trust_id: str) -> dict[str, Any]:
        return self._get_json(f"{self.explorer_url(trust_id)}/anchor/blockchain")

    def verify(self, trust_id: str) -> NovaTrustVerificationResult:
        packet_response = self.fetch_packet(trust_id)
        signature_response = self.fetch_signature(trust_id)
        compliance = self.fetch_compliance_report(trust_id)
        packet = packet_response["packet"]
        signature = signature_response["signature"]
        if not isinstance(packet, dict) or not isinstance(signature, dict):
            raise ValueError("NovaTrust public contract returned invalid packet or signature")
        return NovaTrustVerificationResult(
            trust_id=trust_id,
            verified=verify_packet_signature(packet, signature),
            explorer_url=self.explorer_url(trust_id),
            pdf_url=self.audit_pdf_url(trust_id),
            bundle_url=self.bundle_url(trust_id),
            control_count=len(compliance.get("controls", [])),
        )

    def _get_json(self, url: str) -> dict[str, Any]:
        req = request.Request(url, headers={"Accept": "application/json"})
        with request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{url} did not return a JSON object")
        return payload
