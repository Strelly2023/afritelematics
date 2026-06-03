"""AfriRide FastAPI entry point."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from afriride_system.api.driver_routes import router as driver_router
from afriride_system.api.passenger_routes import router as passenger_router
from afriride_system.api.ride_routes import router as ride_router
from afriride_system.api.compliance_middleware import compliance_metadata_middleware
from afriride_system.api.trace_middleware import trace_enforcement_middleware
from afriride_system.api.dispatcher_adapter import get_gateway
from afriride_system.api.responses import error
from afriride_system.backend.trace_enforcement import TRACE_LOG
from afritech.api.ingestion.event_ingestion import EventIngestionAPI, build_router

app = FastAPI(title="AfriRide API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://afriride-api.onrender.com",
    ],
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(compliance_metadata_middleware)
app.middleware("http")(trace_enforcement_middleware)

app.include_router(passenger_router, prefix="/passenger", tags=["passenger"])
app.include_router(driver_router, prefix="/driver", tags=["driver"])
app.include_router(ride_router, prefix="/ride", tags=["ride"])
app.include_router(build_router(EventIngestionAPI(secret="pilot-secret")))


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "afriride-api",
    }


@app.websocket("/ws/{ride_id}")
async def ride_tracking_socket(websocket: WebSocket, ride_id: str) -> None:
    await websocket.accept()
    await websocket.send_json(
        {
            "ride_id": ride_id,
            "status": "connected",
            "mode": "observation_only",
        }
    )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return


@app.get("/rides/active")
def active_rides() -> dict:
    gateway = get_gateway()
    rides = [
        {
            "ride_id": ride.ride_id,
            "state": ride.status,
            "driver_id": ride.assigned_driver,
            "rider_id": ride.passenger_id,
        }
        for ride in gateway.dispatcher.rides.values()
        if ride.status != "COMPLETED"
    ]
    return {"rides": rides}


@app.get("/system/replay/health")
def replay_health() -> dict:
    summary = TRACE_LOG.integrity_summary()
    return {
        "replay_success_rate": summary["replay_success_rate"],
        "failures": summary["replay_failures"],
        "last_failed_ride_id": summary["last_failed_ride_id"],
        "status": "PASS" if summary["replay_failures"] == 0 else "FAIL",
    }


@app.get("/system/evidence")
def evidence_pipeline() -> dict:
    summary = TRACE_LOG.integrity_summary()
    return {
        "receipts_count": summary["valid_traces"],
        "trace_count": summary["trace_count"],
        "missing_traces": summary["missing_events"],
        "total_rides": summary["total_rides"],
        "valid_traces": summary["valid_traces"],
        "invalid_traces": summary["invalid_traces"],
    }


@app.get("/system/guards")
def guard_violations() -> dict:
    summary = TRACE_LOG.integrity_summary()
    violations = []
    if summary["missing_events"]:
        violations.append(
            {
                "type": "TRACE_COMPLETENESS",
                "severity": "CRITICAL",
                "timestamp": "runtime",
                "details": {"missing_events": summary["missing_events"]},
            }
        )
    if summary["replay_failures"]:
        violations.append(
            {
                "type": "REPLAY_DIVERGENCE",
                "severity": "CRITICAL",
                "timestamp": "runtime",
                "details": {"failures": summary["replay_failures"]},
            }
        )
    return {"violations": violations}


@app.get("/system/traces/{ride_id}")
def trace_integrity(ride_id: str) -> dict:
    return TRACE_LOG.validate_ride(ride_id).canonical_dict()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error(
            code=str(exc.detail).upper(),
            message=str(exc.detail),
        ),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error(
            code="SERVER_ERROR",
            message=str(exc),
        ),
    )
