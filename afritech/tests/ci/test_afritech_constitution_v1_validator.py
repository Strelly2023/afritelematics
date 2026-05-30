from __future__ import annotations

import pytest

from afritech.ci.afritech_constitution_v1_validator import (
    REQUIRED_BRANCHES,
    REQUIRED_BRANCH_DOMAINS,
    REQUIRED_CONSTITUTIONAL_PILLARS,
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
