from ecosystems.afriride.core.infrastructure.geo.geo_index import (
    DriverGeoIndex,
)


def test_geo_index_basic():

    geo = DriverGeoIndex()

    # -----------------------------------------
    # REGISTER DRIVERS
    # -----------------------------------------
    geo.update_driver("d1", 0, 0)
    geo.update_driver("d2", 1, 1)

    pickup = {
        "lat": 0,
        "lng": 0,
    }

    drivers = geo.find_nearby(pickup)

    assert len(drivers) == 2
    assert drivers[0]["id"] == "d1"