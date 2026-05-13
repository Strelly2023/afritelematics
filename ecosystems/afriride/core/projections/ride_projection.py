class RideProjection:
    """
    Persistent ride read model.

    Guarantees:
    - Derived ONLY from events
    - Deterministic (replay-safe)
    - No business logic
    - Stored in persistent projection store (Redis/Postgres)
    """

    KEY_PREFIX = "ride:"

    def __init__(self, store):
        self.store = store

    # --------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------
    def _key(self, ride_id: str) -> str:
        return f"{self.KEY_PREFIX}{ride_id}"

    # --------------------------------------------------
    # EVENT REDUCER
    # --------------------------------------------------
    def apply(self, event):

        # Not all events belong to ride stream (defensive)
        if "ride_id" not in event.payload:
            return

        ride_id = event.payload["ride_id"]
        key = self._key(ride_id)

        current = self.store.get(key) or {
            "ride_id": ride_id,
            "state": None,
            "driver_id": None,
            "rider_id": None,
            "pickup": None,
            "dropoff": None,
            "created_at": None,
            "updated_at": None,
            "version": 0,
        }

        # --------------------------------------------------
        # APPLY EVENTS
        # --------------------------------------------------
        if event.type == "RideRequested":

            current.update({
                "ride_id": ride_id,
                "rider_id": event.payload["rider_id"],
                "pickup": event.payload["pickup"],
                "dropoff": event.payload["dropoff"],
                "state": "REQUESTED",
                "created_at": event.timestamp,
            })

        elif event.type == "DriverAssigned":

            current.update({
                "state": "ASSIGNED",
                "driver_id": event.payload["driver_id"],
            })

        elif event.type == "TripStarted":

            current["state"] = "IN_PROGRESS"

        elif event.type == "TripCompleted":

            current["state"] = "COMPLETED"

        elif event.type == "TripCancelled":

            current.update({
                "state": "COMPLETED",  # current design choice
                "cancel_reason": event.payload.get("reason"),
            })

        # --------------------------------------------------
        # METADATA UPDATE
        # --------------------------------------------------
        current["updated_at"] = event.timestamp
        current["version"] += 1

        # --------------------------------------------------
        # PERSIST
        # --------------------------------------------------
        self.store.upsert(key, current)

    # --------------------------------------------------
    # QUERY API
    # --------------------------------------------------
    def get(self, ride_id: str):
        return self.store.get(self._key(ride_id))

    def exists(self, ride_id: str) -> bool:
        return self.get(ride_id) is not None

    def all(self):
        """
        NOTE:
        This requires store support (e.g. Redis SCAN).
        If not implemented, return empty list safely.
        """
        if hasattr(self.store, "scan"):
            results = []
            for key in self.store.scan(f"{self.KEY_PREFIX}*"):
                results.append(self.store.get(key))
            return results

        return []

    def by_state(self, state: str):
        """
        Convenience filter (in-memory).
        For production, use indexed storage instead.
        """
        return [
            ride for ride in self.all()
            if ride and ride.get("state") == state
        ]