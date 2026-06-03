from gps.fraud_detection import detect_location_anomalies
from gps.services import verify_location_chain

from .engine import RouteReplayEngine


def build_route_replay_receipt(ride_id):
    engine = RouteReplayEngine(ride_id=ride_id)
    route = engine.reconstruct_route()
    chain_status = verify_location_chain(ride_id=ride_id)
    anomaly_status = detect_location_anomalies(ride_id=ride_id)

    return {
        "ride_id": ride_id,
        "authority": "route_replay_projection",
        "point_count": len(route),
        "route_verified": chain_status["verified"] and not anomaly_status["anomaly_detected"],
        "gps_chain_verified": chain_status["verified"],
        "distance_km": engine.distance_km(),
        "duration_minutes": engine.duration_minutes(),
        "anomalies": anomaly_status["anomalies"],
    }
