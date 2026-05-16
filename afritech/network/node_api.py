"""
AfriTech Node API

Responsibilities:
- Accept execution requests
- Execute via runtime
- Return deterministic results
- Provide health, readiness, identity, and metrics endpoints
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest
import logging
import time
import uuid

# ✅ CORRECT IMPORTS (ALIGNED WITH ARCHITECTURE)
from afritech.runtime.engine.executor import ExecutionEngine
from afritech.shared.types import ExecutionResult
from afritech.shared.context import RuntimeContext
from afritech.network.node_identity import NodeIdentity


# -----------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("afritech.node_api")

EXECUTION_ENGINE: Optional[ExecutionEngine] = None
NODE_IDENTITY: Optional[NodeIdentity] = None
BOOT_TIME = time.time()


# -----------------------------------------------------------------
# INITIALIZATION
# -----------------------------------------------------------------

def init_node_api(
    execution_engine: ExecutionEngine,
    node_identity: NodeIdentity
):
    global EXECUTION_ENGINE, NODE_IDENTITY

    if execution_engine is None:
        raise RuntimeError("Execution engine must be provided")

    if node_identity is None:
        raise RuntimeError("Node identity must be provided")

    EXECUTION_ENGINE = execution_engine
    NODE_IDENTITY = node_identity

    logger.info("✅ Node API initialized")
    logger.info(f"Node ID: {NODE_IDENTITY.node_id}")
    logger.info(f"Identity Hash: {NODE_IDENTITY.identity_hash}")


# -----------------------------------------------------------------
# UTILS
# -----------------------------------------------------------------

def _safe_json() -> Dict[str, Any]:
    try:
        data = request.get_json(force=True, silent=False)
    except BadRequest:
        raise ValueError("Invalid JSON payload")

    if not isinstance(data, dict):
        raise ValueError("Request must be a JSON object")

    return data


def _node_id() -> Optional[str]:
    return NODE_IDENTITY.node_id if NODE_IDENTITY else None


def _request_id() -> str:
    return str(uuid.uuid4())


# -----------------------------------------------------------------
# EXECUTION ENDPOINT
# -----------------------------------------------------------------

@app.route("/execute", methods=["POST"])
def execute():
    if EXECUTION_ENGINE is None:
        return jsonify({"error": "Execution engine not initialized"}), 500

    req_id = _request_id()
    start_time = time.time()

    try:
        data = _safe_json()

        authority_profile = data.get("authority_profile")
        payload = data.get("payload")
        replay_requirements = data.get("replay_requirements", {})

        if not authority_profile:
            return jsonify({"error": "Missing authority_profile", "request_id": req_id}), 400

        if not isinstance(payload, dict):
            return jsonify({"error": "payload must be an object", "request_id": req_id}), 400

        # ✅ BUILD CONTEXT (SHARED STRUCTURE)
        context = RuntimeContext(
            authority_profile=authority_profile,
            payload=payload,
            replay_requirements=replay_requirements,
            context_hash=str(uuid.uuid4()),  # ✅ simplified deterministic id placeholder
            timestamp=str(time.time()),
        )

        # ✅ EXECUTION
        result: ExecutionResult = EXECUTION_ENGINE.execute(context)

        duration = round(time.time() - start_time, 6)

        response = result.to_dict()

        if not response.get("result_hash"):
            return jsonify({
                "error": "Missing result_hash (invalid execution contract)",
                "node_id": _node_id(),
                "request_id": req_id
            }), 500

        response.update({
            "node_id": _node_id(),
            "request_id": req_id,
            "execution_time": duration
        })

        if not result.success:
            logger.warning(f"[{req_id}] Execution failed")
            return jsonify(response), 500

        logger.info(
            f"[{req_id}] Execution success "
            f"({duration}s, hash={response['result_hash'][:10]}...)"
        )

        return jsonify(response), 200

    except ValueError as ve:
        return jsonify({
            "error": str(ve),
            "node_id": _node_id(),
            "request_id": req_id
        }), 400

    except Exception as e:
        logger.exception(f"[{req_id}] Unexpected error")

        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "node_id": _node_id(),
            "request_id": req_id
        }), 500


# -----------------------------------------------------------------
# HEALTH / READY / IDENTITY / METRICS (UNCHANGED)
# -----------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "HEALTHY",
        "node_id": _node_id(),
        "service": "afritech-node-api"
    })


@app.route("/ready", methods=["GET"])
def ready():
    if EXECUTION_ENGINE is None or NODE_IDENTITY is None:
        return jsonify({
            "status": "NOT_READY",
            "reason": "Dependencies not initialized"
        }), 503

    return jsonify({
        "status": "READY",
        "node_id": _node_id()
    })


@app.route("/identity", methods=["GET"])
def identity():
    if NODE_IDENTITY is None:
        return jsonify({"error": "Node identity not configured"}), 500

    return jsonify(NODE_IDENTITY.to_dict())


@app.route("/metrics", methods=["GET"])
def metrics():
    uptime = round(time.time() - BOOT_TIME, 2)

    return jsonify({
        "node_id": _node_id(),
        "status": "ACTIVE",
        "uptime_seconds": uptime
    })


# -----------------------------------------------------------------
# START SERVER
# -----------------------------------------------------------------

def run(host="0.0.0.0", port=8000, debug=False):
    if EXECUTION_ENGINE is None or NODE_IDENTITY is None:
        raise RuntimeError("Node API not initialized")

    logger.info(f"🚀 Starting AfriTech Node API on {host}:{port}")

    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    raise RuntimeError(
        "Node API must be initialized via init_node_api() before running."
    )