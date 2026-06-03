from .engine import RouteReplayEngine
from .receipts import build_route_replay_receipt


def get_route_replay(ride_id):
    engine = RouteReplayEngine(ride_id=ride_id)
    return {
        "ride_id": ride_id,
        "authority": "visual_proof_projection",
        "route": engine.reconstruct_route(),
        "receipt": build_route_replay_receipt(ride_id=ride_id),
    }
