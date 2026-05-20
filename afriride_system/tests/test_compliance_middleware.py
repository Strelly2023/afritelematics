from __future__ import annotations

import asyncio

from fastapi import Request, Response

from afriride_system.api.compliance_middleware import (
    ENFORCEMENT_MODE,
    INVARIANT_CONTRACT,
    compliance_metadata_middleware,
)


def test_compliance_middleware_adds_metadata_only() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
        }
    )

    async def call_next(received: Request) -> Response:
        assert received.state.invariant_contract == INVARIANT_CONTRACT
        assert received.state.enforcement_mode == ENFORCEMENT_MODE
        return Response()

    response = asyncio.run(
        compliance_metadata_middleware(request, call_next)
    )

    assert response.headers["X-AfriRide-Invariant-Contract"] == INVARIANT_CONTRACT
    assert response.headers["X-AfriRide-Enforcement-Mode"] == ENFORCEMENT_MODE
