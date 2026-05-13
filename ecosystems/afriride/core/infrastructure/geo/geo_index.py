from math import sqrt


class DriverGeoIndex:
    """
    In-memory geo index for active drivers

    Responsibilities:
    - track available drivers
    - update location
    - query nearby drivers
    """

    def __init__(self):
        # driver_id -> {lat, lng}
        self.drivers = {}

    # --------------------------------------------------
    # REGISTER / UPDATE DRIVER LOCATION
    # --------------------------------------------------
    def update_driver(self, driver_id, lat, lng):
        self.drivers[driver_id] = {"lat": lat, "lng": lng}

    # --------------------------------------------------
    # REMOVE DRIVER (offline)
    # --------------------------------------------------
    def remove_driver(self, driver_id):
        if driver_id in self.drivers:
            del self.drivers[driver_id]

    # --------------------------------------------------
    # FIND NEARBY DRIVERS
    # --------------------------------------------------
    def find_nearby(self, pickup, radius=None):
        """
        Returns drivers sorted by distance

        radius: optional max distance filter
        """

        def distance(d):
            return sqrt(
                (d["lat"] - pickup["lat"]) ** 2 +
                (d["lng"] - pickup["lng"]) ** 2
            )

        results = []

        for driver_id, location in self.drivers.items():
            d = distance(location)

            if radius is None or d <= radius:
                results.append({
                    "id": driver_id,
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "distance": d
                })

        # ✅ deterministic ordering
        return sorted(results, key=lambda x: (x["distance"], x["id"]))
