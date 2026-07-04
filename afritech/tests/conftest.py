from __future__ import annotations

from fnmatch import fnmatch

import pytest


SERIAL_PATTERNS = (
    "runtime_boundary",
    "artifact",
    "snapshot",
    "replay_global_state",
    "database",
    "migration",
)

MARKER_RULES = (
    ("fast", ("afritech/tests/cli/", "afritech/tests/tools/", "afritech/tests/reporting/", "afritech/tests/crypto/", "afritech/tests/core_platform/", "afritech/tests/observability/", "afritech/tests/governance/", "afritech/tests/platform_contracts/", "afritech/tests/standards/", "afritech/tests/identity/")),
    ("unit", ("afritech/tests/cli/", "afritech/tests/tools/", "afritech/tests/reporting/", "afritech/tests/crypto/", "afritech/tests/core_platform/", "afritech/tests/observability/", "afritech/tests/governance/", "afritech/tests/platform_contracts/", "afritech/tests/standards/", "afritech/tests/identity/")),
    ("contract", ("afritech/tests/platform_contracts/", "afritech/tests/standards/", "afritech/tests/certification/", "afritech/tests/api/test_*contract*", "afritech/tests/api/test_*schema*", "afritech/tests/api/test_*discovery*")),
    ("governance", ("afritech/tests/ci/", "afritech/tests/guards/", "afritech/tests/certification/")),
    ("trust", ("afritech/tests/proof/", "afritech/tests/replay/", "afritech/tests/trust_lock/")),
    ("payments", ("afritech/tests/afripay/", "afritech/tests/novapay/")),
    ("novapay", ("afritech/tests/novapay/", "afritech/tests/api/test_novapay_")),
    ("novaride", ("afritech/tests/api/test_novaride_", "ecosystems/afriride/tests/")),
    ("identity", ("afritech/tests/identity/", "afritech/tests/federation/", "afritech/tests/api/test_afriride_rbac_api.py", "afritech/tests/api/test_trace_api.py", "afritech/tests/api/test_identity_")),
    ("slow", ("afritech/tests/load/", "afritech/tests/performance/", "afritech/tests/monitoring/", "afritech/tests/runtime/", "ecosystems/afriride/tests/performance/")),
    ("mobile", ("afritech/tests/api/test_afriride_", "rider_app/", "driver_app/", "afriride_system/mobile/")),
    ("dashboard", ("dashboard/tests/",)),
    ("integration", ("afritech/tests/api/test_",)),
    ("release", ("afritech/tests/certification/", "afritech/tests/ci/test_production_readiness_certificate.py")),
)


def _matches(nodeid: str, pattern: str) -> bool:
    return nodeid.startswith(pattern) or pattern in nodeid or fnmatch(nodeid, pattern)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        nodeid = item.nodeid.replace("\\", "/")
        if any(token in nodeid for token in SERIAL_PATTERNS):
            item.add_marker(pytest.mark.serial)
        for marker, prefixes in MARKER_RULES:
            if any(_matches(nodeid, prefix) for prefix in prefixes):
                item.add_marker(getattr(pytest.mark, marker))
