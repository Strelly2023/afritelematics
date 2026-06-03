from fastapi import FastAPI
from ecosystems.afriride.bootstrap import build_system
from ecosystems.afriride.core.application.command_handlers.ride_handler import RideHandler
from ecosystems.afriride.core.application.adapters.http.proof_api import router as proof_router

system = build_system()
store = system["store"]

ride_handler = RideHandler(store)

app = FastAPI(title="AfriRide API")
app.include_router(proof_router)


# Register routes
@app.get("/")
def health():
    return {"status": "ok"}
