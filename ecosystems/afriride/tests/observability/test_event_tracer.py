from afritech.core.infrastructure.observability.event_tracer import EventTracer
from ecosystems.afriride.domain.events.ride_events import RideRequested


def test_event_tracing():

    tracer = EventTracer()

    event = RideRequested(
        rider_id="r1",
        pickup={"lat": 0},
        dropoff={"lat": 1},
    )

    tracer.trace("ride_001", event)

    logs = tracer.get_logs()

    assert len(logs) == 1
    assert logs[0]["event_type"] == "RideRequested"