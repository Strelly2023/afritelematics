from ecosystems.afriride.core.domain.aggregates.repository import (
    load_aggregate,
)

from ecosystems.afriride.core.application.dispatch.assignment_strategy import (
    build_driver_queue,
)

from ecosystems.afriride.core.application.dispatch.offer_cycle import (
    start_offer_cycle,
    handle_offer_timeout,
)

from ecosystems.afriride.core.application.commands.accept_driver import (
    accept_driver,
)

from ecosystems.afriride.core.infrastructure.dispatch.dispatcher import (
    accepted_to_assigned,
)


class DispatchEngine:
    """
    Deterministic Dispatch Engine
    """

    def __init__(self, store, metrics=None):
        self.store = store
        self.metrics = metrics

    # --------------------------------------------------
    # LOAD PICKUP FROM HISTORY
    # --------------------------------------------------
    def _load_pickup(self, ride_id):

        events = self.store.load(ride_id)

        for event in events:
            if event.type == "RideRequested":
                return event.payload["pickup"]

        raise Exception("Missing pickup in event history")

    # --------------------------------------------------
    # START DISPATCH
    # --------------------------------------------------
    def start(self, ride_id, drivers):

        agg = load_aggregate(self.store, ride_id)

        if agg.state != "REQUESTED":
            raise Exception("Dispatch must start from REQUESTED")

        pickup = self._load_pickup(ride_id)

        # ✅ deterministic ordering
        driver_queue = build_driver_queue(drivers, pickup)

        if not driver_queue:
            raise Exception("No drivers available")

        offer_event = start_offer_cycle(
            ride_id,
            driver_queue
        )

        self.store.append(
            ride_id,
            agg.version,
            offer_event
        )

        # ✅ metrics
        if self.metrics:
            self.metrics.record_attempt(ride_id)

        # ✅ IMPORTANT: return tuple (NOT dict)
        return offer_event, driver_queue

    # --------------------------------------------------
    # HANDLE TIMEOUT
    # --------------------------------------------------
    def timeout(self, ride_id, driver_queue, attempt):

        events = handle_offer_timeout(
            ride_id=ride_id,
            driver_queue=driver_queue,
            attempt=attempt,
        )

        agg = load_aggregate(self.store, ride_id)

        for event in events:

            self.store.append(
                ride_id,
                agg.version,
                event
            )

            agg.apply(event)

        if self.metrics:
            self.metrics.record_retry(ride_id)
            self.metrics.record_attempt(ride_id)

        return events  # ✅ list[Event]

    # --------------------------------------------------
    # HANDLE ACCEPTANCE
    # --------------------------------------------------
    def accept(self, ride_id, driver_id, attempt):

        # 1. Accept event
        accept_event = accept_driver(
            {
                "ride_id": ride_id,
                "driver_id": driver_id,
                "attempt": attempt,
            },
            self.store
        )

        # 2. Replay AFTER acceptance
        agg = load_aggregate(self.store, ride_id)

        # 3. Transform → assignment event
        assign_event = accepted_to_assigned(accept_event)

        # 4. Apply via aggregate (validation)
        agg.apply(assign_event)

        # 5. Persist assignment
        self.store.append(
            ride_id,
            agg.version - 1,
            assign_event
        )

        if self.metrics:
            self.metrics.record_assignment(ride_id)

        return [accept_event, assign_event]  # ✅ list[Event]

    # --------------------------------------------------
    # REPLAY STATE
    # --------------------------------------------------
    def replay(self, ride_id):
        return load_aggregate(self.store, ride_id)

    # --------------------------------------------------
    # LOAD EVENT HISTORY
    # --------------------------------------------------
    def history(self, ride_id):
        return self.store.load(ride_id)

    # --------------------------------------------------
    # METRICS SNAPSHOT
    # --------------------------------------------------
    def metrics_snapshot(self, ride_id):

        if not self.metrics:
            return None

        return {
            "attempts": self.metrics.get_attempts(ride_id),
            "assigned": self.metrics.is_assigned(ride_id),
            "retries": self.metrics.get_retries(ride_id),
        }