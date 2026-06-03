from decimal import Decimal


MAX_SURGE_MULTIPLIER = Decimal("2.00")


def calculate_surge_multiplier(predicted_demand, available_drivers):
    if available_drivers <= 0:
        return MAX_SURGE_MULTIPLIER

    ratio = Decimal(predicted_demand) / Decimal(available_drivers)

    if ratio >= 3:
        return Decimal("2.00")
    if ratio >= 2:
        return Decimal("1.50")
    if ratio >= Decimal("1.25"):
        return Decimal("1.20")

    return Decimal("1.00")


def build_surge_proposal(predicted_demand, available_drivers):
    return {
        "authority": "surge_proposal_only",
        "surge_multiplier": calculate_surge_multiplier(
            predicted_demand=predicted_demand,
            available_drivers=available_drivers,
        ),
        "policy_cap": MAX_SURGE_MULTIPLIER,
    }
