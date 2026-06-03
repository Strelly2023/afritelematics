RUNBOOKS = {
    "replay_degradation": [
        "freeze regional expansion",
        "inspect EventLog continuity",
        "compare replay receipts",
        "open incident if divergence persists",
    ],
    "payment_degradation": [
        "verify provider routing",
        "compare Payment and DriverEarning ledgers",
        "pause payment capture if mismatch appears",
    ],
    "region_unavailable": [
        "activate failover assessment",
        "route read-only operator traffic to backup",
        "preserve EventLog and payment integrity",
    ],
}


def get_runbook(key):
    return {
        "key": key,
        "steps": RUNBOOKS.get(key, []),
    }
