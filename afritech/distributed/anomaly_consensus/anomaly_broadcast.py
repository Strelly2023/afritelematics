from __future__ import annotations


def broadcast_anomaly(report: dict[str, object]) -> dict[str, object]:
    return {
        "broadcast": "prepared",
        "report": report,
        "network_send_performed": False,
        "authority": "non_authoritative",
    }


__all__ = ["broadcast_anomaly"]
