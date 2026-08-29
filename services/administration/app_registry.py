from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Iterable


@dataclass(frozen=True)
class AppRegistryItem:
    id: str
    name: str
    route: str
    icon: str
    requiredPermissions: tuple[str, ...]
    featureFlag: str
    status: str
    domain: str
    description: str
    order: int

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "route": self.route,
            "icon": self.icon,
            "requiredPermissions": list(self.requiredPermissions),
            "featureFlag": self.featureFlag,
            "status": self.status,
            "domain": self.domain,
            "description": self.description,
            "order": self.order,
        }


def load_app_registry_document() -> dict[str, Any]:
    resource = files("contracts").joinpath("app-registry.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def list_app_registry() -> list[AppRegistryItem]:
    document = load_app_registry_document()
    apps = []
    for item in document.get("apps", []):
        apps.append(
            AppRegistryItem(
                id=str(item.get("id", "")),
                name=str(item.get("name", "")),
                route=str(item.get("route", "")),
                icon=str(item.get("icon", "")),
                requiredPermissions=tuple(str(permission) for permission in item.get("requiredPermissions", [])),
                featureFlag=str(item.get("featureFlag", "")),
                status=str(item.get("status", "preview")),
                domain=str(item.get("domain", "shared")),
                description=str(item.get("description", "")),
                order=int(item.get("order", 0)),
            )
        )
    return sorted(apps, key=lambda item: item.order)


def build_app_registry_manifest(*, permissions: Iterable[str] = (), environment: str = "development") -> dict[str, Any]:
    allowed = {str(permission) for permission in permissions}
    apps = []
    for item in list_app_registry():
        canonical = item.canonical_dict()
        canonical["accessible"] = canonical["status"] != "disabled" and (
            not canonical["requiredPermissions"]
            or all(permission in allowed for permission in canonical["requiredPermissions"])
        )
        apps.append(canonical)
    document = load_app_registry_document()
    return {
        "contractVersion": document.get("contractVersion", 1),
        "platform": document.get("platform", "NovaCodePro"),
        "environment": environment,
        "apps": apps,
        "launcher": {
            "count": len(apps),
            "active": sum(1 for item in apps if item["status"] == "active"),
            "preview": sum(1 for item in apps if item["status"] == "preview"),
        },
    }


__all__ = ["AppRegistryItem", "build_app_registry_manifest", "list_app_registry", "load_app_registry_document"]
