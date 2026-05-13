class DriverProjection:
    """
    Persistent driver read model.

    Responsibilities:
    - Track driver availability (online/offline)
    - Track last known location
    - Track ride assignment status
    - Fully derived from events
    """

    KEY_PREFIX = "driver:"

    def __init__(self, store):
        self.store = store

    # --------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------
    def _key(self, driver_id: str) -> str:
        return f"{self.KEY_PREFIX}{driver_id}"

    # --------------------------------------------------
    # EVENT REDUCER
    # --------------------------------------------------
    def apply(self, event):

        payload = event.payload

        # Only process events with driver_id
        if "driver_id" not in payload:
            return

        driver_id = payload["driver_id"]
        key = self._key(driver_id)

        current = self.store.get(key) or {
            "driver_id": driver_id,
            "status": "OFFLINE",         # OFFLINE / ONLINE / BUSY
            "lat": None,
            "lng": None,
            "current_ride_id": None,
            "last_update": None,
            "version": 0,
        }

        # --------------------------------------------------
        # DRIVER PRESENCE EVENTS
        # --------------------------------------------------
        if event.type == "DriverOnline":

            current.update({
                "status": "ONLINE",
                "lat": payload["lat"],
                "lng": payload["lng"],
            })

        elif event.type == "DriverLocationUpdated":

            current.update({
                "lat": payload["lat"],
                "lng": payload["lng"],
            })

        elif event.type == "DriverOffline":

            current.update({
                "status": "OFFLINE",
                "current_ride_id": None,
            })

        # --------------------------------------------------
        # DISPATCH / RIDE EVENTS
        # --------------------------------------------------
        elif event.type == "DriverAssigned":

            current.update({
                "status": "BUSY",
                "current_ride_id": payload["ride_id"],
            })

        elif event.type == "TripCompleted":

            # Driver becomes available again
            current.update({
                "status": "ONLINE",
                "current_ride_id": None,
            })

        elif event.type == "TripCancelled":

            # Also release driver if ride cancelled
            current.update({
                "status": "ONLINE",
                "current_ride_id": None,
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
    def get(self, driver_id: str):
        return self.store.get(self._key(driver_id))

    def exists(self, driver_id: str) -> bool:
        return self.get(driver_id) is not None

    def all(self):
        """
        Return all drivers (requires store scan support)
        """
        if hasattr(self.store, "scan"):
            results = []
            for key in self.store.scan(f"{self.KEY_PREFIX}*"):
                results.append(self.store.get(key))
            return results

        return []

    def available(self):
        """
        Drivers available for dispatch (ONLINE only).
        """
        return [
            d for d in self.all()
            if d and d.get("status") == "ONLINE"
        ]

    def busy(self):
        """
        Drivers currently assigned.
        """
        return [
            d for d in self.all()
            if d and d.get("status") == "BUSY"
        ]
