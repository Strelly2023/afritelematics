import json
import time
from typing import Optional

from ecosystems.afriride.domain.events.ride_events import Event


class ProjectionWorker:
    """
    Background worker for processing events from EventBus
    and applying them to projections.

    Responsibilities:
    - Consume events from Redis Streams (or any EventBus)
    - Deserialize events
    - Apply to ProjectionBus
    - Acknowledge messages
    - Handle failures safely

    Guarantees:
    - At-least-once delivery
    - Deterministic projection updates
    """

    def __init__(
        self,
        event_bus,
        projection_bus,
        group: str = "projection_group",
        consumer: str = "worker-1",
        sleep_on_error: float = 1.0,
    ):
        self.event_bus = event_bus
        self.projection_bus = projection_bus
        self.group = group
        self.consumer = consumer
        self.sleep_on_error = sleep_on_error
        self.running = False

    # --------------------------------------------------
    # START WORKER LOOP
    # --------------------------------------------------
    def run(self):
        """
        Start consuming events indefinitely.
        """
        self.running = True

        print(f"[ProjectionWorker] STARTED consumer={self.consumer}")

        while self.running:
            try:
                for msg_id, msg in self.event_bus.subscribe(
                    group=self.group,
                    consumer=self.consumer,
                ):
                    self._process_message(msg_id, msg)

            except Exception as e:
                self._handle_error("LOOP", None, e)
                time.sleep(self.sleep_on_error)

    # --------------------------------------------------
    # PROCESS SINGLE MESSAGE
    # --------------------------------------------------
    def _process_message(self, msg_id: str, msg: dict):
        """
        Deserialize and apply event.
        """

        try:
            # ----------------------------------------
            # 1. PARSE EVENT
            # ----------------------------------------
            data = json.loads(msg["data"])
            event = Event.from_dict(data)

            # ----------------------------------------
            # 2. APPLY TO PROJECTIONS
            # ----------------------------------------
            self.projection_bus.publish(event)

            # ----------------------------------------
            # 3. ACKNOWLEDGE MESSAGE
            # ----------------------------------------
            self.event_bus.ack(self.group, msg_id)

            # Optional: debug log
            self._log_event(event, msg_id)

        except Exception as e:
            self._handle_error("PROCESS", msg_id, e)

            # ⚠️ DO NOT ACK → message will be retried
            # This ensures at-least-once delivery

    # --------------------------------------------------
    # STOP WORKER
    # --------------------------------------------------
    def stop(self):
        self.running = False
        print(f"[ProjectionWorker] STOPPED consumer={self.consumer}")

    # --------------------------------------------------
    # LOGGING (OPTIONAL)
    # --------------------------------------------------
    def _log_event(self, event, msg_id):
        print(
            f"[ProjectionWorker] processed "
            f"type={event.type} msg_id={msg_id}"
        )

    # --------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------
    def _handle_error(self, stage: str, msg_id: Optional[str], error: Exception):
        print(
            f"[ProjectionWorker ERROR] "
            f"stage={stage} msg_id={msg_id} error={str(error)}"
        )

if __name__ == "__main__":
    from ecosystems.afriride.bootstrap import build_system
    from ecosystems.afriride.core.application.adapters.workers.projection_worker import ProjectionWorker

    system = build_system(use_event_streaming=True)

    if not system["event_bus"]:
        raise Exception("❌ Event streaming is disabled. Set use_event_streaming=True")

    worker = ProjectionWorker(
        event_bus=system["event_bus"],
        projection_bus=system["projection_bus"],
        consumer="worker-1",
    )

    worker.run()