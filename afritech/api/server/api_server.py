from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Any, Dict
import asyncio

# Core runtime
from runtime.activation.constitutional_boot import ConstitutionalRuntime

# APIs
from api.proof_export.proof_export_api import ProofExportAPI
from api.audit_dashboard.audit_dashboard import AuditDashboard
from api.visualization.visualization_layer import VisualizationLayer
from api.visualization.visualization_dashboard import VisualizationDashboard

# Evaluation
from evaluation.persistence.transcript_store import TranscriptStore
from evaluation.drift.drift_dashboard import DriftDashboard
from evaluation.audit.audit_chain import AuditChain
from evaluation.drift.drift_detection_engine import DriftDetectionError

# Governance
from governance.voting.voting_engine import GovernanceVotingEngine

# Auth
from api.auth.dependencies import require_permission, auth_service

# ✅ PRODUCTION QUEUE (switch to Redis in Phase 2)
from execution.queue.redis_queue import RedisTaskQueue
from execution.queue.redis_result_store import RedisResultStore
from execution.queue.task_models import ExecutionTask

# ✅ Real-time
from api.realtime.websocket_manager import WebSocketManager
from api.realtime.event_bus import EventBus


# -----------------------------------------------------------------
# REQUEST MODELS
# -----------------------------------------------------------------

class ExecutionRequest(BaseModel):
    authority_profile: str
    replay_requirements: Dict[str, Any]
    payload: Dict[str, Any]


class VoteRequest(BaseModel):
    voter_id: str
    decision: str


class ExecutionResponse(BaseModel):
    result: Dict[str, Any]


# -----------------------------------------------------------------
# APPLICATION FACTORY
# -----------------------------------------------------------------

def create_app(base_path: str):

    app = FastAPI(
        title="AfriTech Constitutional Runtime API",
        version="5.0.0"
    )

    # -----------------------------------------------------------------
    # AUTH INIT
    # -----------------------------------------------------------------

    auth_service.register_key("admin-key", "admin_user", ["admin"])
    auth_service.register_key("auditor-key", "auditor_user", ["auditor"])
    auth_service.register_key("user-key", "basic_user", ["user"])
    auth_service.register_key("node-key", "node_user", ["node"])

    # -----------------------------------------------------------------
    # REAL-TIME INFRA
    # -----------------------------------------------------------------

    ws_manager = WebSocketManager()
    event_bus = EventBus()

    async def broadcast_wrapper(event):
        try:
            await ws_manager.broadcast(event)
        except Exception:
            # Never crash event loop
            pass

    event_bus.subscribe(broadcast_wrapper)

    # -----------------------------------------------------------------
    # SYSTEM INIT
    # -----------------------------------------------------------------

    runtime = ConstitutionalRuntime(base_path)
    runtime.event_bus = event_bus
    runtime.boot()

    store = TranscriptStore(base_path)
    drift_dashboard = DriftDashboard(store)
    audit_chain = AuditChain(store)

    proof_api = ProofExportAPI(store)
    audit_dashboard = AuditDashboard(store, drift_dashboard, audit_chain)

    visualization = VisualizationLayer(audit_dashboard, drift_dashboard)
    visual_dashboard = VisualizationDashboard(audit_dashboard, drift_dashboard)

    voting_engine = GovernanceVotingEngine(base_path)
    voting_engine.event_bus = event_bus

    # -----------------------------------------------------------------
    # ✅ REDIS-BASED EXECUTION (PHASE 2)
    # -----------------------------------------------------------------

    task_queue = RedisTaskQueue()
    task_store = RedisResultStore()

    # NOTE: Worker is NOT started here in production
    # Workers run as separate services

    # -----------------------------------------------------------------
    # ROOT
    # -----------------------------------------------------------------

    @app.get("/")
    def root():
        return {
            "status": "AfriTech Runtime Active",
            "mode": "constitutional_verified",
            "execution": "distributed_async_realtime",
            "queue": "redis",
            "governance": "policy + voting"
        }

    # -----------------------------------------------------------------
    # ✅ WEBSOCKET
    # -----------------------------------------------------------------

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):

        await ws_manager.connect(websocket)

        try:
            while True:
                await websocket.receive_text()

        except (WebSocketDisconnect, Exception):
            ws_manager.disconnect(websocket)

    # -----------------------------------------------------------------
    # ✅ SYNC EXECUTION (OPTIONAL DIRECT CALL)
    # -----------------------------------------------------------------

    @app.post("/execute", response_model=ExecutionResponse)
    def execute(req: ExecutionRequest,
                user=Depends(require_permission("execute"))):

        try:
            result = runtime.execute(req.dict(), lambda r: {
                "status": "success",
                "echo": r["payload"]
            })

            asyncio.create_task(event_bus.publish({
                "type": "EXECUTE_SYNC_COMPLETED"
            }))

            return {"result": result}

        except DriftDetectionError as d:
            report = getattr(d, "report", None)

            asyncio.create_task(event_bus.publish({
                "type": "DRIFT_DETECTED"
            }))

            raise HTTPException(
                status_code=409,
                detail={
                    "error": "DRIFT_DETECTED",
                    "drift_report": report.to_dict() if report else None
                }
            )

        except Exception as e:
            raise HTTPException(400, detail=str(e))

    # -----------------------------------------------------------------
    # ✅ ASYNC EXECUTION (PRIMARY)
    # -----------------------------------------------------------------

    @app.post("/execute_async")
    def execute_async(req: ExecutionRequest,
                      user=Depends(require_permission("execute"))):

        task = ExecutionTask(req.dict()).to_dict()

        task_queue.push(task)

        asyncio.create_task(event_bus.publish({
            "type": "TASK_QUEUED",
            "task_id": task["id"]
        }))

        return {
            "task_id": task["id"],
            "status": "QUEUED"
        }

    # -----------------------------------------------------------------
    # ✅ TASK STATUS
    # -----------------------------------------------------------------

    @app.get("/task/{task_id}")
    def get_task(task_id: str,
                 user=Depends(require_permission("execute"))):

        task = task_store.get(task_id)

        if not task:
            raise HTTPException(404, detail="Task not found")

        return task

    # -----------------------------------------------------------------
    # ✅ OBSERVABILITY
    # -----------------------------------------------------------------

    @app.get("/audit")
    def audit(user=Depends(require_permission("audit"))):
        return audit_dashboard.export_dashboard()

    @app.get("/drift")
    def drift(user=Depends(require_permission("audit"))):
        return drift_dashboard.export_dashboard()

    @app.get("/visual_dash")
    def visual(user=Depends(require_permission("dashboard"))):
        return visual_dashboard.build_dashboard()

    # -----------------------------------------------------------------
    # ✅ PROOF SYSTEM
    # -----------------------------------------------------------------

    @app.get("/proof/{entry_hash}")
    def proof(entry_hash: str,
              user=Depends(require_permission("proof"))):
        return proof_api.export_proof(entry_hash)

    @app.get("/proof_chain")
    def chain(user=Depends(require_permission("proof"))):
        return proof_api.export_chain()

    # -----------------------------------------------------------------
    # ✅ GOVERNANCE VOTING
    # -----------------------------------------------------------------

    @app.post("/adr/{adr_id}/start_vote")
    def start_vote(adr_id: str,
                   user=Depends(require_permission("audit"))):

        session = voting_engine.start_voting(adr_id)

        asyncio.create_task(event_bus.publish({
            "type": "VOTE_STARTED",
            "adr_id": adr_id
        }))

        return session.to_dict()

    @app.post("/adr/{adr_id}/vote")
    def vote(adr_id: str,
             body: VoteRequest,
             user=Depends(require_permission("audit"))):

        result = voting_engine.vote(
            adr_id,
            body.voter_id,
            body.decision
        )

        asyncio.create_task(event_bus.publish({
            "type": "VOTE_CAST",
            "adr_id": adr_id
        }))

        return result

    @app.get("/adr/{adr_id}/vote_status")
    def vote_status(adr_id: str,
                    user=Depends(require_permission("audit"))):
        return voting_engine.get_status(adr_id)

    @app.get("/adr/list")
    def list_adrs(user=Depends(require_permission("audit"))):
        return voting_engine.workflow.list_all()

    # -----------------------------------------------------------------
    # ✅ HEALTH CHECK
    # -----------------------------------------------------------------

    @app.get("/health")
    def health():
        return {
            "status": "OK",
            "system": "distributed",
            "queue": "redis"
        }

    return app