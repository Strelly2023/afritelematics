"""Full mobile client flow against the top-level AfriTech FastAPI app."""

from __future__ import annotations

from importlib import import_module
import shutil
import socket
import subprocess
import textwrap
import threading
import time
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

import httpx
import pytest
import uvicorn

from afritech.api.app import app

_runtime = import_module("afriride_system.api.dependencies.runtime")
reset_gateway = _runtime.reset_gateway
reset_trace_log = _runtime.reset_trace_log


def test_shared_js_mobile_client_completes_full_ride_flow(tmp_path, monkeypatch) -> None:
    if shutil.which("node") is None:
        pytest.skip("node is required for shared JS mobile client e2e")

    monkeypatch.setenv("AFRIRIDE_DB_PATH", str(tmp_path / "shared-js-mobile.sqlite3"))
    reset_gateway()
    reset_trace_log()

    client_module = tmp_path / "apiClient.mjs"
    client_module.write_text(
        Path("afriride_system/mobile/shared/apiClient.js").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    script = tmp_path / "full_mobile_flow.mjs"
    script.write_text(_mobile_flow_script(client_module), encoding="utf-8")

    with RunningAfriTechBackend() as base_url:
        result = subprocess.run(
            ["node", str(script), base_url],
            cwd=Path.cwd(),
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "mobile_flow_complete" in result.stdout


class RunningAfriTechBackend(AbstractContextManager[str]):
    def __enter__(self) -> str:
        self.port = _free_port()
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=self.port,
            log_level="error",
            lifespan="off",
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._wait_until_ready()
        return self.base_url

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=5)

    def _wait_until_ready(self) -> None:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                response = httpx.get(f"{self.base_url}/health", timeout=0.2)
                if response.status_code == 200:
                    return
            except httpx.HTTPError:
                time.sleep(0.05)
        raise RuntimeError("local AfriTech backend did not start")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", 0))
        except PermissionError as exc:
            pytest.skip(f"local port binding not permitted in this environment: {exc}")
        return int(sock.getsockname()[1])


def _mobile_flow_script(client_module: Path) -> str:
    module_url = client_module.resolve().as_uri()
    return textwrap.dedent(
        f"""
        import assert from "node:assert/strict";
        import {{
          acceptRide,
          arriveRide,
          authenticateUser,
          completeTrip,
          getActiveRides,
          getDriverAssignedRides,
          getDriverEarnings,
          getDriversSnapshot,
          getEvidenceHealth,
          getGuardViolations,
          getPilotMetrics,
          getReplayHealth,
          getRideEvidence,
          getRideReceipt,
          getRideReplay,
          getRideStatus,
          getSystemHealth,
          getTrustMetrics,
          requestRide,
          setApiBaseUrl,
          setDriverStatus,
          startTrip,
        }} from "{module_url}";

        const baseUrl = process.argv[2];
        setApiBaseUrl(baseUrl);

        const rideId = "ride-js-mobile-flow-001";
        const passengerId = "rider-js-mobile-001";
        const driverId = "driver-js-mobile-001";
        const operatorId = "operator-js-mobile-001";

        const riderSession = await authenticateUser({{ role: "RIDER", userId: passengerId }});
        const driverSession = await authenticateUser({{ role: "DRIVER", userId: driverId }});
        const operatorSession = await authenticateUser({{ role: "OPERATOR", userId: operatorId }});
        assert.ok(riderSession.token);
        assert.ok(driverSession.token);
        assert.ok(operatorSession.token);

        const driverOnline = await setDriverStatus({{ driverId, online: true }});
        assert.equal(driverOnline.online, true);

        const requested = await requestRide({{
          passengerId,
          pickup: "Bujumbura Central",
          destination: "Rohero Market",
          rideId,
        }});
        assert.equal(requested.ride_id, rideId);
        assert.equal(requested.status, "REQUESTED");

        const assigned = await getDriverAssignedRides({{ driverId }});
        assert.equal(assigned.rides.length, 1);
        assert.equal(assigned.rides[0].ride_id, rideId);

        const active = await getActiveRides({{ operatorId }});
        assert.equal(active.rides[0].ride_id, rideId);

        const accepted = await acceptRide({{ driverId, rideId }});
        assert.equal(accepted.status, "DRIVER_ASSIGNED");

        const arrived = await arriveRide({{ driverId, rideId }});
        assert.equal(arrived.status, "DRIVER_ARRIVED");

        const started = await startTrip({{ driverId, rideId }});
        assert.equal(started.status, "IN_TRIP");

        const completed = await completeTrip({{ driverId, rideId }});
        assert.equal(completed.status, "COMPLETED");

        const riderStatus = await getRideStatus({{ riderId: passengerId, rideId }});
        assert.equal(riderStatus.status, "COMPLETED");
        assert.equal(riderStatus.assigned_driver, driverId);

        const receipt = await getRideReceipt({{ riderId: passengerId, rideId }});
        assert.ok(receipt.receipt_hash);

        const replay = await getRideReplay({{ role: "RIDER", userId: passengerId, rideId }});
        assert.equal(replay.replay_verified, true);

        const evidence = await getRideEvidence({{ role: "DRIVER", userId: driverId, rideId }});
        assert.ok(evidence.trace_hash);

        const earnings = await getDriverEarnings({{ driverId }});
        assert.equal(earnings.driver_id, driverId);
        assert.equal(earnings.replay_verified, true);

        const health = await getSystemHealth({{ operatorId }});
        assert.equal(health.status, "ok");
        const drivers = await getDriversSnapshot({{ operatorId }});
        assert.equal(drivers.online_count, 1);
        const replayHealth = await getReplayHealth({{ operatorId }});
        assert.equal(replayHealth.status, "PASS");
        const evidenceHealth = await getEvidenceHealth({{ operatorId }});
        assert.equal(evidenceHealth.missing_traces, 0);
        const guards = await getGuardViolations({{ operatorId }});
        assert.equal(guards.violations.length, 0);
        const trust = await getTrustMetrics({{ operatorId }});
        assert.ok(["VERIFIED", "REVIEW"].includes(trust.trust_state));
        const pilot = await getPilotMetrics({{ operatorId }});
        assert.equal(pilot.completed_rides, 1);

        console.log("mobile_flow_complete", rideId);
        """
    )
