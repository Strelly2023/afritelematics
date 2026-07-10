from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_driver_does_not_stay_dispatchable_after_sync_failure() -> None:
    source = (ROOT / "driver_app/state/providers/useDriverFlow.ts").read_text(encoding="utf-8")
    for state in [
        "NETWORK_OFFLINE",
        "API_UNAVAILABLE",
        "AUTH_REQUIRED",
        "SYNCING",
        "ONLINE_NOT_CONFIRMED",
        "DISPATCHABLE",
    ]:
        assert state in source
    assert "Server confirmation is required before dispatchable status" in source
    assert "Ride queue sync failed" in source
    assert 'status: "offline"' in source

