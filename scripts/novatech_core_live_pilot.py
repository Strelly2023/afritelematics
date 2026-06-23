#!/usr/bin/env python3
"""Run one NovaTech core live-pilot payment flow against a deployed API."""

from __future__ import annotations

import json
import os
import urllib.request


def main() -> None:
    base_url = os.environ.get("NOVATECH_API_BASE_URL", "").rstrip("/")
    token = os.environ.get("NOVATECH_BEARER_TOKEN")
    if not base_url or not token:
        raise SystemExit("NOVATECH_API_BASE_URL and NOVATECH_BEARER_TOKEN are required")
    payload = {
        "intent_id": os.environ.get("NOVATECH_PILOT_INTENT_ID", "external-live-pilot-001"),
        "amount": os.environ.get("NOVATECH_PILOT_AMOUNT", "10.00"),
        "currency": os.environ.get("NOVATECH_PILOT_CURRENCY", "AUD"),
        "destination": os.environ.get("NOVATECH_PILOT_DESTINATION", "external-pilot"),
        "provider": "stripe",
        "live_provider": True,
    }
    req = urllib.request.Request(
        f"{base_url}/v1/core-platform/pilot/flow",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        body = json.loads(response.read().decode("utf-8"))
    print(json.dumps(body, indent=2, sort_keys=True))
    print(f"Explorer: {base_url}{body['trust_explorer']}")
    print(f"PDF: {base_url}{body['trust_explorer']}/audit.pdf")


if __name__ == "__main__":
    main()
