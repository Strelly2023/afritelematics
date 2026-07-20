"""Production-like NovaID ASGI application with managed local lifecycle."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from afritech.api.novaid_audit_replay_api import build_novaid_audit_replay_router

from .runtime import build_default_durable_router

router = build_default_durable_router()


@asynccontextmanager
async def lifespan(app: FastAPI):
    publisher = getattr(router, "novaid_revocation_publisher", None)
    consumer = getattr(router, "novaid_revocation_consumer", None)
    webauthn_publisher = getattr(router, "novaid_webauthn_publisher", None)
    webauthn_consumer = getattr(router, "novaid_webauthn_consumer", None)
    if publisher:
        publisher.start()
    if consumer:
        consumer.start()
    if webauthn_publisher:
        webauthn_publisher.start()
    if webauthn_consumer:
        webauthn_consumer.start()
    app.state.novaid_ready = True
    try:
        yield
    finally:
        app.state.novaid_ready = False
        if publisher:
            publisher.shutdown()
        if consumer:
            consumer.shutdown()
        if webauthn_publisher:
            webauthn_publisher.shutdown()
        if webauthn_consumer:
            webauthn_consumer.shutdown()
        redis_client = getattr(router, "novaid_redis_client", None)
        if redis_client:
            redis_client.close()
        pool = getattr(router, "novaid_postgres_pool", None)
        if pool:
            pool.close()


app = FastAPI(title="NovaID Runtime", lifespan=lifespan)
app.include_router(router)
app.include_router(build_novaid_audit_replay_router())


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready")
def readiness() -> dict[str, str]:
    if not getattr(app.state, "novaid_ready", False):
        raise HTTPException(status_code=503, detail="not_ready")
    pool = getattr(router, "novaid_postgres_pool", None)
    if pool and not pool.check():
        raise HTTPException(status_code=503, detail="postgres_unavailable")
    redis_client = getattr(router, "novaid_redis_client", None)
    if redis_client:
        try:
            redis_client.ping()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="redis_unavailable") from exc
    return {"status": "ready"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    return router.novaid_metrics.prometheus()
