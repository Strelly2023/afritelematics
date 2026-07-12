from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novacodepro import NovaCodeProPlatform, get_novacodepro_platform
from afritech.novacodepro.workspace import (
    build_tool_manifest,
    build_workspace_manifest,
    render_tool_html,
    render_workspace_html,
)


def _service() -> NovaCodeProPlatform:
    db_path = Path(__file__).resolve().parents[2] / "var/novacodepro-platform.sqlite3"
    return get_novacodepro_platform(db_path)


def build_novacodepro_workspace_router(platform: NovaCodeProPlatform | None = None) -> APIRouter:
    service = platform or _service()
    router = APIRouter(tags=["novacodepro-workspace"])
    observer = require_roles(
        "OPERATOR",
        "ADMIN",
        "VERIFIER",
        "OBSERVER",
        "DEVELOPER",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "UI_UX_DESIGNER",
        "PROJECT_MANAGER",
        "CLIENT",
        "PARTNER",
        "CUSTOMER",
    )
    editor = require_roles(
        "OPERATOR",
        "ADMIN",
        "VERIFIER",
        "DEVELOPER",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "UI_UX_DESIGNER",
        "PROJECT_MANAGER",
    )

    def _workspace_manifest(
        claims: JWTClaims,
        *,
        environment: str | None = None,
    ) -> dict[str, Any]:
        return build_workspace_manifest(
            service,
            user_id=claims.sub,
            role=claims.role,
            organization_id=claims.organization_id,
            environment=environment,
        )

    def _tool_manifest(
        claims: JWTClaims,
        tool_id: str,
        *,
        environment: str | None = None,
    ) -> dict[str, Any]:
        return build_tool_manifest(
            service,
            user_id=claims.sub,
            role=claims.role,
            organization_id=claims.organization_id,
            tool_id=tool_id,
            environment=environment,
        )

    @router.get("/novacodepro/", include_in_schema=False)
    def novacodepro_root(claims: JWTClaims = Depends(observer)) -> RedirectResponse:
        manifest = _workspace_manifest(claims)
        return RedirectResponse(manifest["workspace"]["home_route"], status_code=307)

    @router.get("/novacodepro/workspace", include_in_schema=False)
    def novacodepro_workspace_index(claims: JWTClaims = Depends(observer)) -> RedirectResponse:
        manifest = _workspace_manifest(claims)
        return RedirectResponse(manifest["workspace"]["home_route"], status_code=307)

    @router.get("/novacodepro/workspace/{workspace_slug}", response_class=HTMLResponse)
    def novacodepro_workspace_home(
        workspace_slug: str,
        environment: str | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> str:
        manifest = _workspace_manifest(claims, environment=environment)
        if workspace_slug != manifest["workspace"]["slug"]:
            raise HTTPException(status_code=404, detail="workspace_not_found")
        return render_workspace_html(manifest)

    @router.get("/novacodepro/tools/{tool_id}", response_class=HTMLResponse)
    def novacodepro_tool_window(
        tool_id: str,
        environment: str | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> str:
        try:
            manifest = _tool_manifest(claims, tool_id, environment=environment)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="tool_not_found") from exc
        return render_tool_html(manifest)

    @router.get("/v1/novacodepro/me")
    def me(claims: JWTClaims = Depends(observer)) -> dict[str, Any]:
        return _workspace_manifest(claims)["user"]

    @router.get("/v1/novacodepro/me/workspace")
    def me_workspace(
        environment: str | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        return _workspace_manifest(claims, environment=environment)["workspace"]

    @router.get("/v1/novacodepro/me/navigation")
    def me_navigation(
        environment: str | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> list[dict[str, Any]]:
        return _workspace_manifest(claims, environment=environment)["workspace"]["navigation"]

    @router.get("/v1/novacodepro/me/tools")
    def me_tools(
        environment: str | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> list[dict[str, Any]]:
        return _workspace_manifest(claims, environment=environment)["workspace"]["tools"]

    @router.get("/v1/novacodepro/me/commands")
    def me_commands(
        environment: str | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> list[dict[str, Any]]:
        return _workspace_manifest(claims, environment=environment)["workspace"]["command_palette"]

    @router.get("/v1/novacodepro/tools")
    def tools(
        environment: str | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> list[dict[str, Any]]:
        return _workspace_manifest(claims, environment=environment)["workspace"]["tools"]

    @router.get("/v1/novacodepro/tools/{tool_id}")
    def tool(
        tool_id: str,
        environment: str | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        try:
            return _tool_manifest(claims, tool_id, environment=environment)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="tool_not_found") from exc

    @router.get("/v1/novacodepro/tools/{tool_id}/manifest")
    def tool_manifest(
        tool_id: str,
        environment: str | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        try:
            return _tool_manifest(claims, tool_id, environment=environment)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="tool_not_found") from exc

    @router.get("/v1/novacodepro/workspace")
    def workspace_manifest(
        environment: str | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> dict[str, Any]:
        return _workspace_manifest(claims, environment=environment)

    @router.get("/v1/novacodepro/workspace/navigation")
    def workspace_navigation(
        environment: str | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> list[dict[str, Any]]:
        return _workspace_manifest(claims, environment=environment)["workspace"]["navigation"]

    @router.get("/v1/novacodepro/workspace/commands")
    def workspace_commands(
        environment: str | None = None,
        claims: JWTClaims = Depends(observer),
    ) -> list[dict[str, Any]]:
        return _workspace_manifest(claims, environment=environment)["workspace"]["command_palette"]

    @router.post("/v1/novacodepro/commands/execute")
    def execute_command(payload: dict[str, Any], claims: JWTClaims = Depends(editor)) -> dict[str, Any]:
        workspace_manifest = _workspace_manifest(claims)
        command = str(payload.get("command") or "").strip()
        allowed_commands = {item["label"]: item for item in workspace_manifest["workspace"]["command_palette"]}
        if command not in allowed_commands:
            raise HTTPException(status_code=404, detail="command_not_found")
        command_item = allowed_commands[command]
        return {
            "command": command,
            "status": "queued",
            "route": command_item.get("route"),
            "requires_confirmation": command_item.get("requires_confirmation", False),
            "audit": {
                "actor": claims.sub,
                "organization_id": claims.organization_id,
                "timestamp": workspace_manifest["workspace"]["audit"]["last_updated"],
            },
        }

    return router


__all__ = ["build_novacodepro_workspace_router"]
