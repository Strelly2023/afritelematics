from ecosystems.core.infrastructure.stream.event_stream import EventStream
from ecosystems.core.infrastructure.stream.streaming_event_store import StreamingEventStore
from ecosystems.core.infrastructure.observability.event_tracer import EventTracer

from ecosystems.afriride.core.domain.events.ride_events import RideRequested


# --------------------------------------------------
# BASIC STREAM PUBLISH TEST
# --------------------------------------------------
def test_streaming_event_store_publish():

    stream = EventStream()
    tracer = EventTracer()

    store = StreamingEventStore(
        stream=stream,
        tracer=tracer,
    )

    received = []

    # --------------------------------------------------
    # Subscribe listener
    # --------------------------------------------------
    def listener(event):
        received.append(event)

    stream.subscribe(listener)

    # --------------------------------------------------
    # Create event (FIXED: includes ride_id)
    # --------------------------------------------------
    event = RideRequested(
        ride_id="ride_001",
        rider_id="r1",
        pickup={"lat": 0, "lng": 0},
        dropoff={"lat": 1, "lng": 1},
    )

    # --------------------------------------------------
    # Persist + publish
    # --------------------------------------------------
    store.append(
        stream_id="ride_001",
        expected_version=0,
        event=event,
    )

    # --------------------------------------------------
    # Assertions
    # --------------------------------------------------
    assert len(received) == 1

    payload = received[0]

    assert payload["stream_id"] == "ride_001"
    assert payload["event"]["type"] == "RideRequested"

    # --------------------------------------------------
    # Verify persistence
    # --------------------------------------------------
    events = store.load("ride_001")

    assert len(events) == 1
    assert events[0].type == "RideRequested"

    # --------------------------------------------------
    # Verify tracing
    # --------------------------------------------------
    logs = tracer.get_logs()

    assert len(logs) == 1
    assert logs[0]["stream_id"] == "ride_001"
    assert logs[0]["event_type"] == "RideRequested"


# --------------------------------------------------
# MULTI-EVENT STREAM TEST
# --------------------------------------------------
def test_streaming_event_store_multiple_events():

    stream = EventStream()
    tracer = EventTracer()

    store = StreamingEventStore(
        stream=stream,
        tracer=tracer,
    )

    received = []

    stream.subscribe(lambda event: received.append(event))

    e1 = RideRequested(
        ride_id="ride_001",
        rider_id="r1",
        pickup={"lat": 0, "lng": 0},
        dropoff={"lat": 1, "lng": 1},
    )

    e2 = RideRequested(
        ride_id="ride_002",
        rider_id="r2",
        pickup={"lat": 5, "lng": 5},
        dropoff={"lat": 6, "lng": 6},
    )

    store.append("ride_001", 0, e1)
    store.append("ride_002", 0, e2)

    assert len(received) == 2

    assert received[0]["stream_id"] == "ride_001"
    assert received[1]["stream_id"] == "ride_002"

    assert len(store.load("ride_001")) == 1
    assert len(store.load("ride_002")) == 1

    assert len(tracer.get_logs()) == 2


# --------------------------------------------------
# VERSION SAFETY TEST
# --------------------------------------------------
def test_streaming_event_store_version_conflict():

    stream = EventStream()

    store = StreamingEventStore(stream=stream)

    event = RideRequested(
        ride_id="ride_001",
        rider_id="r1",
        pickup={"lat": 0},
        dropoff={"lat": 1},
    )

    store.append("ride_001", 0, event)

    try:
        store.append("ride_001", 0, event)  # wrong version again
        assert False, "Expected version conflict"

    except Exception as e:
        assert "version" in str(e).lower()


# --------------------------------------------------
# TRACE FILTER TEST
# --------------------------------------------------
def test_streaming_event_store_trace_filter():

    stream = EventStream()
    tracer = EventTracer()

    store = StreamingEventStore(stream=stream, tracer=tracer)

    e1 = RideRequested(
        ride_id="ride_001",
        rider_id="r1",
        pickup={"lat": 0},
        dropoff={"lat": 1},
    )

    e2 = RideRequested(
        ride_id="ride_002",
        rider_id="r2",
        pickup={"lat": 2},
        dropoff={"lat": 3},
    )

    store.append("ride_001", 0, e1)
    store.append("ride_002", 0, e2)

    ride_1_logs = tracer.get_stream_logs("ride_001")

    assert len(ride_1_logs) == 1
    assert ride_1_logs[0]["stream_id"] == "ride_001"


# --------------------------------------------------
# LOAD ALL STREAMS TEST
# --------------------------------------------------
def test_streaming_event_store_load_all():

    stream = EventStream()
    store = StreamingEventStore(stream=stream)

    e1 = RideRequested(
        ride_id="ride_001",
        rider_id="r1",
        pickup={"lat": 0},
        dropoff={"lat": 1},
    )

    e2 = RideRequested(
        ride_id="ride_002",
        rider_id="r2",
        pickup={"lat": 2},
        dropoff={"lat": 3},
    )

    store.append("ride_001", 0, e1)
    store.append("ride_002", 0, e2)

    streams = store.load_all()

    assert "ride_001" in streams
    assert "ride_002" in streams

    assert len(streams["ride_001"]) == 1
    assert len(streams["ride_002"]) == 1