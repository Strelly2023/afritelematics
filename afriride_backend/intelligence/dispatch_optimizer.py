def score_driver_for_ride(driver, ride, distance_km, acceptance_rate, replay_quality):
    return (
        (100 - distance_km)
        + (acceptance_rate * 20)
        + (replay_quality * 30)
    )


def choose_best_driver(candidates):
    if not candidates:
        return None

    return sorted(candidates, key=lambda item: item["score"], reverse=True)[0]


def build_dispatch_recommendation(candidates):
    return {
        "authority": "dispatch_recommendation_only",
        "recommended_candidate": choose_best_driver(candidates),
    }
