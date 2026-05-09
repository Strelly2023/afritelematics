"""
afritech/health_monitor.py

Health Monitor
==============

Monitors health and readiness of distributed nodes.

Responsibilities:
- Perform health checks (liveness)
- Perform readiness checks
- Update NodeRegistry states
- Provide cluster health metrics
"""

from __future__ import annotations

from typing import Dict, Any, List
import time

from network.node_registry import NodeRegistry, NodeState
from network.node.http_node_client import HttpNodeClient


# -----------------------------------------------------------------
# HEALTH MONITOR ERROR
# -----------------------------------------------------------------

class HealthMonitorError(Exception):
    pass


# -----------------------------------------------------------------
# HEALTH MONITOR
# -----------------------------------------------------------------

class HealthMonitor:

    def __init__(
        self,
        node_registry: NodeRegistry,
        check_interval: float = 5.0,
        timeout: float = 2.0,
        failure_threshold: int = 3,
    ):
        """
        :param node_registry: NodeRegistry instance
        :param check_interval: interval between checks (seconds)
        :param timeout: request timeout for health checks
        :param failure_threshold: failures before marking unhealthy
        """
        self.node_registry = node_registry
        self.check_interval = check_interval
        self.timeout = timeout
        self.failure_threshold = failure_threshold
        self._running = False

    # -----------------------------------------------------------------
    # MAIN LOOP (OPTIONAL THREAD USAGE)
    # -----------------------------------------------------------------

    def start(self):
        """
        Blocking loop (run in thread for production)
        """
        self._running = True

        while self._running:
            self.check_all()
            time.sleep(self.check_interval)

    def stop(self):
        self._running = False

    # -----------------------------------------------------------------
    # CHECK ALL NODES
    # -----------------------------------------------------------------

    def check_all(self) -> Dict[str, Any]:
        """
        Check health of all nodes
        """

        results = []

        for record in self.node_registry.list_all():

            identity = record.identity
            metadata = identity.metadata or {}
            url = metadata.get("url")

            if not url:
                continue  # skip nodes without endpoint

            client = HttpNodeClient(
                node_id=identity.node_id,
                base_url=url,
                timeout=self.timeout
            )

            result = self._check_node(record, client)
            results.append(result)

        return {
            "timestamp": time.time(),
            "results": results,
            "stats": self.node_registry.stats()
        }

    # -----------------------------------------------------------------
    # CHECK SINGLE NODE
    # -----------------------------------------------------------------

    def _check_node(self, record, client: HttpNodeClient) -> Dict[str, Any]:

        node_id = record.identity.node_id

        try:
            # Liveness check
            healthy = client.health()

            if not healthy:
                record.mark_failure()

                if record.failures >= self.failure_threshold:
                    record.state = NodeState.UNHEALTHY

                return {
                    "node_id": node_id,
                    "status": "UNHEALTHY",
                    "failures": record.failures
                }

            # Readiness check (optional)
            ready = self._check_ready(client)

            if not ready:
                record.mark_failure()

                return {
                    "node_id": node_id,
                    "status": "NOT_READY",
                    "failures": record.failures
                }

            # Success
            record.mark_seen()

            return {
                "node_id": node_id,
                "status": "ACTIVE",
                "failures": record.failures
            }

        except Exception as e:
            record.mark_failure()

            return {
                "node_id": node_id,
                "status": "ERROR",
                "error": str(e),
                "failures": record.failures
            }

    # -----------------------------------------------------------------
    # READINESS CHECK
    # -----------------------------------------------------------------

    def _check_ready(self, client: HttpNodeClient) -> bool:
        """
        Calls /ready endpoint
        """

        try:
            import requests

            response = requests.get(
                f"{client.base_url}/ready",
                timeout=self.timeout
            )

            if response.status_code != 200:
                return False

            data = response.json()

            return data.get("status") == "READY"

        except Exception:
            return False

    # -----------------------------------------------------------------
    # CLUSTER SNAPSHOT
    # -----------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """
        Get current cluster state without triggering checks
        """

        return {
            "nodes": [n.to_dict() for n in self.node_registry.list_all()],
            "stats": self.node_registry.stats(),
            "timestamp": time.time()
        }

    # -----------------------------------------------------------------
    # STRING
    # -----------------------------------------------------------------

    def __repr__(self):
        stats = self.node_registry.stats()
        return (
            f"<HealthMonitor nodes={stats.get('total')} "
            f"active={stats.get('active')} "
            f"unhealthy={stats.get('unhealthy')}>"
        )
