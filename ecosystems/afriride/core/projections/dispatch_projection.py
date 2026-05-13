class DispatchProjection:
    """
    Persistent dispatch read model.

    Responsibilities:
    - Track offer attempts
    - Track current dispatch state
    - Track assignment outcome
    - Provide visibility into dispatch lifecycle

    Derived ONLY from events.
    """

    KEY_PREFIX = "dispatch:"

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

        payload = event.payload

        if "ride_id" not in payload:
            return

        ride_id = payload["ride_id"]
        key = self._key(ride_id)

        current = self.store.get(key) or {
            "ride_id": ride_id,
            "status": "PENDING",     # PENDING / OFFERING / ASSIGNED / EXHAUSTED
            "current_driver_id": None,
            "attempt": 0,
            "history": [],           # list of attempts
            "last_update": None,
            "version": 0,
        }

        # --------------------------------------------------
        # DISPATCH EVENTS
        # --------------------------------------------------

        if event.type == "DriverOffered":

            entry = {
                "driver_id": payload["driver_id"],
                "attempt": payload["attempt"],
                "status": "OFFERED",
                "timestamp": event.timestamp,
            }

            current["history"].append(entry)

            current.update({
                "status": "OFFERING",
                "current_driver_id": payload["driver_id"],
                "attempt": payload["attempt"],
            })

        elif event.type == "OfferExpired":

            # mark last attempt as expired
            if current["history"]:
                current["history"][-1]["status"] = "EXPIRED"

            current.update({
                "status": "PENDING",
                "current_driver_id": None,
            })

        elif event.type == "DriverAccepted":

            # mark last attempt as accepted
            if current["history"]:
                current["history"][-1]["status"] = "ACCEPTED"

            current.update({
                "status": "ACCEPTED",
                "current_driver_id": payload["driver_id"],
            })

        elif event.type == "DriverAssigned":

            current.update({
                "status": "ASSIGNED",
                "current_driver_id": payload["driver_id"],
            })

        # --------------------------------------------------
        # TERMINATION EVENTS
        # --------------------------------------------------

        elif event.type in ("TripCompleted", "TripCancelled"):

            current.update({
                "status": "COMPLETED",
                "current_driver_id": None,
            })

        # --------------------------------------------------
        # METADATA UPDATE
        # --------------------------------------------------
        current["last_update"] = event.timestamp
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
        Return all dispatch states (requires store scan support).
        """
        if hasattr(self.store, "scan"):
            results = []
            for key in self.store.scan(f"{self.KEY_PREFIX}*"):
                results.append(self.store.get(key))
            return results

        return []

    def by_status(self, status: str):
        return [
            d for d in self.all()
            if d and d.get("status") == status
        ]

    def active(self):
        """
        Active dispatches (still searching or offering).
        """
        return [
            d for d in self.all()
            if d and d.get("status") in ("PENDING", "OFFERING", "ACCEPTED")
        ]