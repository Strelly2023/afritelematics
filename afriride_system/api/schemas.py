"""Request and response schemas for the AfriRide API."""

from __future__ import annotations

from pydantic import BaseModel


class RequestRide(BaseModel):
    passenger_id: str
    pickup: str
    destination: str
    ride_id: str | None = None


class CancelRide(BaseModel):
    passenger_id: str
    ride_id: str


class DriverStatus(BaseModel):
    driver_id: str
    online: bool


class RideAction(BaseModel):
    driver_id: str
    ride_id: str
