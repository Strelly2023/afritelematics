from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from afriride_system.api.auth import JWT
from afriride_system.api.main import app
from afriride_system.integration.websocket_gateway.mobility_hub import (
    MobilityHub,
    RedisMobilityHub,
    mobility_hub,
)


class SharedFakeRedis:
    def __init__(self) -> None:
        self.streams: dict[str, list[tuple[str, dict[str, str]]]] = {}
        self.values: dict[str, str] = {}
        self.sequence = 0

    def xadd(self, stream, fields, **_kwargs):
        self.sequence += 1
        stream_id = f"1719981234567-{self.sequence}"
        self.streams.setdefault(stream, []).append((stream_id, fields))
        return stream_id

    def xread(self, streams, **_kwargs):
        result = []
        for stream, cursor in streams.items():
            cursor_tuple = tuple(map(int, cursor.split("-")))
            messages = [
                item for item in self.streams.get(stream, [])
                if tuple(map(int, item[0].split("-"))) > cursor_tuple
            ]
            if messages:
                result.append((stream, messages))
        return result

    def set(self, key, value, **_kwargs):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)


def test_mobility_hub_replays_targeted_events_after_cursor() -> None:
    hub = MobilityHub()
    first = hub.publish(
        "DISPATCH_REQUESTED",
        targets={"actor:driver-1", "role:driver"},
        data={"ride_id": "ride-1"},
    )
    hub.publish(
        "RIDE_STATE_UPDATED",
        targets={"actor:rider-2"},
        data={"ride_id": "ride-2"},
    )

    replay = hub.events_after(0, {"actor:driver-1"})
    assert replay == [first]
    assert hub.events_after(first["sequence"], {"actor:driver-1"}) == []


def test_driver_presence_expires_without_heartbeat() -> None:
    hub = MobilityHub(presence_ttl_seconds=0)
    hub.heartbeat("driver-1")
    assert hub.presence("driver-1")["status"] == "offline"


def test_redis_adapter_shares_events_and_presence_across_instances() -> None:
    redis = SharedFakeRedis()
    producer = RedisMobilityHub(redis)
    consumer = RedisMobilityHub(redis)
    event = producer.publish(
        "RIDE_STATE_UPDATED",
        targets={"ride:ride-1", "actor:rider-1"},
        partition="ride:ride-1",
        data={"ride_id": "ride-1", "status": "started"},
    )
    replay = consumer.events_after("0-0", {"actor:rider-1"})
    assert replay[0]["trace_id"] == event["trace_id"]
    assert replay[0]["partition"] == "ride:ride-1"
    producer.heartbeat("driver-1")
    assert consumer.presence("driver-1")["status"] == "online"


def test_mobility_socket_authenticates_heartbeats_and_replays_events() -> None:
    mobility_hub.reset()
    token = JWT.create_token("driver-live-1", "DRIVER")
    event = mobility_hub.publish(
        "DISPATCH_REQUESTED",
        targets={"actor:driver-live-1"},
        data={"ride_id": "ride-live-1"},
    )

    with TestClient(app) as client:
        with client.websocket_connect(
            f"/ws/mobility/driver-live-1?token={token}&cursor=0"
        ) as websocket:
            ready = websocket.receive_json()
            replay = websocket.receive_json()
            assert ready["type"] == "SESSION_READY"
            assert replay == event

            websocket.send_json({"type": "HEARTBEAT", "cursor": event["sequence"]})
            acknowledgement = websocket.receive_json()
            assert acknowledgement["type"] == "HEARTBEAT_ACK"
            assert acknowledgement["data"]["status"] == "online"


def test_mobility_socket_rejects_actor_impersonation() -> None:
    token = JWT.create_token("driver-a", "DRIVER")
    with TestClient(app) as client:
        try:
            with client.websocket_connect(
                f"/ws/mobility/driver-b?token={token}"
            ) as websocket:
                websocket.receive_json()
        except WebSocketDisconnect as exc:
            assert exc.code == 1008
        else:
            raise AssertionError("actor impersonation websocket was accepted")
