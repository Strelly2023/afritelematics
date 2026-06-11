"""AfriRide FastAPI entry point."""

from __future__ import annotations
import os
import secrets

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from afriride_system.api.auth import JWT, auth_middleware, build_auth_router
from afriride_system.api.compliance_middleware import compliance_metadata_middleware
from afriride_system.api.driver_routes import router as driver_router
from afriride_system.api.passenger_routes import router as passenger_router
from afriride_system.api.ride_routes import router as ride_router
from afriride_system.api.system_routes import router as system_router
from afriride_system.api.trace_middleware import trace_enforcement_middleware
from afriride_system.api.responses import error
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
app.middleware("http")(auth_middleware)

app.include_router(build_auth_router())
app.include_router(passenger_router, prefix="/passenger", tags=["passenger"])
app.include_router(driver_router, prefix="/driver", tags=["driver"])
app.include_router(ride_router, prefix="/ride", tags=["ride"])
app.include_router(system_router)
_AFRIRIDE_EVENT_SECRET = os.environ.get("AFRIRIDE_EVENT_INGESTION_SECRET", secrets.token_urlsafe(32))
app.include_router(build_router(EventIngestionAPI(secret=_AFRIRIDE_EVENT_SECRET)))


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
    token = websocket.query_params.get("token")
    if token is None:
        authorization = websocket.headers.get("authorization", "")
        if authorization.startswith("Bearer "):
            token = authorization[len("Bearer ") :]
    if not token:
        await websocket.close(code=1008)
        return
    try:
        claims = JWT.verify_token(token)
    except ValueError:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await websocket.send_json(
        {
            "ride_id": ride_id,
            "status": "connected",
            "mode": "observation_only",
            "subscriber": claims.sub,
            "role": claims.role,
        }
    )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return


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
            message="internal server error",
        ),
    )
