"""AfriRide FastAPI entry point."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from afriride_system.api.driver_routes import router as driver_router
from afriride_system.api.passenger_routes import router as passenger_router
from afriride_system.api.compliance_middleware import compliance_metadata_middleware
from afriride_system.api.responses import error

app = FastAPI(title="AfriRide API")
app.middleware("http")(compliance_metadata_middleware)

app.include_router(passenger_router, prefix="/passenger", tags=["passenger"])
app.include_router(driver_router, prefix="/driver", tags=["driver"])


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
