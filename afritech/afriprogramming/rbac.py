from __future__ import annotations

from collections import Counter
from typing import Any


DEFAULT_ORGANIZATION_ID = "afritech-core"

CORE_ROLE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "CUSTOMER": {
        "label": "Customer",
        "category": "core",
        "mission": "Request rides, track trips, pay, and verify outcomes.",
        "aliases": ("RIDER", "PASSENGER"),
        "permissions": (
            "ride.request",
            "ride.track",
            "ride.cancel",
            "ride.history",
            "payment.pay",
            "receipt.view",
            "proof.view",
            "replay.view",
        ),
        "visible_panels": (
            "Request Ride",
            "Trip Tracker",
            "Payment",
            "Receipt",
            "Verify Ride",
            "Ride History",
        ),
        "api_surfaces": (
            "/v1/rider/rides",
            "/v1/rider/rides/{ride_id}",
            "/v1/rider/rides/{ride_id}/receipt",
            "/v1/rider/rides/{ride_id}/replay",
            "/v1/rider/rides/history",
            "/public/trust/{receipt_id}",
        ),
        "dashboard_surface": "/v1/afriride/rbac/dashboard/customer",
    },
    "DRIVER": {
        "label": "Driver",
        "category": "core",
        "mission": "Execute rides, manage availability, and earn verified income.",
        "aliases": (),
        "permissions": (
            "driver.go_online",
            "driver.go_offline",
            "driver.view.own",
            "ride.accept",
            "ride.arrive",
            "ride.start",
            "ride.complete",
            "earnings.view",
            "replay.view",
        ),
        "visible_panels": (
            "Availability",
            "Ride Queue",
            "Trip Lifecycle",
            "Earnings",
            "Replay History",
        ),
        "api_surfaces": (
            "/v1/driver/{driver_id}/availability",
            "/v1/driver/{driver_id}/ride-queue",
            "/v1/driver/rides/{ride_id}/accept",
            "/v1/driver/rides/{ride_id}/arrive",
            "/v1/driver/rides/{ride_id}/start",
            "/v1/driver/rides/{ride_id}/complete",
            "/v1/driver/{driver_id}/earnings",
            "/v1/driver/{driver_id}/replay-history",
        ),
        "dashboard_surface": "/v1/afriride/rbac/dashboard/driver",
    },
    "DISPATCHER": {
        "label": "Dispatcher",
        "category": "core",
        "mission": "Monitor operational flow and manage ride allocation.",
        "aliases": ("DISPATCH",),
        "permissions": (
            "dispatch.view",
            "dispatch.assign",
            "dispatch.reassign",
            "dispatch.override",
            "ride.monitor",
            "incident.resolve",
        ),
        "visible_panels": (
            "Dispatch Overview",
            "Ride Queue",
            "Driver Availability",
            "Incident Console",
            "Operational Overrides",
        ),
        "api_surfaces": (
            "/v1/afriride/dispatch/overview",
            "/v1/afriride/dispatch/rides",
            "/v1/afriride/dispatch/assign",
            "/v1/afriride/dispatch/reassign",
            "/v1/afriride/dispatch/incidents",
        ),
        "dashboard_surface": "/v1/afriride/rbac/dashboard/dispatcher",
    },
    "FLEET_OWNER": {
        "label": "Fleet Owner",
        "category": "core",
        "mission": "Manage drivers, vehicles, performance, and fleet revenue.",
        "aliases": ("FLEET OWNER", "FLEET-OWNER", "FLEETOWNER"),
        "permissions": (
            "fleet.view",
            "fleet.manage_drivers",
            "fleet.manage_vehicles",
            "fleet.view_earnings",
            "fleet.view_performance",
            "trust.view",
            "billing.preview",
        ),
        "visible_panels": (
            "Fleet Summary",
            "Driver Management",
            "Vehicle Registry",
            "Revenue",
            "Trust Health",
        ),
        "api_surfaces": (
            "/v1/afriride/fleet/summary",
            "/v1/afriride/fleet/drivers",
            "/v1/afriride/fleet/vehicles",
            "/v1/afriride/fleet/earnings",
            "/v1/afriride/fleet/trust",
        ),
        "dashboard_surface": "/v1/afriride/rbac/dashboard/fleet_owner",
    },
    "ADMIN": {
        "label": "Administrator",
        "category": "core",
        "mission": "Govern roles, compliance, trust, and platform policy.",
        "aliases": ("SYSTEM_ADMIN", "SYSTEM ADMIN", "PLATFORM_ADMIN"),
        "permissions": (
            "rbac.manage",
            "policy.manage",
            "compliance.view",
            "trust.view",
            "audit.view",
            "certification.issue",
            "verification.view",
        ),
        "visible_panels": (
            "Governance",
            "RBAC",
            "Audit",
            "Compliance",
            "Certification",
            "Trust Registry",
        ),
        "api_surfaces": (
            "/v1/afriride/rbac/catalog",
            "/v1/afriride/rbac/assignments",
            "/v1/afriride/rbac/check",
            "/v1/novatech/documentation/certification/issue",
            "/v1/novatech/documentation/status",
            "/v1/novatech/intranet/platform",
        ),
        "dashboard_surface": "/v1/afriride/rbac/dashboard/admin",
    },
    "PRODUCT_MANAGER": {
        "label": "Product Manager",
        "category": "core",
        "mission": "Define product direction, prioritize work, and coordinate release readiness.",
        "aliases": ("PM", "PRODUCT OWNER"),
        "permissions": (
            "product.read",
            "product.create",
            "product.update",
            "roadmap.read",
            "roadmap.create",
            "roadmap.update",
            "requirements.read",
            "requirements.create",
            "requirements.update",
            "backlog.read",
            "backlog.prioritize",
            "insight.create",
            "analytics.read_aggregated",
            "release.read",
            "release.scope_propose",
            "documentation.read",
            "documentation.write",
        ),
        "visible_panels": (
            "Product Portfolio",
            "Roadmap",
            "Requirements",
            "Customer Signals",
            "Release Readiness",
        ),
        "api_surfaces": (
            "/v1/novacodepro/workspace",
            "/v1/novacodepro/tools",
            "/v1/novacodepro/me/commands",
        ),
        "dashboard_surface": "/v1/novacodepro/workspace/product",
    },
    "BUSINESS_ANALYST": {
        "label": "Business Analyst",
        "category": "core",
        "mission": "Translate business needs into clear, testable, and traceable requirements.",
        "aliases": ("BA", "BUSINESS ANALYST"),
        "permissions": (
            "requirements.read",
            "requirements.create",
            "requirements.update",
            "process.read",
            "process.model",
            "businessrules.create",
            "stakeholder.manage",
            "backlog.create",
            "analytics.read",
            "documentation.write",
            "report.generate",
            "traceability.manage",
            "change.request",
            "risk.review",
        ),
        "visible_panels": (
            "Requirements Management",
            "Process Modeling",
            "Stakeholders",
            "Business Rules",
            "Traceability",
            "Reporting",
        ),
        "api_surfaces": (
            "/v1/novacodepro/workspace/business-analyst",
            "/v1/novacodepro/tools",
            "/v1/novacodepro/me/commands",
        ),
        "dashboard_surface": "/v1/novacodepro/workspace/business-analyst",
    },
    "UI_UX_DESIGNER": {
        "label": "UI/UX Designer",
        "category": "core",
        "mission": "Shape accessible, consistent, and user-centered product experiences.",
        "aliases": ("DESIGNER", "UI DESIGNER", "UX DESIGNER"),
        "permissions": (
            "design.read",
            "design.create",
            "design.update",
            "wireframe.create",
            "prototype.create",
            "component.read",
            "component.publish",
            "designsystem.read",
            "designsystem.update",
            "research.read",
            "research.create",
            "accessibility.review",
            "asset.upload",
            "asset.manage",
            "handoff.generate",
            "documentation.write",
            "design.review",
            "analytics.read",
        ),
        "visible_panels": (
            "Design Workspace",
            "Wireframes",
            "Components",
            "Accessibility",
            "Research",
            "Handoff",
        ),
        "api_surfaces": (
            "/v1/novacodepro/workspace/design",
            "/v1/novacodepro/tools",
            "/v1/novacodepro/me/commands",
        ),
        "dashboard_surface": "/v1/novacodepro/workspace/design",
    },
    "PROJECT_MANAGER": {
        "label": "Project Manager",
        "category": "core",
        "mission": "Plan, coordinate, and deliver projects within scope, schedule, budget, and governance.",
        "aliases": ("PM", "PROJECT LEAD"),
        "permissions": (
            "project.read",
            "project.create",
            "project.update",
            "portfolio.read",
            "portfolio.manage",
            "schedule.create",
            "schedule.update",
            "resource.assign",
            "budget.read",
            "budget.manage_assigned",
            "risk.create",
            "risk.manage",
            "change.request",
            "change.review",
            "stakeholder.manage",
            "report.generate",
            "documentation.write",
            "governance.review",
            "milestone.manage",
        ),
        "visible_panels": (
            "Projects",
            "Planning",
            "Schedule",
            "RAID",
            "Governance",
            "Reporting",
        ),
        "api_surfaces": (
            "/v1/novacodepro/workspace/project-manager",
            "/v1/novacodepro/tools",
            "/v1/novacodepro/me/commands",
        ),
        "dashboard_surface": "/v1/novacodepro/workspace/project-manager",
    },
}

LEGACY_ROLE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "OPERATOR": {
        "label": "Operator",
        "category": "legacy",
        "mission": "Monitor operational state and governed dashboards.",
        "aliases": (),
        "permissions": (
            "read:metrics",
            "read:trust",
            "read:delivery",
            "read:replay",
            "read:verification",
        ),
        "visible_panels": ("Operations Dashboard", "Trust Metrics", "Replay", "Evidence"),
        "api_surfaces": (
            "/v1/operator/dashboard",
            "/v1/operator/analytics",
            "/v1/operator/decisions",
            "/v1/operator/actions",
            "/v1/operator/public-verification/status",
        ),
        "dashboard_surface": "/v1/novaprogramming/staff/operator/dashboard",
    },
    "CLIENT": {
        "label": "Client",
        "category": "external",
        "mission": "Access public trust, documentation, and verification portals.",
        "aliases": (),
        "permissions": ("read:public_trust", "read:verification", "read:documentation"),
        "visible_panels": ("Public Trust", "Verification Portal", "Documentation"),
        "api_surfaces": (
            "/public/trust/dashboard",
            "/public/verify/portal",
            "/public/documentation/portal",
        ),
        "dashboard_surface": "/public/trust/dashboard",
    },
    "SUPPLIER": {
        "label": "Supplier",
        "category": "external",
        "mission": "Access governed partner surfaces and supply-chain trust views.",
        "aliases": (),
        "permissions": ("read:partner", "read:trust", "read:documentation"),
        "visible_panels": ("Partner Surface", "Trust Network", "Documentation"),
        "api_surfaces": (
            "/public/partners/registry",
            "/public/trust/dashboard",
            "/public/documentation/portal",
        ),
        "dashboard_surface": "/public/partners/registry",
    },
    "INVESTOR": {
        "label": "Investor",
        "category": "external",
        "mission": "Review public trust posture, compliance posture, and ecosystem signals.",
        "aliases": (),
        "permissions": ("read:trust", "read:verification", "read:marketplace"),
        "visible_panels": ("Trust Overview", "Verification", "Marketplace"),
        "api_surfaces": (
            "/public/trust/dashboard",
            "/public/verify/portal",
            "/v1/novatech/marketplace/status",
        ),
        "dashboard_surface": "/public/trust/dashboard",
    },
    "VERIFIER": {
        "label": "Verifier",
        "category": "legacy",
        "mission": "Validate proof, trust, and certification surfaces.",
        "aliases": (),
        "permissions": ("read:verification", "write:certification", "read:proof"),
        "visible_panels": ("Verification", "Certification", "Trust", "Proof"),
        "api_surfaces": (
            "/v1/novatech/documentation/verification",
            "/v1/novatech/documentation/certification",
            "/public/verify/portal",
        ),
        "dashboard_surface": "/v1/novaprogramming/staff/verifier/dashboard",
    },
    "PARTNER": {
        "label": "Partner",
        "category": "legacy",
        "mission": "Consume the platform through governed integrations and trust exchange.",
        "aliases": (),
        "permissions": ("read:integration", "read:trust", "read:marketplace"),
        "visible_panels": ("Integrations", "Trust Network", "Marketplace"),
        "api_surfaces": ("/v1/novatech/marketplace/status", "/public/partners/registry"),
        "dashboard_surface": "/v1/novaprogramming/staff/partner/dashboard",
    },
    "DEVELOPER": {
        "label": "Developer",
        "category": "legacy",
        "mission": "Build and review governed platform services.",
        "aliases": (),
        "permissions": ("read:studio", "write:scaffold", "read:analysis"),
        "visible_panels": ("Studio", "Repo Intelligence", "Scaffold Output"),
        "api_surfaces": (
            "/v1/novaprogramming/studio/context/{project_id}",
            "/v1/novaprogramming/studio/analyze/{project_id}",
            "/v1/novaprogramming/studio/explain/{project_id}",
        ),
        "dashboard_surface": "/v1/novaprogramming/staff/developer/dashboard",
    },
    "OBSERVER": {
        "label": "Observer",
        "category": "legacy",
        "mission": "Read dashboards and audit evidence without authority.",
        "aliases": (),
        "permissions": ("read:metrics", "read:trust", "read:verification", "read:replay"),
        "visible_panels": ("Read-only Dashboards", "Trust", "Replay", "Evidence"),
        "api_surfaces": ("/v1/operator/dashboard", "/public/verify/portal"),
        "dashboard_surface": "/v1/novaprogramming/staff/observer/dashboard",
    },
    "DEVICE": {
        "label": "Device",
        "category": "legacy",
        "mission": "Bind a device identity to a trusted actor.",
        "aliases": (),
        "permissions": ("device.bind", "device.attest"),
        "visible_panels": ("Device Binding", "Attestation"),
        "api_surfaces": ("/v1/devices/register",),
        "dashboard_surface": "/v1/novaprogramming/staff/device/dashboard",
    },
}

CORE_ROLE_ORDER: tuple[str, ...] = tuple(CORE_ROLE_DEFINITIONS.keys())
LEGACY_ROLE_ORDER: tuple[str, ...] = tuple(LEGACY_ROLE_DEFINITIONS.keys())
AUTH_ROLE_ORDER: tuple[str, ...] = (*CORE_ROLE_ORDER, *LEGACY_ROLE_ORDER)

ROLE_HIERARCHY: dict[str, tuple[str, ...]] = {
    "ADMIN": (
        "FLEET_OWNER",
        "DISPATCHER",
        "DRIVER",
        "CUSTOMER",
        "OPERATOR",
        "VERIFIER",
        "OBSERVER",
        "PARTNER",
        "CLIENT",
        "SUPPLIER",
        "INVESTOR",
        "DEVELOPER",
        "DEVICE",
    ),
    "FLEET_OWNER": ("DRIVER", "CUSTOMER"),
    "DRIVER": ("CUSTOMER",),
    "DISPATCHER": ("CUSTOMER",),
    "OPERATOR": ("OBSERVER",),
    "VERIFIER": ("OBSERVER",),
}

ROLE_PERMISSION_GROUPS: dict[str, tuple[str, ...]] = {
    "CUSTOMER": (
        "ride.*",
        "payment.view.*",
        "receipt.view.*",
        "proof.view.*",
        "replay.view.*",
    ),
    "DRIVER": (
        "ride.*",
        "earnings.view.*",
        "payment.view.*",
        "receipt.view.*",
        "replay.view.*",
    ),
    "DISPATCHER": (
        "ride.view.*",
        "ride.assign",
        "ride.reassign",
        "ride.override",
        "incident.*",
        "driver.view.*",
        "customer.view.*",
    ),
    "FLEET_OWNER": (
        "fleet.*",
        "driver.view.*",
        "ride.view.*",
        "payment.view.*",
        "earnings.view.*",
        "trust.view",
        "billing.preview",
    ),
    "ADMIN": (
        "ride.*",
        "payment.*",
        "fleet.*",
        "rbac.*",
        "policy.*",
        "compliance.*",
        "trust.*",
        "audit.*",
        "documentation.*",
        "verification.view",
        "certification.*",
    ),
    "CLIENT": (
        "public.*",
        "verification.view",
        "documentation.view",
        "marketplace.view",
    ),
    "SUPPLIER": (
        "public.*",
        "verification.view",
        "documentation.view",
        "marketplace.view",
    ),
    "INVESTOR": (
        "public.*",
        "verification.view",
        "documentation.view",
        "marketplace.view",
    ),
    "OPERATOR": (
        "read:metrics",
        "read:trust",
        "read:delivery",
        "read:replay",
        "read:verification",
    ),
    "VERIFIER": (
        "read:verification",
        "write:certification",
        "read:proof",
    ),
    "PARTNER": (
        "read:integration",
        "read:trust",
        "read:marketplace",
    ),
    "DEVELOPER": (
        "read:studio",
        "write:scaffold",
        "read:analysis",
    ),
    "OBSERVER": (
        "read:metrics",
        "read:trust",
        "read:verification",
        "read:replay",
    ),
    "DEVICE": ("device.bind", "device.attest"),
}

ROLE_DENIES: dict[str, tuple[str, ...]] = {
    "CUSTOMER": (
        "ride.accept",
        "ride.arrive",
        "ride.start",
        "ride.complete",
        "ride.assign",
        "ride.reassign",
        "payment.capture.*",
        "payment.refund.*",
        "fleet.*",
        "rbac.*",
        "policy.*",
        "compliance.*",
    ),
    "DRIVER": (
        "ride.request",
        "ride.assign",
        "ride.reassign",
        "payment.capture.*",
        "payment.refund.*",
        "fleet.*",
        "rbac.*",
        "policy.*",
        "compliance.*",
    ),
    "DISPATCHER": (
        "ride.accept",
        "ride.arrive",
        "ride.start",
        "ride.complete",
        "payment.capture.*",
        "payment.refund.*",
        "fleet.*",
        "rbac.*",
    ),
    "FLEET_OWNER": (
        "ride.accept",
        "ride.arrive",
        "ride.start",
        "ride.complete",
        "rbac.*",
        "policy.*",
        "compliance.*",
        "payment.capture.*",
        "payment.refund.*",
    ),
    "CLIENT": ("ride.*", "payment.*", "fleet.*", "rbac.*", "policy.*", "compliance.*"),
    "SUPPLIER": ("ride.*", "payment.*", "fleet.*", "rbac.*", "policy.*", "compliance.*"),
    "INVESTOR": ("ride.*", "payment.*", "fleet.*", "rbac.*", "policy.*", "compliance.*"),
    "OPERATOR": ("ride.accept", "ride.arrive", "ride.start", "ride.complete", "payment.*", "fleet.*"),
    "VERIFIER": ("ride.accept", "ride.arrive", "ride.start", "ride.complete", "payment.*", "fleet.*"),
    "PARTNER": ("ride.accept", "ride.arrive", "ride.start", "ride.complete", "payment.*", "fleet.*"),
    "DEVELOPER": ("payment.*", "ride.accept", "ride.arrive", "ride.start", "ride.complete"),
    "OBSERVER": ("ride.*", "payment.*", "fleet.*", "rbac.*", "policy.*", "compliance.*"),
    "DEVICE": ("ride.*", "payment.*", "fleet.*", "rbac.*", "policy.*", "compliance.*"),
}

ROLE_PAYMENT_SCOPES: dict[str, tuple[str, ...]] = {
    "CUSTOMER": ("payments:write", "payments:read", "wallets:read", "events:read", "proofs:read"),
    "DRIVER": (
        "payments:write",
        "payments:read",
        "wallets:read",
        "payouts:read",
        "events:read",
        "monitoring:read",
    ),
    "DISPATCHER": ("payments:read", "events:read", "monitoring:read"),
    "FLEET_OWNER": (
        "payments:read",
        "wallets:read",
        "payouts:read",
        "treasury:read",
        "escrows:write",
        "events:read",
        "monitoring:read",
    ),
    "ADMIN": (
        "api_keys:write",
        "events:read",
        "escrows:write",
        "fx:read",
        "monitoring:read",
        "payments:read",
        "payments:write",
        "proofs:read",
        "proofs:write",
        "payouts:read",
        "payouts:write",
        "treasury:read",
        "treasury:write",
        "wallets:read",
        "wallets:write",
    ),
    "CLIENT": ("payments:read", "wallets:read", "events:read", "monitoring:read"),
    "SUPPLIER": ("payments:read", "wallets:read", "events:read", "monitoring:read"),
    "INVESTOR": ("payments:read", "wallets:read", "events:read", "monitoring:read"),
    "OPERATOR": ("payments:read", "events:read", "monitoring:read", "proofs:read"),
    "VERIFIER": ("payments:read", "events:read", "monitoring:read", "proofs:read"),
    "PARTNER": ("payments:read", "events:read", "monitoring:read"),
    "DEVELOPER": ("payments:read", "events:read", "monitoring:read"),
    "OBSERVER": ("payments:read", "events:read", "monitoring:read"),
    "DEVICE": (),
}


def _direct_hierarchy(role: str) -> tuple[str, ...]:
    canonical = canonical_role_name(role)
    return tuple(canonical_role_name(item) for item in ROLE_HIERARCHY.get(canonical, ()))


def _role_closure(role: str) -> tuple[str, ...]:
    canonical = canonical_role_name(role)
    seen: set[str] = {canonical}
    ordered: list[str] = []
    stack = [canonical]
    while stack:
        current = stack.pop()
        for inherited in ROLE_HIERARCHY.get(current, ()):
            inherited = canonical_role_name(inherited)
            if inherited in seen:
                continue
            seen.add(inherited)
            ordered.append(inherited)
            stack.append(inherited)
    return tuple(ordered)


def role_implies_role(role: str, required_role: str) -> bool:
    canonical_role = canonical_role_name(role)
    canonical_required = canonical_role_name(required_role)
    return canonical_role == canonical_required or canonical_required in _role_closure(canonical_role)


def _normalize_permission(permission: str) -> str:
    return str(permission).strip().lower()


def permission_matches(granted: str, requested: str) -> bool:
    granted = _normalize_permission(granted)
    requested = _normalize_permission(requested)
    if granted in {"*", "all"}:
        return True
    if granted == requested:
        return True
    if granted.endswith(".*"):
        prefix = granted[:-2]
        return requested == prefix or requested.startswith(f"{prefix}.")
    if granted.endswith(":*"):
        prefix = granted[:-2]
        return requested == prefix or requested.startswith(f"{prefix}:")
    return False


def role_permission_groups(role: str) -> list[str]:
    canonical = canonical_role_name(role)
    return list(ROLE_PERMISSION_GROUPS.get(canonical, ()))


def role_denies(role: str) -> list[str]:
    canonical = canonical_role_name(role)
    return list(ROLE_DENIES.get(canonical, ()))


def role_payment_scopes(role: str) -> list[str]:
    canonical = canonical_role_name(role)
    return list(ROLE_PAYMENT_SCOPES.get(canonical, ()))


def role_effective_permissions(role: str) -> list[str]:
    canonical = canonical_role_name(role)
    spec = _role_spec(canonical)
    granted: list[str] = []
    for permission in (
        *spec.get("permissions", ()),
        *role_permission_groups(canonical),
    ):
        if permission not in granted:
            granted.append(permission)
    for inherited in _role_closure(canonical):
        inherited_spec = _role_spec(inherited)
        for permission in (
            *inherited_spec.get("permissions", ()),
            *role_permission_groups(inherited),
        ):
            if permission not in granted:
                granted.append(permission)
    return granted


def _role_spec(role: str) -> dict[str, Any]:
    canonical = canonical_role_name(role)
    return {**LEGACY_ROLE_DEFINITIONS.get(canonical, {}), **CORE_ROLE_DEFINITIONS.get(canonical, {})}

def normalize_role_name(role: str) -> str:
    return role.strip().replace("-", "_").replace(" ", "_").upper()


ROLE_ALIASES: dict[str, str] = {}
for role, spec in {**CORE_ROLE_DEFINITIONS, **LEGACY_ROLE_DEFINITIONS}.items():
    ROLE_ALIASES[role] = role
    for alias in spec.get("aliases", ()):
        ROLE_ALIASES[normalize_role_name(alias)] = role


def canonical_role_name(role: str) -> str:
    normalized = normalize_role_name(role)
    return ROLE_ALIASES.get(normalized, normalized)


def role_definition(role: str) -> dict[str, Any]:
    canonical = canonical_role_name(role)
    spec = _role_spec(canonical)
    if spec:
        permission_groups = list(ROLE_PERMISSION_GROUPS.get(canonical, ()))
        denies = list(ROLE_DENIES.get(canonical, ()))
        return {
            "role": canonical,
            "label": spec["label"],
            "category": spec["category"],
            "mission": spec["mission"],
            "aliases": list(spec.get("aliases", ())),
            "permissions": list(spec.get("permissions", ())),
            "permission_groups": permission_groups,
            "denies": denies,
            "inherits": list(_role_closure(canonical)),
            "effective_permissions": role_effective_permissions(canonical),
            "visible_panels": list(spec.get("visible_panels", ())),
            "api_surfaces": list(spec.get("api_surfaces", ())),
            "dashboard_surface": spec.get("dashboard_surface"),
            "read_only": True,
            "governance_linked": True,
        }
    return {
        "role": canonical,
        "label": canonical.replace("_", " ").title(),
        "category": "unclassified",
        "mission": "Unclassified role surface",
        "aliases": [],
        "permissions": [],
        "permission_groups": [],
        "denies": [],
        "inherits": [],
        "effective_permissions": [],
        "visible_panels": [],
        "api_surfaces": [],
        "dashboard_surface": f"/v1/afriride/rbac/dashboard/{canonical.lower()}",
        "read_only": True,
        "governance_linked": True,
    }


def build_rbac_permission_matrix() -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for role in AUTH_ROLE_ORDER:
        spec = role_definition(role)
        for permission in spec["effective_permissions"]:
            matrix.append(
                {
                    "role": spec["role"],
                    "label": spec["label"],
                    "permission": permission,
                    "category": spec["category"],
                }
            )
    return matrix


def build_rbac_catalog(
    *,
    organization_id: str | None = None,
    assignments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    assignments = assignments or []
    counts = Counter(assignment.get("role_key") for assignment in assignments)
    core_roles = [role_definition(role) | {"assignment_count": counts.get(role, 0)} for role in CORE_ROLE_ORDER]
    legacy_roles = [role_definition(role) | {"assignment_count": counts.get(role, 0)} for role in LEGACY_ROLE_ORDER]
    return {
        "view": "afriride_rbac_catalog",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "status": "ready",
        "catalog_id": "AFRIRIDE_RBAC_CATALOG_V1",
        "core_roles": core_roles,
        "legacy_roles": legacy_roles,
        "permission_matrix": build_rbac_permission_matrix(),
        "summary": {
            "core_role_count": len(core_roles),
            "legacy_role_count": len(legacy_roles),
            "assignment_count": len(assignments),
            "permission_count": len(build_rbac_permission_matrix()),
        },
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def build_rbac_assignments(
    *,
    organization_id: str | None = None,
    assignments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    assignments = assignments or []
    normalized = [
        {
            **assignment,
            "role_profile": role_definition(str(assignment.get("role_key", assignment.get("role", "")))),
        }
        for assignment in assignments
    ]
    return {
        "view": "afriride_rbac_assignments",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "status": "ready",
        "assignments": normalized,
        "summary": {
            "assignment_count": len(normalized),
            "role_count": len({item["role_profile"]["role"] for item in normalized}) if normalized else 0,
            "subject_count": len({item.get("subject_id") for item in normalized}) if normalized else 0,
        },
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def build_rbac_access_check(*, role: str, permission: str) -> dict[str, Any]:
    spec = role_definition(role)
    requested = _normalize_permission(permission)
    denied = any(permission_matches(rule, requested) for rule in spec["denies"])
    allowed = not denied and any(permission_matches(rule, requested) for rule in spec["effective_permissions"])
    return {
        "view": "afriride_rbac_check",
        "role": spec["role"],
        "label": spec["label"],
        "permission": requested,
        "allowed": allowed,
        "reason": "permission_denied" if denied else ("permission_matched" if allowed else "permission_missing"),
        "permissions": spec["effective_permissions"],
        "permission_groups": spec["permission_groups"],
        "denies": spec["denies"],
        "inherits": spec["inherits"],
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }


def evaluate_rbac_access(
    *,
    role: str,
    permission: str,
    actor_id: str | None = None,
    owner_id: str | None = None,
    assigned_driver_id: str | None = None,
    privileged_roles: tuple[str, ...] = ("ADMIN",),
) -> dict[str, Any]:
    decision = build_rbac_access_check(role=role, permission=permission)
    if not decision["allowed"]:
        return decision
    canonical_role = canonical_role_name(role)
    privileged = {canonical_role_name(item) for item in privileged_roles}
    if owner_id is not None and actor_id is not None and actor_id != owner_id and canonical_role not in privileged:
        return {
            **decision,
            "allowed": False,
            "reason": "owner_mismatch",
            "owner_id": owner_id,
            "actor_id": actor_id,
        }
    if (
        assigned_driver_id is not None
        and actor_id is not None
        and actor_id != assigned_driver_id
        and canonical_role not in privileged
    ):
        return {
            **decision,
            "allowed": False,
            "reason": "assignment_mismatch",
            "assigned_driver_id": assigned_driver_id,
            "actor_id": actor_id,
        }
    return {
        **decision,
        "actor_id": actor_id,
        "owner_id": owner_id,
        "assigned_driver_id": assigned_driver_id,
        "reason": "context_matched" if owner_id or assigned_driver_id else decision["reason"],
    }


def build_rbac_role_dashboard(
    *,
    role: str,
    organization_id: str | None = None,
    assignment: dict[str, Any] | None = None,
    assignments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    spec = role_definition(role)
    assignments = assignments or []
    assignment_count = sum(1 for item in assignments if item.get("role_key") == spec["role"])
    dashboard = {
        "view": "afriride_rbac_role_dashboard",
        "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        "status": "ready",
        "role": spec,
        "assignment_count": assignment_count,
        "summary": {
            "permission_count": len(spec["effective_permissions"]),
            "visible_panel_count": len(spec["visible_panels"]),
            "api_surface_count": len(spec["api_surfaces"]),
            "inheritance_depth": len(spec["inherits"]),
        },
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
    }
    if assignment is not None:
        dashboard["assignment"] = assignment
    return dashboard
