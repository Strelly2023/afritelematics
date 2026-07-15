"""Offline authority guard."""

OFFLINE_FORBIDDEN = {"accept_trip_confirmed", "start_trip_confirmed", "complete_trip_confirmed", "payment_confirmed", "emergency_resolved"}


def assert_offline_operation_safe(operation: str) -> None:
    if operation in OFFLINE_FORBIDDEN:
        raise PermissionError(f"offline_authority_forbidden:{operation}")
