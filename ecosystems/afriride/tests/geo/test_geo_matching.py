from ecosystems.afriride.core.infrastructure.geo.geo_index import (
    DriverGeoIndex,
)

from ecosystems.afriride.core.infrastructure.geo.geo_matcher import (
    GeoMatcher,
)


def test_geo_matcher():

    geo = DriverGeoIndex()

    geo.update_driver("d1", 0.1, 0.1)
    geo.update_driver("d2", 5, 5)

    matcher = GeoMatcher(geo)

    pickup = {
        "lat": 0,
        "lng": 0,
    }

    drivers = matcher.match(pickup)

    assert drivers[0]["id"] == "d1"