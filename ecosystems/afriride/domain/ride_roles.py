# ecosystems/afriride/core/domain/ride_roles.py

from enum import Enum


class RideAuthorityRole(str, Enum):
    """
    Domain-owned authority roles.
    These represent WHO actors are, not WHAT they can do.
    """

    RIDER = "rider"
    DRIVER = "driver"
    DISPATCHER = "dispatcher"
    SYSTEM = "system"
    ADMIN = "admin"