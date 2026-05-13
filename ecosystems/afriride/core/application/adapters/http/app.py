from fastapi import FastAPI
from ecosystems.afriride.bootstrap import build_system
from ecosystems.afriride.core.application.command_handlers.ride_handler import RideHandler

system = build_system()
store = system["store"]

ride_handler = RideHandler(store)

app = FastAPI(title="AfriRide API")


# Register routes
@app.get("/")
def health():
    return {"status": "ok"}
