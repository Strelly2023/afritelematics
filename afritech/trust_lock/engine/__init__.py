"""Trust lock-in engine.

Externally consumed truth must not be replaceable without loss of institutional trust.
"""

from afritech.trust_lock.engine.dependency_model import (
    ExternalDependency,
    TrustDependencyGraph,
    build_dependency_graph,
)
from afritech.trust_lock.engine.removal_simulator import RemovalSimulation, simulate_removal
from afritech.trust_lock.engine.workflow_consumer import WorkflowResult, consume_audit_packet

__all__ = [
    "ExternalDependency",
    "RemovalSimulation",
    "TrustDependencyGraph",
    "WorkflowResult",
    "build_dependency_graph",
    "consume_audit_packet",
    "simulate_removal",
]

