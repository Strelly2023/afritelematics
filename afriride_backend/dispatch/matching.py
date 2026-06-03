from .models import DriverAvailability


def find_available_driver():
    """Return the oldest available driver deterministically.

    No randomness and no client timing race are used. Ties are resolved by
    primary key to keep replay behavior stable.
    """

    availability = (
        DriverAvailability.objects.filter(
            is_available=True,
            driver__role="driver",
        )
        .order_by("updated_at", "id")
        .first()
    )

    if availability is None:
        return None

    return availability.driver
