from __future__ import annotations

import asyncio

from afritech.platform_runtime.operational import RecoveryRunner


def test_restart_recovery_reports_recovered_when_state_exists() -> None:
    result = asyncio.run(RecoveryRunner().recover("novafleet", observed_state={"workers": ["fleet-worker"]}))
    assert result.status == "RECOVERED"

