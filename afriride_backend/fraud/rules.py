from .anomaly_detection import (
    detect_missing_gps,
    detect_replay_route_gap,
    detect_speed_anomaly,
)


def evaluate_fraud_rules(replay_data):
    route = replay_data.get("route", [])

    checks = [
        detect_replay_route_gap(replay_data),
        detect_missing_gps(route),
        detect_speed_anomaly(route),
    ]

    return [check for check in checks if check["anomaly"]]
