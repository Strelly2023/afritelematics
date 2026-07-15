"""NovaRide runtime authority guard."""

FORBIDDEN_FRONTEND_AUTHORITIES = {
    "driver_dispatchability",
    "confirmed_booking",
    "payment_success",
    "identity_verification",
    "emergency_resolution",
}


def assert_frontend_not_authoritative(authority: str) -> None:
    if authority in FORBIDDEN_FRONTEND_AUTHORITIES:
        raise PermissionError(f"frontend_authority_forbidden:{authority}")
