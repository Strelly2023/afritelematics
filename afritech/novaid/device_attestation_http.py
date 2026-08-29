"""HTTP transport for the canonical NovaID device-attestation authority."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Header, HTTPException

from .application.device_attestation import (
    AttestationContext,
    DeviceAttestationAuthority,
    DeviceAttestationError,
)


def build_device_attestation_router(
    authority: DeviceAttestationAuthority,
    *,
    authenticate: Callable[[str, str], dict[str, object]],
    activate: Callable[[Any, dict[str, object]], dict[str, str]],
) -> APIRouter:
    router = APIRouter(prefix="/v1/device-attestation", tags=["novaid-device-attestation"])

    def context(
        payload: dict[str, Any], authorization: str, tenant_id: str,
        request_id: str, correlation_id: str,
    ) -> AttestationContext:
        try:
            claims = authenticate(authorization, tenant_id)
        except Exception as exc:
            raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED"}) from exc
        subject_id = str(claims.get("sub", ""))
        if not subject_id or str(claims.get("tenant_id", "")) != tenant_id:
            raise HTTPException(status_code=403, detail={"code": "TENANT_ACCESS_DENIED"})
        if str(payload.get("device_id", "")) != str(claims.get("device_id", "")):
            raise HTTPException(status_code=403, detail={"code": "DEVICE_ACCESS_DENIED"})
        return AttestationContext(
            tenant_id=tenant_id, subject_id=subject_id,
            device_id=str(payload.get("device_id", "")),
            provider=str(payload.get("provider") or payload.get("platform", "")),
            request_id=request_id, correlation_id=correlation_id,
        )

    @router.post("/challenge")
    def challenge(
        payload: dict[str, Any], authorization: str = Header(),
        x_tenant_id: str = Header(), x_request_id: str = Header(),
        x_correlation_id: str = Header(),
    ) -> dict[str, Any]:
        try:
            result = authority.create_challenge(
                context(payload, authorization, x_tenant_id, x_request_id, x_correlation_id)
            )
        except DeviceAttestationError as exc:
            raise HTTPException(status_code=400, detail={"code": str(exc)}) from exc
        return {
            "challenge_id": result.challenge_id, "nonce": result.nonce,
            "provider": result.provider, "expires_at": result.expires_at.isoformat(),
            "cloud_project_number": result.cloud_project_number,
        }

    @router.post("/verify")
    def verify(
        payload: dict[str, Any], authorization: str = Header(),
        x_tenant_id: str = Header(), x_request_id: str = Header(),
        x_correlation_id: str = Header(),
    ) -> dict[str, Any]:
        try:
            result = authority.verify(
                context(payload, authorization, x_tenant_id, x_request_id, x_correlation_id),
                challenge_id=str(payload.get("challenge_id", "")),
                nonce=str(payload.get("nonce", "")), token=str(payload.get("token", "")),
            )
        except DeviceAttestationError as exc:
            code = str(exc)
            status = 503 if code in {"attestation_verifier_not_configured", "attestation_verifier_unavailable"} else 401
            raise HTTPException(status_code=status, detail={"code": code}) from exc
        activated = activate(result, authenticate(authorization, x_tenant_id))
        return {
            "trusted": True, "tenant_id": result.tenant_id,
            "subject_id": result.subject_id, "device_id": result.device_id,
            "provider": result.provider, "verdicts": list(result.verdicts),
            "verified_at": result.verified_at.isoformat(),
            "correlation_id": result.correlation_id,
            **activated,
        }

    return router
