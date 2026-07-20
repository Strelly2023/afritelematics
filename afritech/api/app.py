"""FastAPI entrypoint for the deterministic MVP production pipeline."""

from __future__ import annotations
from datetime import datetime
from importlib import import_module
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

# ============================================================
# API LAYERS
# ============================================================

from afritech.api.auth.jwt_device_auth import (
    authenticate_websocket,
    build_auth_router as build_pilot_auth_router,
    build_novacodepro_session_router,
    reject_websocket,
    require_roles,
)
from afritech.api.ingestion.event_ingestion import (
    EventIngestionAPI,
    MobileEventAuthenticator,
    build_router,
)
from afritech.api.realtime.dashboard_bus import dashboard_hub, publish_dashboard_event as broadcast_dashboard_event
from afritech.api.realtime.ride_bus import ride_hub
from afritech.api.trace_api import build_trace_router
from afritech.api.system_status import build_system_status_router
from afritech.api.partner_verification_api import build_partner_verification_router
from afritech.api.partner_registry_api import build_partner_registry_router
from afritech.api.partner_governance_api import build_partner_governance_router
from afritech.api.partner_certification_api import build_partner_certification_router
from afritech.api.api_catalog_api import build_api_catalog_router
from afritech.api.public_verification_api import build_public_verification_router
from afritech.api.public_gateway_api import build_enterprise_service_catalog_router, build_public_gateway_router
from afritech.api.ops_governance_api import build_ops_governance_router
from afritech.api.architecture_proof_api import build_architecture_proof_router
from afritech.api.afriride_mobile_release_api import build_afriride_mobile_release_router
from afritech.api.afriride_next_gen_mobile_api import build_afriride_next_gen_mobile_router
from afritech.api.novaride_runtime_api import build_novaride_runtime_router
from afritech.api.novaride_operations_api import build_novaride_operations_router
from afritech.api.phase0_api import build_phase0_router
from afritech.api.phase1_api import build_phase1_router
from afritech.api.phase2_api import build_phase2_router
from afritech.api.phase3_api import build_phase3_router
from afritech.api.phase4_api import build_phase4_router
from afritech.api.phase5_api import build_phase5_router
from afritech.api.phase6_api import build_phase6_router
from afritech.api.phase7_api import build_phase7_router
from afritech.api.phase8_api import build_phase8_router
from afritech.api.phase9_api import build_phase9_router
from afritech.api.phase10_api import build_phase10_router
from afritech.api.phase11_api import build_phase11_router
from afritech.api.phase12_api import build_phase12_router
from afritech.api.phase13_api import build_phase13_router
from afritech.api.mobile_intelligence_api import build_mobile_intelligence_router
from afritech.api.trust_network_api import build_trust_network_router
from afritech.api.dashboard_gateway_api import build_dashboard_gateway_router
from afritech.api.afroprog_workspace_api import build_afroprog_workspace_router
from afritech.api.novacodepro_workspace_api import build_novacodepro_workspace_router
from afritech.api.novascript_api import build_novascript_public_router, build_novascript_router
from afritech.api.novatech_intranet_api import build_novatech_intranet_router
from afritech.api.documentation_compliance_api import build_documentation_compliance_router
from afritech.api.data_governance_api import build_data_governance_router
from afritech.api.core_platform_api import (
    build_core_platform_router,
    build_public_trust_explorer_router,
)
from afritech.api.novapay_ecosystem_api import build_novapay_ecosystem_router
from afritech.api.novaid_api import build_novaid_router
from afritech.api.novaid_audit_replay_api import build_novaid_audit_replay_router
from afritech.novaid.runtime import build_default_durable_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro.platform import get_novacodepro_platform
from afritech.api.novacodepro_ncp007_api import build_novacodepro_ncp007_router
from afritech.api.novacodepro_ncp008_api import build_novacodepro_ncp008_router
from afritech.api.novacodepro_workflow_fabric_api import build_novacodepro_workflow_fabric_router
from afritech.api.executable_runtime_api import build_executable_runtime_router
from afritech.api.runtime_activation_api import build_runtime_activation_router
from afritech.api.runtime_infrastructure_api import build_runtime_infrastructure_router
from afritech.api.runtime_verification_api import build_runtime_verification_router
from afritech.api.runtime_worker_api import build_runtime_worker_router
from afritech.api.runtime_operations_api import build_runtime_operations_router
from afritech.api.api_platform_admin_api import build_api_platform_admin_router
from afritech.api.delivery_platform_api import build_delivery_platform_router
from afritech.api.integration_platform_api import build_integration_platform_router
from afritech.api.platform_runtime_api import build_platform_runtime_router
from afritech.api.solution_engineering_api import build_solution_engineering_router
from afritech.api.novacodepro_operational_verification_api import build_novacodepro_operational_verification_router
from afritech.api.novaportal_suite_api import build_novaportal_suite_router
from afritech.api.novapay_runtime_api import build_novapay_runtime_router
from afritech.api.contracts.schema_registry_api import build_schema_registry_router
from afritech.api.contracts.schema_registry_middleware import SchemaRegistryMiddleware
from afritech.api.afriprogramming_control_api import (
    build_afriprogramming_control_router,
)
from afritech.api.afriride_operational_api import build_afriride_operational_router
from afritech.api.feature_registry_api import build_feature_registry_router
from afritech.architecture.anchor_indexer import ANCHOR_EVENT_SUBSCRIBER, ANCHOR_STREAM_HUB

# ============================================================
# EDGE PIPELINE
# ============================================================

from afritech.edge.adapter.runtime_adapter import adapt_request
from afritech.edge.adapter.validation import validate_adapted_request
from afritech.edge.ingestion.queue_ingestor import ingest_event
from afritech.edge.normalization.normalizer import normalize_input
from afritech.edge.normalization.validation import validate_normalized_input

# ============================================================
# EXECUTION LAYER
# ============================================================

from afritech.execution.partition.router import get_partition
from afritech.execution.queue.partitioned_queue import PartitionedQueue
from afritech.execution.worker.worker_pool import WorkerPool
from afritech.core_platform.adaptive_sla import AdaptiveSLAController
from afritech.core_platform.autonomous_control import AutonomousControlPlane
from afritech.middleware.distributed_governance import DistributedGovernanceMiddleware
from afritech.middleware.request_logging import JsonRequestLoggingMiddleware
from afritech.middleware.multi_region_redis import RegionAwareRedisBackend, parse_region_redis_urls
from afritech.partner_registry import PartnerRegistryStore, seed_partner_registry
from afritech.partner_certification import PartnerCertificationStore, seed_partner_certification_registry
from afritech.partner_governance import PartnerGovernanceStore, seed_partner_governance_registry
from afritech.partner_verification import PartnerVerificationStore
from afritech.standards_dependency import StandardsDependencyStore
from afritech.trust_network import TrustRegistryStore
from afritech.observability.opentelemetry import configure_fastapi_observability
from afritech.novaride_runtime.replay.dependencies import build_default_replay_repository
from afritech.platform_runtime import build_default_product_runtime_registry
from afritech.platform_runtime.activation import ProductActivationService
from afritech.platform_runtime.deployment_verifier import DeploymentVerifier
from afritech.platform_runtime.executable_runtime import ExecutableProductRuntime
from afritech.platform_runtime.provisioning import InfrastructureProvisioner
from afritech.platform_runtime.runtime_evidence import RuntimeEvidenceService
from afritech.platform_runtime.route_registry import RouteRegistry
from afritech.api_platform import EndpointRegistry
from afritech.platform_runtime.adapters.base import AdapterExecutionMode
from afritech.platform_runtime.operational import OperationalRuntimeOrchestrator, PersistentEvidenceStore, RecoveryRunner, RollbackCoordinator, RuntimeVerificationService
from afritech.platform_runtime.persistence.repository import build_runtime_control_repository
from afritech.platform_runtime.worker_supervisor import WorkerSupervisor


# ============================================================
# APPLICATION INIT
# ============================================================

app = FastAPI(title="NovaTech Deterministic MVP Pipeline")

# ✅ CORS (IMPORTANT for React dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(JsonRequestLoggingMiddleware)
app.add_middleware(SchemaRegistryMiddleware)
configure_fastapi_observability(app)

# ============================================================
# CORE SYSTEM
# ============================================================

queue = PartitionedQueue(num_partitions=8)
worker_pool = WorkerPool(queue)

_EVENT_INGESTION_SECRET = os.environ.get("AFRITECH_EVENT_INGESTION_SECRET", "pilot-secret")


def runtime_event_ingestion_secret() -> str:
    return _EVENT_INGESTION_SECRET


mobile_event_ingestion = EventIngestionAPI(secret=runtime_event_ingestion_secret())
mobile_event_authenticator = MobileEventAuthenticator()
partner_verification_store = PartnerVerificationStore()
trust_registry_store = TrustRegistryStore()
standards_dependency_store = StandardsDependencyStore()
partner_registry_store = PartnerRegistryStore(seed_partner_registry())
partner_certification_store = PartnerCertificationStore(seed_partner_certification_registry())
partner_governance_store = PartnerGovernanceStore(seed_partner_governance_registry())
app.state.governance_store = partner_governance_store
_trust_redis_region = os.environ.get("AFRITECH_TRUST_REGION") or os.environ.get("AFRITECH_REGION") or "AU"
_trust_redis_urls = os.environ.get("AFRITECH_TRUST_REDIS_URLS")
_trust_redis_url_map = parse_region_redis_urls(_trust_redis_urls)
trust_redis_backend = RegionAwareRedisBackend.from_env(
    region=_trust_redis_region,
    region_urls=_trust_redis_url_map or None,
)
autonomous_control_plane = AutonomousControlPlane(client=trust_redis_backend)
adaptive_sla_controller = AdaptiveSLAController(
    client=trust_redis_backend,
    region=_trust_redis_region,
    autonomous_control=autonomous_control_plane,
)
app.state.adaptive_sla_controller = adaptive_sla_controller
app.state.autonomous_control_plane = autonomous_control_plane
app.state.novaride_replay_repository = build_default_replay_repository()
app.state.platform_runtime_registry = build_default_product_runtime_registry()
app.state.api_platform_endpoint_registry = EndpointRegistry()
app.state.platform_runtime_route_registry = RouteRegistry()
app.state.platform_runtime_worker_supervisor = WorkerSupervisor()
app.state.platform_runtime_infrastructure_provisioner = InfrastructureProvisioner()
app.state.platform_runtime_activation_service = ProductActivationService()
app.state.platform_runtime_evidence_service = RuntimeEvidenceService()
app.state.platform_runtime_verifier = DeploymentVerifier()
_runtime_control_repo = build_runtime_control_repository(
    dsn=os.environ.get("NOVATECH_POSTGRES_DSN") or os.environ.get("DATABASE_URL") or "",
    sqlite_path=Path(os.environ.get("NOVATECH_RUNTIME_CONTROL_SQLITE_PATH") or "/var/lib/afritech/runtime-control.sqlite3"),
)
app.state.platform_runtime_control_repository = _runtime_control_repo
app.state.platform_runtime_persistent_evidence_store = PersistentEvidenceStore(
    repository=_runtime_control_repo,
    object_root=Path(os.environ.get("NOVATECH_EVIDENCE_ROOT") or "/var/lib/afritech/runtime-evidence"),
)
app.state.platform_runtime_orchestrator = OperationalRuntimeOrchestrator(
    repository=_runtime_control_repo,
    evidence_store=app.state.platform_runtime_persistent_evidence_store,
    verifier=RuntimeVerificationService(),
    recovery_runner=RecoveryRunner(),
    rollback_coordinator=RollbackCoordinator(),
    adapter_modes={
        "postgres": AdapterExecutionMode.REAL,
        "redis": AdapterExecutionMode.REAL,
        "nats": AdapterExecutionMode.UNAVAILABLE,
        "object_storage": AdapterExecutionMode.REAL,
    },
)
app.state.platform_executable_runtime = ExecutableProductRuntime(
    app.state.platform_runtime_registry,
    route_registry=app.state.platform_runtime_route_registry,
    worker_supervisor=app.state.platform_runtime_worker_supervisor,
    infrastructure_provisioner=app.state.platform_runtime_infrastructure_provisioner,
    activation_service=app.state.platform_runtime_activation_service,
    evidence_service=app.state.platform_runtime_evidence_service,
    deployment_verifier=app.state.platform_runtime_verifier,
)
app.add_middleware(
    DistributedGovernanceMiddleware,
    store=partner_governance_store,
    region=_trust_redis_region,
    redis_backend=trust_redis_backend,
    adaptive_controller=adaptive_sla_controller,
    protected_paths=("/v1/trust/orgs", "/v1/partners"),
)


# ============================================================
# ROUTERS
# ============================================================

# ✅ Core ingestion API
app.include_router(build_router(mobile_event_ingestion))


@app.post("/pilot/evidence")
def pilot_evidence_compatibility(
    payload: dict[str, Any],
    request: Request,
) -> dict[str, Any]:
    """Accept driver pilot evidence and bridge it into signed event ingestion.

    Mobile clients should not carry the ingestion HMAC secret. This compatibility
    route preserves the driver diagnostics contract while the server signs the
    canonical mobile event before passing it through `/v1/events` rules.
    """
    captured_at = str(payload.get("captured_at") or "")
    timestamp = _pilot_evidence_timestamp_ms(captured_at)
    evidence_type = str(payload.get("type") or "driver_location_event")
    driver_id = str(
        payload.get("driver_id")
        or request.headers.get("X-AfriRide-Device-Id")
        or "unknown_driver"
    )
    evidence_payload = dict(payload.get("payload") or {})
    constraints = dict(payload.get("constraints") or {})
    event_type = _pilot_evidence_event_type(evidence_type)
    entity_id = str(
        evidence_payload.get("ride_id")
        or evidence_payload.get("rideId")
        or driver_id
    )
    event_id = str(
        request.headers.get("X-AfriRide-Event-Id")
        or f"pilot-{evidence_type}-{timestamp}"
    )
    mobile_event = {
        "event_id": event_id,
        "event_type": event_type,
        "device_id": str(
            request.headers.get("X-AfriRide-Device-Id")
            or evidence_payload.get("device_id")
            or driver_id
        ),
        "entity_id": entity_id,
        "timestamp": timestamp,
        "logical_clock": timestamp,
        "payload": _pilot_evidence_mobile_payload(
            evidence_type=evidence_type,
            event_type=event_type,
            entity_id=entity_id,
            evidence_payload=evidence_payload,
            constraints=constraints,
            verdict=str(payload.get("verdict") or "observed"),
        ),
        "signature": "0" * 64,
    }
    mobile_event["signature"] = mobile_event_authenticator.generate_signature(
        mobile_event,
        runtime_event_ingestion_secret(),
    )
    result = mobile_event_ingestion.ingest(
        [mobile_event],
        received_at_ms=int(time.time() * 1000),
    )
    if result["rejected"]:
        raise HTTPException(status_code=422, detail=result["rejected"])
    return {
        "status": "captured",
        "evidence_id": event_id,
        "node_id": "fastapi_event_ingestion",
        "proposal_id": entity_id,
        "accepted": result["accepted"],
    }


def _pilot_evidence_timestamp_ms(captured_at: str) -> int:
    if captured_at:
        try:
            normalized = captured_at.replace("Z", "+00:00")
            return int(datetime.fromisoformat(normalized).timestamp() * 1000)
        except ValueError:
            pass
    return int(time.time() * 1000)


def _pilot_evidence_event_type(evidence_type: str) -> str:
    if evidence_type == "ride_accept_latency":
        return "DRIVER_ACCEPTED_RIDE"
    return "DRIVER_LOCATION_UPDATE"


def _pilot_evidence_mobile_payload(
    *,
    evidence_type: str,
    event_type: str,
    entity_id: str,
    evidence_payload: dict[str, Any],
    constraints: dict[str, Any],
    verdict: str,
) -> dict[str, Any]:
    forbidden = {"replay_hash", "authority", "decision_authority"}
    cleaned = {key: value for key, value in evidence_payload.items() if key not in forbidden}
    if event_type == "DRIVER_LOCATION_UPDATE":
        latitude = cleaned.get("latitude") or cleaned.get("lat")
        longitude = cleaned.get("longitude") or cleaned.get("lon") or cleaned.get("lng")
        if latitude is not None:
            cleaned["latitude"] = str(latitude)
        if longitude is not None:
            cleaned["longitude"] = str(longitude)
    cleaned["ride_id"] = str(cleaned.get("ride_id") or cleaned.get("rideId") or entity_id)
    cleaned["evidence_type"] = evidence_type
    cleaned["constraints"] = constraints
    cleaned["verdict"] = verdict
    return cleaned

# ✅ Auth APIs
app.include_router(build_pilot_auth_router())
app.include_router(import_module("afriride_system.api.auth").build_auth_router())

# ✅ Trace API (dashboard critical)
trace_router = build_trace_router()
app.include_router(trace_router)

# ✅ System status API
app.include_router(build_system_status_router())

# ✅ Partner verification API
app.include_router(build_partner_verification_router(store=partner_verification_store))

# ✅ Partner registry API
app.include_router(build_partner_registry_router(store=partner_registry_store))

# ✅ Partner trust governance API
app.include_router(
    build_partner_governance_router(
        store=partner_governance_store,
        adaptive_controller=adaptive_sla_controller,
    )
)

# ✅ Partner certification API
app.include_router(
    build_partner_certification_router(
        store=partner_certification_store,
        partner_registry_store=partner_registry_store,
    )
)
app.include_router(build_api_catalog_router())

# ✅ Trust Network API
app.include_router(
    build_trust_network_router(
        store=trust_registry_store,
        dependency_store=standards_dependency_store,
        verification_store=partner_verification_store,
    )
)

# ✅ Controlled public verification API
app.include_router(
    build_public_verification_router(
        verification_store=partner_verification_store,
        registry_store=trust_registry_store,
        partner_store=partner_registry_store,
    )
)
app.include_router(build_public_gateway_router())
app.include_router(build_enterprise_service_catalog_router())

# ✅ Public architecture proof and partner demo API
app.include_router(build_architecture_proof_router())

# ✅ NovaRide mobile release readiness API
app.include_router(build_afriride_mobile_release_router())
app.include_router(build_afriride_next_gen_mobile_router())
app.include_router(build_novaride_runtime_router())
app.include_router(build_novaride_operations_router())

# ✅ Dashboard gateway API
app.include_router(build_dashboard_gateway_router())
app.include_router(build_novacodepro_workspace_router())
app.include_router(build_novatech_intranet_router())
app.include_router(build_data_governance_router())
app.include_router(build_documentation_compliance_router())
app.include_router(build_schema_registry_router())

# ✅ NovaTechSol core platform API
app.include_router(build_core_platform_router())
app.include_router(build_public_trust_explorer_router())
app.include_router(build_platform_runtime_router(app.state.platform_runtime_registry))
app.include_router(build_executable_runtime_router(app.state.platform_executable_runtime))
app.include_router(build_runtime_activation_router(app.state.platform_runtime_activation_service))
app.include_router(build_runtime_worker_router(app.state.platform_runtime_worker_supervisor))
app.include_router(build_runtime_infrastructure_router(app.state.platform_runtime_infrastructure_provisioner))
app.include_router(build_runtime_verification_router(app.state.platform_runtime_verifier))
app.include_router(build_runtime_operations_router(app.state.platform_runtime_orchestrator))
app.include_router(build_api_platform_admin_router(app.state.api_platform_endpoint_registry))
app.include_router(build_delivery_platform_router())
app.include_router(build_integration_platform_router())
app.include_router(
    build_novapay_runtime_router(
        governance_store=partner_governance_store,
    )
)
app.include_router(build_novapay_ecosystem_router())
app.include_router(build_novaid_router())
app.include_router(build_default_durable_router())
app.include_router(build_novaid_audit_replay_router())
app.include_router(build_novacodepro_platform_router())
app.include_router(build_novacodepro_ncp007_router(get_novacodepro_platform()))
app.include_router(build_novacodepro_ncp008_router(get_novacodepro_platform()))
app.include_router(build_novacodepro_workflow_fabric_router())
app.include_router(build_solution_engineering_router())
app.include_router(build_novacodepro_operational_verification_router())
app.include_router(build_novacodepro_session_router())
app.include_router(build_novaportal_suite_router())

# ✅ AfriPro workspace API
app.include_router(build_afroprog_workspace_router())
app.include_router(build_phase0_router())
app.include_router(build_phase1_router())
app.include_router(build_phase2_router())
app.include_router(build_phase3_router())
app.include_router(build_phase4_router())
app.include_router(build_phase5_router())
app.include_router(build_phase6_router())
app.include_router(build_phase7_router())
app.include_router(build_phase8_router())
app.include_router(build_phase9_router())
app.include_router(build_phase10_router())
app.include_router(build_phase11_router())
app.include_router(build_phase12_router())
app.include_router(build_phase13_router())
app.include_router(build_mobile_intelligence_router())

# ✅ NovaScript assistant API
app.include_router(build_novascript_router())
app.include_router(build_novascript_public_router())

# ✅ NovaProgramming internal toolchain API
app.include_router(build_afriprogramming_control_router())

# ✅ Governed feature registry API
app.include_router(build_feature_registry_router())

# ✅ Operator observability and audit APIs
app.include_router(build_ops_governance_router())

# ✅ NovaRide operational product API
app.include_router(
    import_module("afriride_system.api.passenger_routes").router,
    prefix="/passenger",
    tags=["afriride-passenger"],
)
app.include_router(
    import_module("afriride_system.api.driver_routes").router,
    prefix="/driver",
    tags=["afriride-driver"],
)
app.include_router(
    import_module("afriride_system.api.ride_routes").router,
    prefix="/ride",
    tags=["afriride-ride"],
)
app.include_router(import_module("afriride_system.api.system_routes").router)
app.include_router(build_afriride_operational_router())


@app.on_event("startup")
async def _start_anchor_event_subscription() -> None:
    await ANCHOR_STREAM_HUB.start()
    if ANCHOR_EVENT_SUBSCRIBER.enabled:
        await ANCHOR_EVENT_SUBSCRIBER.start()


@app.on_event("shutdown")
async def _stop_anchor_event_subscription() -> None:
    await ANCHOR_EVENT_SUBSCRIBER.stop()
    await ANCHOR_STREAM_HUB.stop()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root() -> dict[str, Any]:
    """Report bounded pilot API status without claiming product readiness."""
    return {
        "status": "active",
        "service": "NovaTech Deterministic MVP Pipeline",
        "legacy_service": "AfriTech Deterministic MVP Pipeline",
        "classification": "controlled_pilot_api",
        "product_ready": False,
        "docs": "/docs",
        "event_ingestion": "/v1/events",
        "trace_api": "/v1/traces",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    """Lightweight readiness probe surface for container health checks."""
    return {
        "status": "healthy",
        "service": "afritech-api",
        "version": "0.7.0",
        "environment": os.environ.get("AFRITECH_RUNTIME_ENVIRONMENT", "PUBLIC_PILOT"),
    }


@app.get("/v1/health")
def v1_health() -> dict[str, Any]:
    """Compatibility alias for release gating and mobile smoke tests."""
    return health()


@app.get("/live")
def live() -> dict[str, Any]:
    """Report liveness without dependency checks."""
    return {
        "alive": True,
        "service": "afritech-api",
    }


@app.get("/v1/live")
def v1_live() -> dict[str, Any]:
    """Compatibility alias for liveness checks."""
    return live()


def _configuration_valid() -> bool:
    environment = (
        os.environ.get("AFRITECH_RUNTIME_ENVIRONMENT")
        or os.environ.get("AFRITECH_ENV")
        or ""
    ).strip().lower()
    if not environment:
        return False
    if environment not in {"public_pilot", "controlled_pilot", "internal_qa", "private_development", "production"}:
        return False
    return True


def _database_ready() -> bool:
    db_target = os.environ.get("AFRIRIDE_DB_PATH", ":memory:")
    try:
        with sqlite3.connect(db_target, timeout=1.0) as connection:
            connection.execute("SELECT 1")
    except Exception:
        return False
    return True


def _disk_ready() -> bool:
    db_target = Path(os.environ.get("AFRIRIDE_DB_PATH", "/var/lib/afritech/pilot_state.sqlite3"))
    target_dir = db_target.parent if db_target.parent.exists() else Path("/tmp")
    try:
        stats = os.statvfs(target_dir)
    except OSError:
        return False
    free_bytes = stats.f_bavail * stats.f_frsize
    return free_bytes >= 50 * 1024 * 1024


def _tls_ready() -> bool:
    cert_path = os.environ.get("AFRITECH_TLS_CERT_PATH")
    key_path = os.environ.get("AFRITECH_TLS_KEY_PATH")
    if not cert_path and not key_path:
        return True
    if not cert_path or not key_path:
        return False
    return Path(cert_path).exists() and Path(key_path).exists()


def _migration_ready() -> bool:
    migration_state = os.environ.get("AFRITECH_MIGRATION_STATE_PATH")
    if not migration_state:
        return True
    path = Path(migration_state)
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").strip().lower()
    return text in {"applied", "ready", "complete", "completed"}


def _monitoring_ready() -> bool:
    return bool(_prometheus_metrics_text())


def _readiness_diagnostics(
    *,
    database_ready: bool,
    configuration_valid: bool,
    disk_ready: bool,
    tls_ready: bool,
    migration_ready: bool,
    monitoring_ready: bool,
) -> list[dict[str, Any]]:
    return [
        {"name": "AFRITECH_RUNTIME_ENVIRONMENT", "valid": configuration_valid},
        {"name": "AFRITECH_ENV", "valid": configuration_valid},
        {"name": "AFRIRIDE_DB_PATH", "valid": database_ready},
        {"name": "AFRITECH_TLS_CERT_PATH", "valid": tls_ready},
        {"name": "AFRITECH_TLS_KEY_PATH", "valid": tls_ready},
        {"name": "AFRITECH_MIGRATION_STATE_PATH", "valid": migration_ready},
        {"name": "AFRITECH_METRICS_ENDPOINT", "valid": monitoring_ready},
        {"name": "AFRITECH_MONITORING_READY", "valid": monitoring_ready},
        {"name": "DISK_SPACE", "valid": disk_ready},
    ]


def _prometheus_metrics_text() -> str:
    environment = (
        os.environ.get("AFRITECH_RUNTIME_ENVIRONMENT")
        or os.environ.get("AFRITECH_ENV")
        or "PUBLIC_PILOT"
    ).strip().lower()
    ready_flag = int(
        _configuration_valid()
        and _database_ready()
        and _disk_ready()
        and _tls_ready()
        and _migration_ready()
    )
    return "\n".join(
        (
            "# HELP afritech_api_up API process liveness.",
            "# TYPE afritech_api_up gauge",
            "afritech_api_up 1",
            "# HELP afritech_api_ready API readiness gate.",
            "# TYPE afritech_api_ready gauge",
            f"afritech_api_ready {ready_flag}",
            "# HELP afritech_api_build_info Static build metadata.",
            "# TYPE afritech_api_build_info gauge",
            f'afritech_api_build_info{{service="afritech-api",environment="{environment}",version="0.7.0"}} 1',
        )
    )


@app.get("/ready")
def ready() -> JSONResponse:
    """Report dependency readiness for deployment health gates."""
    database_ready = _database_ready()
    configuration_valid = _configuration_valid()
    disk_ready = _disk_ready()
    tls_ready = _tls_ready()
    migration_ready = _migration_ready()
    monitoring_ready = _monitoring_ready()
    payload = {
        "ready": bool(database_ready and configuration_valid and disk_ready and tls_ready and migration_ready and monitoring_ready),
        "database": "up" if database_ready else "down",
        "configuration": "valid" if configuration_valid else "invalid",
        "disk": "ok" if disk_ready else "low",
        "tls": "ok" if tls_ready else "missing",
        "migrations": "applied" if migration_ready else "pending",
        "monitoring": "available" if monitoring_ready else "unavailable",
        "diagnostics": _readiness_diagnostics(
            database_ready=database_ready,
            configuration_valid=configuration_valid,
            disk_ready=disk_ready,
            tls_ready=tls_ready,
            migration_ready=migration_ready,
            monitoring_ready=monitoring_ready,
        ),
    }
    status_code = 200 if payload["ready"] else 503
    return JSONResponse(status_code=status_code, content=payload)


@app.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus-compatible metrics for readiness and monitoring."""
    return Response(
        content=_prometheus_metrics_text(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.get("/health/products")
def health_products() -> dict[str, Any]:
    return app.state.platform_runtime_registry.health_snapshot()


@app.get("/health/products/{product_code}")
def health_product(product_code: str) -> dict[str, Any]:
    registry = app.state.platform_runtime_registry
    try:
        product = registry.get_product(product_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="unknown_product") from exc
    return {
        "platform": "NovaTech",
        "product": product,
        "health": registry.health_snapshot()["products"].get(product_code.lower(), {"status": "unknown"}),
    }


@app.get("/health/runtime")
def health_runtime() -> dict[str, Any]:
    return {
        "status": "ready",
        "control_store": "ready" if app.state.platform_runtime_control_repository else "unavailable",
        "adapters": app.state.platform_runtime_orchestrator.adapter_modes,
        "reconciliation": {"status": "ready", "last_run_at": ""},
    }


@app.get("/health/runtime/control-store")
def health_runtime_control_store() -> dict[str, Any]:
    return {"status": "ready", "backend": type(app.state.platform_runtime_control_repository).__name__}


@app.get("/health/runtime/adapters")
def health_runtime_adapters() -> dict[str, Any]:
    return {"status": "ready", "adapters": {key: value.value for key, value in app.state.platform_runtime_orchestrator.adapter_modes.items()}}


@app.get("/health/runtime/reconciliation")
def health_runtime_reconciliation() -> dict[str, Any]:
    return {"status": "ready", "last_run_at": ""}


@app.get("/health/runtime/deployments")
def health_runtime_deployments() -> dict[str, Any]:
    return {"status": "ready", "deployments": []}


@app.get("/health/runtime/evidence")
def health_runtime_evidence() -> dict[str, Any]:
    return {"status": "ready", "evidence_root": str(app.state.platform_runtime_persistent_evidence_store.object_root)}


@app.get("/v1/metrics")
def v1_metrics() -> Response:
    """Compatibility alias for the public metrics surface."""
    return metrics()


@app.get("/v1/ready")
def v1_ready() -> JSONResponse:
    """Compatibility alias for readiness gates."""
    return ready()


# ============================================================
# WEBSOCKET ADAPTER
# ============================================================

class FastAPIWebSocketClient:
    """Adapter so the observation-only hub can publish to FastAPI sockets."""

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket

    async def send_json(self, message: dict[str, Any]) -> None:
        await self.websocket.send_json(message)


# ============================================================
# REALTIME WEBSOCKET
# ============================================================

@app.websocket("/ws/ride/{ride_id}")
async def ride_projection_socket(websocket: WebSocket, ride_id: str) -> None:
    """Subscribe a client to observation-only projected ride state."""

    claims = authenticate_websocket(websocket, roles={"OPERATOR", "VERIFIER", "PARTNER", "OBSERVER"})
    if claims is None:
        await reject_websocket(websocket)
        return

    await websocket.accept()
    client = FastAPIWebSocketClient(websocket)
    ride_hub.subscribe(ride_id, client)

    try:
        await websocket.send_json(
            {
                "ride_id": ride_id,
                "status": "connected",
                "subscriber": claims.sub,
                "role": claims.role,
                "authority": "projection_only",
            }
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ride_hub.unsubscribe(ride_id, client)


# ============================================================
# REALTIME DASHBOARD SOCKET
# ============================================================

@app.websocket("/ws/dashboard")
async def dashboard_socket(websocket: WebSocket) -> None:
    """Subscribe a client to the live dashboard observation channel."""

    claims = authenticate_websocket(websocket, roles={"OPERATOR", "VERIFIER", "PARTNER", "OBSERVER", "DEVELOPER"})
    if claims is None:
        await reject_websocket(websocket)
        return

    await websocket.accept()
    client = FastAPIWebSocketClient(websocket)
    dashboard_hub.subscribe("dashboard", client)

    try:
        await websocket.send_json(
            {
                "channel": "dashboard",
                "status": "connected",
                "subscriber": claims.sub,
                "role": claims.role,
                "authority": "projection_only",
            }
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_hub.unsubscribe("dashboard", client)


# ============================================================
# REALTIME PUBLISH (PILOT)
# ============================================================

@app.post("/v1/realtime/ride/{ride_id}/projection")
async def publish_ride_projection(
    ride_id: str,
    payload: dict[str, Any],
    _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
) -> dict[str, Any]:
    """Pilot-only projection publisher; does not mutate source-of-truth."""

    data = dict(payload.get("data", payload))
    message = await ride_hub.publish_state_update(ride_id, data)
    await broadcast_dashboard_event(
        "RIDE_PROJECTION_UPDATE",
        {
            "ride_id": ride_id,
            "projection": data,
            "source": "ride_projection",
            "status": data.get("status") or data.get("state") or "UNKNOWN",
        },
    )

    return {
        "status": "published",
        "message": message,
    }


@app.post("/v1/realtime/dashboard/publish")
async def publish_dashboard_projection(
    payload: dict[str, Any],
    _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "DEVELOPER")),
) -> dict[str, Any]:
    """Pilot-only dashboard event publisher for live browser projections."""

    event_type = str(payload.get("type", "DASHBOARD_SNAPSHOT"))
    data = dict(payload.get("data", payload))
    message = await broadcast_dashboard_event(event_type, data)
    return {
        "status": "published",
        "message": message,
    }


# ============================================================
# EDGE PROCESSING PIPELINE
# ============================================================

@app.post("/process")
def process(
    payload: dict[str, Any],
    _: object = Depends(require_roles("OPERATOR", "DEVICE")),
) -> dict[str, Any]:
    """Process one external request through the deterministic edge pipeline."""

    raw_input = {
        "request_id": str(payload.get("request_id")),
        "user_id": str(payload.get("user_id")),
        "timestamp": int(payload.get("timestamp", 0)),
        "payload": dict(payload),
    }

    # Edge → Adapter
    adapted = adapt_request(raw_input)
    validate_adapted_request(adapted)

    # Edge → Normalization
    normalized = normalize_input(adapted)
    validate_normalized_input(normalized)

    # Execution routing
    partition_id = get_partition(normalized, queue.num_partitions)

    # Ingestion
    ingest_event(normalized, queue, partition_id=partition_id)

    return {
        "status": "accepted",
        "request_id": normalized["request_id"],
        "partition_id": partition_id,
    }


# ============================================================
# WORKER CONTROL
# ============================================================

@app.post("/workers/drain")
def drain_workers(
    partition_id: int | None = None,
    _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
) -> dict[str, Any]:
    """Run deterministic worker cycles for queued events."""

    outputs = worker_pool.drain(partition_id=partition_id)

    return {
        "status": "drained",
        "processed": len(outputs),
        "outputs": [result.outputs for result in outputs],
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": str(exc.detail).upper(),
                "message": str(exc.detail),
            }
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if request.url.path == "/public/architecture/proof":
        return JSONResponse(
            status_code=200,
            content={
                "status": "generation_failed",
                "classification": "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF",
                "authority_boundary": (
                    "architecture proof generation failed before publication; "
                    "replay and governed execution remain the authority"
                ),
                "proof_id": None,
                "runtime_boundary_status": "UNKNOWN",
                "proof": None,
                "error": {
                    "code": "ARCHITECTURE_PROOF_GENERATION_FAILED",
                    "type": type(exc).__name__,
                    "message": str(exc) or "architecture proof generation failed",
                },
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "SERVER_ERROR",
                "message": "internal server error",
            }
        },
    )
