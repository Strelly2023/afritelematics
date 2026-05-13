from fastapi import APIRouter
from ecosystems.afriride.bootstrap import build_system
from ecosystems.afriride.core.application.command_handlers.ride_handler import RideHandler

router = APIRouter()

system = build_system()
ride_handler = RideHandler(system["store"])
ride_projection = system["ride_projection"]


# ----------------------------------------
# WRITE SIDE
# ----------------------------------------

@router.post("/ride/request")
def request_ride(cmd: dict):
    return ride_handler.request(cmd)


@router.post("/ride/accept")
def accept_driver(cmd: dict):
    return ride_handler.accept_driver(cmd)


@router.post("/ride/assign")
def assign_driver(cmd: dict):
    return ride_handler.assign_driver(cmd)


@router.post("/ride/start")
def start_trip(cmd: dict):
    return ride_handler.start_trip(cmd)


@router.post("/ride/complete")
def complete_trip(cmd: dict):
    return ride_handler.complete_trip(cmd)


@router.post("/ride/cancel")
def cancel_trip(cmd: dict):
    return ride_handler.cancel_trip(cmd)


# ----------------------------------------
# READ SIDE
# ----------------------------------------

@router.get("/ride/{ride_id}")
def get_ride(ride_id: str):
    return ride_projection.get(ride_id)
