"""Ride lifecycle state definitions."""

from __future__ import annotations


class RideState:
    REQUESTED = "REQUESTED"
    MATCHED = "MATCHED"
    ACCEPTED = "ACCEPTED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"

    ORDER = (REQUESTED, MATCHED, ACCEPTED, STARTED, COMPLETED, VERIFIED)
