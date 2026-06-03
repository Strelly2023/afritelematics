def detect_speed_anomaly(route_points, max_speed_kmh=160):
    for point in route_points:
        if point.get("speed", 0) and point["speed"] > max_speed_kmh:
            return {
                "anomaly": True,
                "type": "speed_anomaly",
                "reason": "Speed exceeded allowed threshold",
            }

    return {"anomaly": False}


def detect_missing_gps(route_points, minimum_points=3):
    if len(route_points) < minimum_points:
        return {
            "anomaly": True,
            "type": "missing_gps",
            "reason": "Insufficient route evidence",
        }

    return {"anomaly": False}


def detect_replay_route_gap(replay_data):
    if not replay_data.get("route"):
        return {
            "anomaly": True,
            "type": "missing_route_replay",
            "reason": "Replay did not include route evidence",
        }

    return {"anomaly": False}
