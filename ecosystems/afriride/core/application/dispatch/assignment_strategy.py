from ecosystems.afriride.core.infrastructure.matching.driver_matcher import rank_drivers


def build_driver_queue(drivers, pickup):
    """
    Deterministic driver ordering
    """
    return rank_drivers(drivers, pickup)
