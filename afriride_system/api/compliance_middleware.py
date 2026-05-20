"""Metadata-only invariant compliance middleware."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response


INVARIANT_CONTRACT = "five-invariant-contract"
ENFORCEMENT_MODE = "metadata-only"


async def compliance_metadata_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request.state.invariant_contract = INVARIANT_CONTRACT
    request.state.enforcement_mode = ENFORCEMENT_MODE

    response = await call_next(request)
    response.headers["X-AfriRide-Invariant-Contract"] = INVARIANT_CONTRACT
    response.headers["X-AfriRide-Enforcement-Mode"] = ENFORCEMENT_MODE
    return response
