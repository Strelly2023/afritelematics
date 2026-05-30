from __future__ import annotations

import pytest

from afritech.ci.afritech_constitution_v1_validator import (
    REQUIRED_BRANCHES,
    REQUIRED_BRANCH_DOMAINS,
    REQUIRED_CONSTITUTIONAL_PILLARS,
    REQUIRED_CORE_PILLAR_LAYERS,
    REQUIRED_ECOSYSTEM_PILLARS,
    validate,
)


def test_afritech_constitution_v1_validates():
    validate()


def test_afritech_constitution_v1_expected_branches_are_fixed():
    assert REQUIRED_BRANCHES == {
        "AfriCPPT": "GOVERNANCE",
        "AfriTPPS": "EXECUTION",
        "AfriProgramming": "ENGINEERING",
        "AFRIPower": "INTELLIGENCE",
    }


def test_afritech_constitution_v1_expected_domains_are_fixed():
    assert REQUIRED_BRANCH_DOMAINS == {
        "AfriCPPT": "GOVERNANCE",
        "AfriTPPS": "EXECUTION",
        "AFRIPower": "INTELLIGENCE",
        "AfriProgramming": "ENGINEERING",
    }


def test_afritech_constitution_v1_constitutional_pillars_are_fixed():
    assert REQUIRED_CONSTITUTIONAL_PILLARS == {
        "DETERMINISTIC_TRUTH": {
            "name": "Deterministic Truth",
            "constitutional_function": "Replay Governance",
        },
        "ORCHESTRATION": {
            "name": "Orchestration",
            "constitutional_function": "Replay-Safe Execution",
        },
        "DATA_LOCALITY": {
            "name": "Data Locality",
            "constitutional_function": "Compute Near Data",
        },
        "OBSERVABILITY": {
            "name": "Observability",
            "constitutional_function": "Explain Without Authority",
        },
    }


def test_afritech_constitution_v1_ecosystem_pillars_are_fixed():
    assert REQUIRED_ECOSYSTEM_PILLARS == {
        "AfriCPPT": {"role": "GOVERNANCE", "canonical_action": "governs"},
        "AfriTPPS": {"role": "EXECUTION", "canonical_action": "executes"},
        "AfriProgramming": {"role": "ENGINEERING", "canonical_action": "builds"},
        "AFRIPower": {"role": "INTELLIGENCE", "canonical_action": "explains"},
    }


def test_afritech_constitution_v1_core_pillar_layers_are_fixed():
    assert list(REQUIRED_CORE_PILLAR_LAYERS) == [
        "CONSTITUTIONAL_KERNEL",
        "RUNTIME",
        "DISTRIBUTED_SCALE",
        "GOVERNANCE",
        "HUMAN_ECOSYSTEM",
    ]
    assert sum(
        len(layer[2]) for layer in REQUIRED_CORE_PILLAR_LAYERS.values()
    ) == 18
    assert REQUIRED_CORE_PILLAR_LAYERS["CONSTITUTIONAL_KERNEL"][2] == (
        "DETERMINISTIC_EXECUTION",
        "REPLAY_LEGITIMACY",
        "CLOSED_WORLD_ADMISSIBILITY",
        "CANONICAL_IDENTITY",
        "CONSTITUTIONAL_AUTHORITY",
    )
    assert REQUIRED_CORE_PILLAR_LAYERS["HUMAN_ECOSYSTEM"][2] == (
        "HUMAN_CONTINUITY",
        "ECONOMIC_CONTINUITY",
        "INFRASTRUCTURE_SOVEREIGNTY",
    )
