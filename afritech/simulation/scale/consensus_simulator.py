"""
afritech.simulation.scale.consensus_simulator

Simulates distributed consensus using deterministic execution.

Guarantees:
- quorum agreement
- leader validation
- deterministic consensus outcome
"""

from __future__ import annotations

from typing import List, Dict, Tuple, Any
from collections import Counter

from afritech.simulation.scale.run_multi_node import run_simulation


# ============================================================
# CORE CONSENSUS
# ============================================================

def run_consensus_round(
    *,
    worker_counts: List[int],
    event_count: int,
    inject_failures: bool = False,
    failure_rate: int = 10,
) -> Dict[str, Any]:
    """
    Simulates a consensus round across multiple nodes.

    Each node independently computes result.

    A leader (simulated implicitly) selects the majority result.

    Args:
        worker_counts: list of worker counts per node
        event_count: number of events
        inject_failures: whether to inject failures
        failure_rate: frequency of failures

    Returns:
        dict with consensus result and metadata
    """

    if not worker_counts:
        raise ValueError("worker_counts must not be empty")

    node_results: List[List[str]] = []

    # ---------------------------------------------------------
    # Each node executes independently (deterministic)
    # ---------------------------------------------------------
    for wc in worker_counts:
        result = run_simulation(
            worker_count=wc,
            event_count=event_count,
            inject_failures=inject_failures,
            failure_rate=failure_rate,
        )
        node_results.append(result)

    # ---------------------------------------------------------
    # Quorum decision (majority vote)
    # ---------------------------------------------------------
    counts: Counter = Counter(tuple(r) for r in node_results)

    consensus_result_tuple, votes = counts.most_common(1)[0]
    consensus_result = list(consensus_result_tuple)

    total_nodes = len(worker_counts)
    majority_threshold = (total_nodes // 2) + 1

    return {
        "consensus": consensus_result,
        "votes": votes,
        "total_nodes": total_nodes,
        "majority_threshold": majority_threshold,
        "achieved_quorum": votes >= majority_threshold,
        "node_results": node_results,
    }


# ============================================================
# VALIDATION UTILITIES
# ============================================================

def assert_consensus(
    result: Dict[str, Any]
) -> None:
    """
    Validates that consensus reached quorum.

    Raises AssertionError if consensus is invalid.
    """

    assert result["achieved_quorum"], (
        f"Consensus quorum not reached\n"
        f"Votes: {result['votes']} / {result['total_nodes']}\n"
        f"Required: {result['majority_threshold']}"
    )


def is_consensus_stable(
    result_a: Dict[str, Any],
    result_b: Dict[str, Any],
) -> bool:
    """
    Checks if two consensus results are identical.
    """

    return result_a["consensus"] == result_b["consensus"]


# ============================================================
# DIAGNOSTIC UTILITIES
# ============================================================

def summarize_consensus(
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Provides a structured summary of consensus outcome.
    """

    return {
        "total_nodes": result["total_nodes"],
        "votes": result["votes"],
        "majority_threshold": result["majority_threshold"],
        "achieved_quorum": result["achieved_quorum"],
        "result_length": len(result["consensus"]),
    }


def detect_disagreements(
    result: Dict[str, Any]
) -> List[Tuple[int, List[str]]]:
    """
    Returns list of nodes that disagree with consensus.

    Each item:
        (node_index, node_result)
    """

    consensus = result["consensus"]
    disagreements: List[Tuple[int, List[str]]] = []

    for i, node_result in enumerate(result["node_results"]):
        if node_result != consensus:
            disagreements.append((i, node_result))

    return disagreements


# ============================================================
# SELF TESTS (PYTEST COMPATIBLE)
# ============================================================

def test_basic_consensus():
    result = run_consensus_round(
        worker_counts=[3, 5, 7],
        event_count=100,
    )

    assert_consensus(result)


def test_consensus_with_failures():
    result = run_consensus_round(
        worker_counts=[4, 6, 8],
        event_count=150,
        inject_failures=True,
        failure_rate=5,
    )

    assert_consensus(result)


def test_consensus_extreme_failure():
    result = run_consensus_round(
        worker_counts=[5, 7, 9],
        event_count=200,
        inject_failures=True,
        failure_rate=2,
    )

    assert_consensus(result)


def test_consensus_repeatability():
    r1 = run_consensus_round(
        worker_counts=[3, 5, 7],
        event_count=120,
    )

    r2 = run_consensus_round(
        worker_counts=[3, 5, 7],
        event_count=120,
    )

    assert is_consensus_stable(r1, r2)


def test_consensus_quorum_rule():
    result = run_consensus_round(
        worker_counts=[3, 5, 7],
        event_count=100,
    )

    assert result["votes"] >= result["majority_threshold"]