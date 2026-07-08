"""NovaRide FastAPI entry point with AfriRide compatibility paths."""

from __future__ import annotations
import asyncio
import json
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
from afriride_system.api.operations_routes import router as operations_router
from afriride_system.api.payment_routes import router as payment_router
from afriride_system.api.global_routes import router as global_router
from afriride_system.api.corridors_routes import router as corridors_router
from afriride_system.api.architecture_routes import router as architecture_router
from afriride_system.api.internal_qa_contract_routes import router as internal_qa_contract_router
from afriride_system.api.trace_middleware import trace_enforcement_middleware
from afriride_system.api.responses import error
from afriride_system.api.security import build_security_router, security_middleware
from afriride_system.observability.enterprise import api_metrics_middleware
from afriride_system.api.treasury_routes import router as treasury_router
from afriride_system.integration.websocket_gateway.mobility_hub import mobility_hub
from afritech.api.ingestion.event_ingestion import EventIngestionAPI, build_router
from afritech.api.afriride_next_gen_mobile_api import build_afriride_next_gen_mobile_router

app = FastAPI(title="NovaRide API")
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
app.middleware("http")(api_metrics_middleware)
app.middleware("http")(security_middleware)

app.include_router(build_auth_router())
app.include_router(build_auth_router(), prefix="/v1")
app.include_router(passenger_router, prefix="/passenger", tags=["passenger"])
app.include_router(driver_router, prefix="/driver", tags=["driver"])
app.include_router(ride_router, prefix="/ride", tags=["ride"])
app.include_router(system_router)
app.include_router(operations_router)
app.include_router(payment_router)
app.include_router(global_router)
app.include_router(corridors_router)
app.include_router(architecture_router)
app.include_router(internal_qa_contract_router)
app.include_router(treasury_router)
app.include_router(build_security_router())
app.include_router(build_afriride_next_gen_mobile_router())
_AFRIRIDE_EVENT_SECRET = os.environ.get("AFRIRIDE_EVENT_INGESTION_SECRET", secrets.token_urlsafe(32))
app.include_router(build_router(EventIngestionAPI(secret=_AFRIRIDE_EVENT_SECRET)))


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "novaride-api",
        "legacy_service": "afriride-api",
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


@app.websocket("/ws/mobility/{actor_id}")
async def mobility_socket(websocket: WebSocket, actor_id: str) -> None:
    """Authenticated replayable mobility stream with application heartbeats."""
    token = websocket.query_params.get("token", "")
    try:
        claims = JWT.verify_token(token)
    except ValueError:
        await websocket.close(code=1008)
        return
    privileged = claims.role in {"ADMIN", "OPERATOR", "DISPATCHER"}
    if claims.sub != actor_id and not privileged:
        await websocket.close(code=1008)
        return

    ride_id = websocket.query_params.get("ride_id")
    cursor = websocket.query_params.get("cursor", "0")
    if not cursor.replace("-", "").isdigit():
        await websocket.close(code=1003)
        return
    targets = {f"actor:{actor_id}", f"role:{claims.role.lower()}"}
    if ride_id:
        targets.add(f"ride:{ride_id}")

    await websocket.accept()
    presence = mobility_hub.heartbeat(actor_id)
    await websocket.send_json(
        {
            "contract": "afriride.mobility.v1",
            "type": "SESSION_READY",
            "sequence": int(cursor) if cursor.isdigit() else None,
            "stream_id": cursor if "-" in cursor else None,
            "authority": "server_projection",
            "data": {
                "actor_id": actor_id,
                "role": claims.role,
                "ride_id": ride_id,
                "presence": presence,
                "heartbeat_interval_seconds": 15,
            },
        }
    )
    for event in mobility_hub.events_after(cursor, targets):
        await websocket.send_json(event)
        cursor = str(event.get("stream_id") or event.get("sequence") or cursor)

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=5)
                message = json.loads(raw)
                if message.get("type") == "HEARTBEAT":
                    presence = mobility_hub.heartbeat(actor_id)
                    await websocket.send_json(
                        {
                            "contract": "afriride.mobility.v1",
                            "type": "HEARTBEAT_ACK",
                            "sequence": int(cursor) if cursor.isdigit() else None,
                            "stream_id": cursor if "-" in cursor else None,
                            "authority": "server_projection",
                            "data": presence,
                        }
                    )
                elif message.get("type") == "RESUME":
                    requested = str(message.get("cursor", cursor))
                    if requested.replace("-", "").isdigit():
                        cursor = requested
            except TimeoutError:
                pass

            for event in mobility_hub.events_after(cursor, targets):
                await websocket.send_json(event)
                cursor = str(event.get("stream_id") or event.get("sequence") or cursor)
    except (WebSocketDisconnect, json.JSONDecodeError, ValueError):
        mobility_hub.disconnect(actor_id)


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
