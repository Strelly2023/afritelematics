class GeoMatcher:
    """
    Matching adapter between
    geo index and dispatch engine.
    """

    def __init__(self, geo_index):
        self.geo_index = geo_index

    # -------------------------------------------------
    # FIND BEST DRIVERS
    # -------------------------------------------------
    def match(self, pickup, radius=None):

        return self.geo_index.find_nearby(
            pickup,
            radius=radius
        )