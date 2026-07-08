from __future__ import annotations

from pathlib import Path

import pytest

from tests.internal_qa._helpers import ROOT


pytestmark = [pytest.mark.internal_qa, pytest.mark.qa_regression]


REQUIRED_SUITE_PATHS = [
    "tests/private_dev/test_private_dev_environment.py",
    "tests/private_dev/test_no_live_charging.py",
    "tests/private_dev/test_novaride_private_dev.py",
    "tests/private_dev/test_novapay_private_dev.py",
    "tests/private_dev/test_novaid_private_dev.py",
    "tests/test_novaride_apps.py",
    "tests/test_novapay_apps.py",
    "tests/test_novaid_apps.py",
    "tests/test_simulated_vs_real_payment_boundaries.py",
    "tests/test_novatech_scenario_catalog.py",
    "tests/test_novatech_enterprise_scenario_registry.py",
]


def test_internal_qa_regression_matrix_references_previous_suites() -> None:
    missing = [path for path in REQUIRED_SUITE_PATHS if not (ROOT / path).is_file()]
    assert not missing, f"missing regression suite files: {missing}"

    current = [
        "tests/test_internal_qa_environment.py",
        "tests/test_internal_qa_payment_safety.py",
        "tests/test_internal_qa_novaride_e2e.py",
        "tests/test_internal_qa_novapay_e2e.py",
        "tests/test_internal_qa_novaid_e2e.py",
        "tests/test_internal_qa_apk_release_validation.py",
        "tests/test_internal_qa_android_icons.py",
        "tests/test_internal_qa_api_contracts.py",
        "tests/test_internal_qa_release_guard.py",
        "tests/test_internal_qa_server_validation.py",
    ]
    assert all((ROOT / path).is_file() for path in current)
