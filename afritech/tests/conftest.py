from __future__ import annotations

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
    ("governance", ("afritech/tests/ci/", "afritech/tests/guards/", "afritech/tests/certification/")),
    ("trust", ("afritech/tests/proof/", "afritech/tests/replay/", "afritech/tests/trust_lock/")),
    ("payments", ("afritech/tests/afripay/", "afritech/tests/novapay/")),
    ("mobile", ("afritech/tests/api/test_afriride_", "rider_app/", "driver_app/", "afriride_system/mobile/")),
    ("dashboard", ("dashboard/tests/",)),
    ("integration", ("afritech/tests/api/test_",)),
    ("release", ("afritech/tests/certification/", "afritech/tests/ci/test_production_readiness_certificate.py")),
)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        nodeid = item.nodeid.replace("\\", "/")
        if any(token in nodeid for token in SERIAL_PATTERNS):
            item.add_marker(pytest.mark.serial)
        for marker, prefixes in MARKER_RULES:
            if any(nodeid.startswith(prefix) or prefix in nodeid for prefix in prefixes):
                item.add_marker(getattr(pytest.mark, marker))
