import pytest

from afritech.runtime.consensus.semantic_consensus import local_consensus
from afritech.runtime.consensus.sync_protocol import build_sync_envelope
from afritech.runtime.engine.execution_engine import SemanticExecutionEngine
from afritech.runtime.recovery.snapshot_controller import create_snapshot, verify_snapshot
from afritech.runtime.system_enforcement.execution_guard import admit_contract
from afritech.runtime.system_enforcement.violation_handler import handle_violation
from afritech.semantic_engine.cache.proof_cache import ProofCache
from afritech.semantic_engine.cache.proof_canonical_store import ProofCanonicalStore
from afritech.semantic_engine.cache.semantic_index import SemanticIndex
from afritech.semantic_engine.conflict.detector import detect_conflict
from afritech.semantic_engine.conflict.resolver import resolve_conflict
from afritech.semantic_engine.equivalence.index import EquivalenceIndex
from afritech.semantic_engine.index.global_semantic_graph import GlobalSemanticGraph
from afritech.semantic_engine.ir.hasher import hash_expression
from afritech.semantic_engine.ir.schema import SystemInvalid
from afritech.semantic_engine.ir.serializer import from_json, to_json
from afritech.semantic_engine.optimizer.complexity_controller import (
    ComplexityLimits,
    enforce_complexity,
)
from afritech.semantic_engine.optimizer.complexity_tracker import track_complexity
from afritech.semantic_engine.parser.ir_builder import compile_semantic_yaml
from afritech.semantic_engine.proof.incremental_proof import IncrementalProofBuilder
from afritech.semantic_engine.proof.proof_dag import ProofDAG, ProofNode
from afritech.semantic_engine.proof.proof_serializer import proof_from_json, proof_to_json
from afritech.semantic_engine.satisfiability.global_solver import all_admissible, solve_all
from afritech.semantic_engine.state.global_state_registry import GlobalStateRegistry


CONTRACT_ROOT = "afritech/semantic_engine/contracts"


def _program(path="minimal_admit.yaml"):
    return compile_semantic_yaml(f"{CONTRACT_ROOT}/{path}")


def test_ir_serializer_round_trips_canonical_expression():
    expr = _program().expression

    restored = from_json(to_json(expr))

    assert hash_expression(restored) == hash_expression(expr)


def test_complexity_metrics_and_limits_are_enforced():
    expr = _program().expression
    metrics = track_complexity(expr)

    assert metrics.nodes > 1
    assert metrics.operators["AND"] == 1
    assert enforce_complexity(expr, ComplexityLimits(max_nodes=64, max_depth=16))

    with pytest.raises(SystemInvalid, match="complexity_node_limit_exceeded"):
        enforce_complexity(expr, ComplexityLimits(max_nodes=1))


def test_proof_cache_store_reuse_and_serialization():
    result = admit_contract(f"{CONTRACT_ROOT}/minimal_admit.yaml")
    proof = result["proof"]
    expr = _program().expression

    cache = ProofCache()
    cache.put(proof["normalized_expression_hash"], proof)
    assert cache.has(proof["normalized_expression_hash"])

    store = ProofCanonicalStore()
    expression_hash = store.store(expr, proof)
    assert store.load(expression_hash)["proof_hash"] == proof["proof_hash"]

    serialized = proof_to_json(proof)
    assert proof_from_json(serialized)["proof_hash"] == proof["proof_hash"]


def test_incremental_proof_reuses_existing_proof():
    result = admit_contract(f"{CONTRACT_ROOT}/minimal_admit.yaml")
    expr = _program().expression
    builder = IncrementalProofBuilder()

    first, reused_first = builder.build_or_reuse(expr, result["proof"]["evaluated"])
    second, reused_second = builder.build_or_reuse(expr, result["proof"]["evaluated"])

    assert reused_first is False
    assert reused_second is True
    assert first["proof_hash"] == second["proof_hash"]


def test_semantic_indexes_and_graphs():
    expr = _program().expression

    semantic_index = SemanticIndex()
    semantic_index.add("minimal", expr)
    assert semantic_index.programs_for_symbol("can_assign") == ["minimal"]
    assert semantic_index.programs_for_operator("REQUIRES") == ["minimal"]

    equivalence = EquivalenceIndex()
    equivalence.add("minimal", expr)
    assert equivalence.equivalent_ids(expr) == ["minimal"]
    assert equivalence.are_equivalent(expr, expr)

    graph = GlobalSemanticGraph()
    graph.add_dependency("admission", "determinism")
    assert graph.dependencies("admission") == ["determinism"]
    assert graph.validate_acyclic()


def test_conflict_detection_and_resolution_fail_closed():
    conflict = detect_conflict(f"{CONTRACT_ROOT}/adversarial_unsupported_operator.yaml")
    resolution = resolve_conflict(conflict)

    assert conflict is not None
    assert conflict.reason == "unsupported_operator:OR"
    assert resolution.status == "SYSTEM_INVALID"


def test_global_solver_and_execution_engine():
    valid = f"{CONTRACT_ROOT}/minimal_admit.yaml"
    denied = f"{CONTRACT_ROOT}/adversarial_rejected_admission.yaml"

    assert all_admissible([valid])
    assert all_admissible([valid, denied]) is False
    assert solve_all([valid, denied])[1]["status"] == "DENY"
    assert SemanticExecutionEngine().admit(valid)["status"] == "ADMIT"


def test_local_consensus_sync_snapshot_and_violation_helpers():
    result = admit_contract(f"{CONTRACT_ROOT}/minimal_admit.yaml")
    proof = result["proof"]

    consensus = local_consensus(
        [
            proof["normalized_expression_hash"],
            proof["normalized_expression_hash"],
        ]
    )
    assert consensus.agreed is True

    envelope = build_sync_envelope(result)
    assert envelope.semantic_hash == proof["normalized_expression_hash"]
    assert envelope.proof_hash == proof["proof_hash"]

    snapshot = create_snapshot({"semantic_hash": envelope.semantic_hash})
    assert verify_snapshot(snapshot)

    violation = handle_violation("unsupported_operator:OR")
    assert violation.action == "SYSTEM_INVALID"


def test_proof_dag_topological_order():
    dag = ProofDAG()
    dag.add_proof(ProofNode("root", "p1", "e1"))
    dag.add_proof(ProofNode("child", "p2", "e2"), depends_on=["root"])

    assert dag.topological_order() == ["root", "child"]
