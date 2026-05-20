class RequestRideCommand:
    def __init__(self, rider_id, pickup, dropoff, authority):
        self.rider_id = rider_id
        self.pickup = pickup
        self.dropoff = dropoff
        self.authority = authority


class AssignDriverCommand:
    def __init__(self, ride_id, driver_id, authority):
        self.ride_id = ride_id
        self.driver_id = driver_id
        self.authority = authority
