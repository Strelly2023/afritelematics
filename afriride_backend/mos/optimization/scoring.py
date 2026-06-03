def score_journey_option(option):
    cost = option.get("cost", 0)
    duration_minutes = option.get("duration_minutes", 0)
    availability = option.get("availability", 0)
    trust = option.get("trust", 0)

    return (
        (100 - cost)
        + (100 - duration_minutes)
        + (availability * 10)
        + (trust * 10)
    )


def rank_journey_options(options):
    ranked = sorted(
        [
            {
                **option,
                "score": score_journey_option(option),
                "authority": "journey_recommendation_only",
            }
            for option in options
        ],
        key=lambda option: option["score"],
        reverse=True,
    )
    return ranked
