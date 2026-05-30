from __future__ import annotations

import pytest

from afritech.ci.afritech_constitution_v1_validator import (
    REQUIRED_BRANCHES,
    REQUIRED_BRANCH_DOMAINS,
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
