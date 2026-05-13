from ecosystems.afriride.bootstrap import build_system
from ecosystems.afriride.core.application.dispatch.dispatch_engine import DispatchEngine

system = build_system()
store = system["store"]

dispatch = DispatchEngine(store)


def run_dispatch(ride_id, drivers):
    """
    Background worker for dispatch cycle.
    """
    offer_event, queue = dispatch.start(ride_id, drivers)

    return {
        "offer": offer_event.to_dict(),
        "queue": queue
    }