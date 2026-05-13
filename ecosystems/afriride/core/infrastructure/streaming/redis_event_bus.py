import json
import redis


class RedisEventBus:
    """
    Event streaming using Redis Streams.

    - Producer: EventStore
    - Consumer: workers (projections, services)
    """

    def __init__(self, url="redis://localhost:6379/0", stream="events"):
        self.client = redis.from_url(url, decode_responses=True)
        self.stream = stream

    # --------------------------------------------------
    # PUBLISH EVENT
    # --------------------------------------------------
    def publish(self, event):
        self.client.xadd(
            self.stream,
            {
                "data": json.dumps(event.to_dict())
            }
        )

    # --------------------------------------------------
    # CONSUME EVENTS
    # --------------------------------------------------
    def subscribe(self, group: str, consumer: str, block=5000):
        """
        Generator for consuming events.
        """
        try:
            self.client.xgroup_create(
                self.stream,
                group,
                id="0",
                mkstream=True,
            )
        except redis.ResponseError:
            pass  # group already exists

        while True:
            messages = self.client.xreadgroup(
                group,
                consumer,
                {self.stream: ">"},
                block=block,
                count=10,
            )

            for _, msgs in messages:
                for msg_id, msg in msgs:
                    yield msg_id, msg

    # --------------------------------------------------
    # ACKNOWLEDGE
    # --------------------------------------------------
    def ack(self, group: str, msg_id: str):
        self.client.xack(self.stream, group, msg_id)