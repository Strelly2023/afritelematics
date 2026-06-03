def recommend_driver_position(zone_snapshots):
    ranked = sorted(
        zone_snapshots,
        key=lambda snapshot: (
            snapshot.predicted_demand,
            -snapshot.available_drivers,
            snapshot.captured_at,
        ),
        reverse=True,
    )

    selected = ranked[0] if ranked else None
    return {
        "authority": "positioning_recommendation_only",
        "recommended_zone_snapshot": selected,
    }
