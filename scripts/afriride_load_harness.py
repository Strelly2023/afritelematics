#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Lock
from uuid import uuid4


@dataclass(frozen=True)
class HttpResult:
    status_code: int
    payload: dict
    elapsed_ms: float


class AfriRideHarness:
    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._tokens: dict[tuple[str, str], str] = {}
        self._token_lock = Lock()

    def token(self, role: str, user_id: str) -> str:
        key = (role, user_id)
        with self._token_lock:
            token = self._tokens.get(key)
            if token is not None:
                return token
        result = self.request(
            "POST",
            "/auth/token",
            payload={"user_id": user_id, "role": role},
        )
        token = str(result.payload["token"])
        with self._token_lock:
            self._tokens[key] = token
        return token

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        payload: dict | None = None,
        idempotency_key: str | None = None,
    ) -> HttpResult:
        body = None
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        if payload is not None:
            body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                status_code = response.status
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            status_code = exc.code
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"unable to reach AfriRide API at {self.base_url}{path}: {exc.reason}"
            ) from exc
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        payload_json = json.loads(raw.decode("utf-8") or "{}")
        return HttpResult(status_code=status_code, payload=payload_json, elapsed_ms=elapsed_ms)


def _ok(result: HttpResult) -> bool:
    return 200 <= result.status_code < 300


def _idempotency(label: str, run_id: str, suffix: str) -> str:
    return f"load-{label}-{run_id}-{suffix}"


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _client_event(
    *,
    event_id: str,
    actor_type: str,
    actor_id: str,
    action: str,
    payload: dict,
) -> dict:
    return {
        "event_id": event_id,
        "device_id": f"device-{actor_type}-{actor_id}",
        "actor_type": actor_type,
        "actor_id": actor_id,
        "action": action,
        "payload": payload,
        "local_timestamp": _timestamp(),
        "app_version": "0.1",
        "test_mode": True,
    }


def _error_message(payload: dict) -> str | None:
    if isinstance(payload.get("detail"), str):
        return str(payload["detail"])
    error = payload.get("error")
    if isinstance(error, dict):
        if isinstance(error.get("message"), str):
            return str(error["message"])
        if isinstance(error.get("code"), str):
            return str(error["code"]).lower()
    return None


def run_full_lifecycle_case(
    harness: AfriRideHarness,
    *,
    case_index: int,
    driver_id: str,
) -> dict:
    ride_id = f"load-ride-{case_index}-{uuid4().hex[:10]}"
    rider_id = f"load-rider-{case_index}"
    rider_token = harness.token("RIDER", rider_id)
    driver_token = harness.token("DRIVER", driver_id)
    run_id = uuid4().hex[:10]

    create = harness.request(
        "POST",
        "/passenger/request-ride",
        token=rider_token,
        idempotency_key=_idempotency("create", run_id, "1"),
        payload={
            "passenger_id": rider_id,
            "pickup": f"Pickup {case_index}",
            "destination": f"Destination {case_index}",
            "ride_id": ride_id,
            "client_event": _client_event(
                event_id=f"{ride_id}-request",
                actor_type="rider",
                actor_id=rider_id,
                action="POST /passenger/request-ride",
                payload={"ride_id": ride_id},
            ),
        },
    )
    if not _ok(create):
        return {"ride_id": ride_id, "ok": False, "stage": "create", "response": create.payload}

    accept = harness.request(
        "POST",
        f"/ride/{ride_id}/accept",
        token=driver_token,
        idempotency_key=_idempotency("accept", run_id, "1"),
        payload={
            "driver_id": driver_id,
            "client_event": _client_event(
                event_id=f"{ride_id}-accept",
                actor_type="driver",
                actor_id=driver_id,
                action=f"POST /ride/{ride_id}/accept",
                payload={"driver_id": driver_id, "ride_id": ride_id},
            ),
        },
    )
    if not _ok(accept):
        return {"ride_id": ride_id, "ok": False, "stage": "accept", "response": accept.payload}

    arrive = harness.request(
        "POST",
        f"/ride/{ride_id}/arrive",
        token=driver_token,
        idempotency_key=_idempotency("arrive", run_id, "1"),
        payload={
            "driver_id": driver_id,
            "client_event": _client_event(
                event_id=f"{ride_id}-arrive",
                actor_type="driver",
                actor_id=driver_id,
                action=f"POST /ride/{ride_id}/arrive",
                payload={"driver_id": driver_id, "ride_id": ride_id},
            ),
        },
    )
    if not _ok(arrive):
        return {"ride_id": ride_id, "ok": False, "stage": "arrive", "response": arrive.payload}

    start = harness.request(
        "POST",
        f"/ride/{ride_id}/start",
        token=driver_token,
        idempotency_key=_idempotency("start", run_id, "1"),
        payload={
            "driver_id": driver_id,
            "client_event": _client_event(
                event_id=f"{ride_id}-start",
                actor_type="driver",
                actor_id=driver_id,
                action=f"POST /ride/{ride_id}/start",
                payload={"driver_id": driver_id, "ride_id": ride_id},
            ),
        },
    )
    if not _ok(start):
        return {"ride_id": ride_id, "ok": False, "stage": "start", "response": start.payload}

    complete = harness.request(
        "POST",
        f"/ride/{ride_id}/complete",
        token=driver_token,
        idempotency_key=_idempotency("complete", run_id, "1"),
        payload={
            "driver_id": driver_id,
            "client_event": _client_event(
                event_id=f"{ride_id}-complete",
                actor_type="driver",
                actor_id=driver_id,
                action=f"POST /ride/{ride_id}/complete",
                payload={"driver_id": driver_id, "ride_id": ride_id},
            ),
        },
    )
    if not _ok(complete):
        return {"ride_id": ride_id, "ok": False, "stage": "complete", "response": complete.payload}

    replay = harness.request("GET", f"/ride/{ride_id}/replay", token=rider_token)
    evidence = harness.request("GET", f"/ride/{ride_id}/evidence", token=rider_token)
    receipt = harness.request("GET", f"/ride/{ride_id}/receipt", token=rider_token)
    ledger = harness.request("GET", f"/ride/{ride_id}/ledger-receipt", token=rider_token)

    checks = {
        "replay_verified": replay.payload.get("replay_verified") is True,
        "evidence_verified": evidence.payload.get("verification_status") == "VERIFIED",
        "receipt_hash_present": len(str(receipt.payload.get("receipt_hash", ""))) == 64,
        "ledger_valid": ledger.payload.get("verdict") == "VALID",
        "ledger_signatures_valid": ledger.payload.get("signature_validation", {}).get("all_signatures_valid") is True,
        "ledger_identity_valid": ledger.payload.get("identity_validation", {}).get("all_verified") is True,
    }
    return {
        "ride_id": ride_id,
        "ok": all(checks.values()),
        "driver_id": driver_id,
        "stage": "verified",
        "checks": checks,
        "latency_ms": {
            "create": create.elapsed_ms,
            "accept": accept.elapsed_ms,
            "start": start.elapsed_ms,
            "complete": complete.elapsed_ms,
            "replay": replay.elapsed_ms,
            "evidence": evidence.elapsed_ms,
            "receipt": receipt.elapsed_ms,
            "ledger": ledger.elapsed_ms,
        },
    }


def run_accept_race(harness: AfriRideHarness) -> dict:
    rider_id = "race-rider-1"
    ride_id = f"race-ride-{uuid4().hex[:10]}"
    rider_token = harness.token("RIDER", rider_id)
    driver_ids = ("race-driver-a", "race-driver-b")
    driver_tokens = {driver_id: harness.token("DRIVER", driver_id) for driver_id in driver_ids}

    for driver_id in driver_ids:
        online = harness.request(
            "POST",
            "/driver/status",
            token=driver_tokens[driver_id],
            idempotency_key=_idempotency("driver-online", ride_id, driver_id),
            payload={
                "driver_id": driver_id,
                "online": True,
                "client_event": _client_event(
                    event_id=f"{ride_id}-online-{driver_id}",
                    actor_type="driver",
                    actor_id=driver_id,
                    action="POST /driver/status",
                    payload={"driver_id": driver_id, "online": True},
                ),
            },
        )
        if not _ok(online):
            return {"scenario": "accept-race", "ok": False, "stage": "driver-online", "response": online.payload}

    create = harness.request(
        "POST",
        "/passenger/request-ride",
        token=rider_token,
        idempotency_key=_idempotency("race-create", ride_id, "1"),
        payload={
            "passenger_id": rider_id,
            "pickup": "Race Pickup",
            "destination": "Race Destination",
            "ride_id": ride_id,
            "client_event": _client_event(
                event_id=f"{ride_id}-request",
                actor_type="rider",
                actor_id=rider_id,
                action="POST /passenger/request-ride",
                payload={"ride_id": ride_id},
            ),
        },
    )
    if not _ok(create):
        return {"scenario": "accept-race", "ok": False, "stage": "create", "response": create.payload}

    def accept(driver_id: str) -> tuple[str, HttpResult]:
        return (
            driver_id,
            harness.request(
                "POST",
                f"/ride/{ride_id}/accept",
                token=driver_tokens[driver_id],
                idempotency_key=_idempotency("race-accept", ride_id, driver_id),
                payload={
                    "driver_id": driver_id,
                    "client_event": _client_event(
                        event_id=f"{ride_id}-accept-{driver_id}",
                        actor_type="driver",
                        actor_id=driver_id,
                        action=f"POST /ride/{ride_id}/accept",
                        payload={"driver_id": driver_id, "ride_id": ride_id},
                    ),
                },
            ),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(accept, driver_ids))

    successes = [(driver_id, result) for driver_id, result in results if _ok(result)]
    failures = [(driver_id, result) for driver_id, result in results if not _ok(result)]
    status = harness.request("GET", f"/passenger/status/{ride_id}", token=rider_token)
    assigned_driver = status.payload.get("data", {}).get("assigned_driver")

    ok = (
        len(successes) == 1
        and len(failures) == 1
        and _error_message(failures[0][1].payload) == "ride_not_accepting_driver"
        and assigned_driver == successes[0][0]
    )
    return {
        "scenario": "accept-race",
        "ok": ok,
        "ride_id": ride_id,
        "winner": successes[0][0] if successes else None,
        "assigned_driver": assigned_driver,
        "results": {
            driver_id: {
                "status_code": result.status_code,
                "payload": result.payload,
            }
            for driver_id, result in results
        },
    }


def run_idempotency_race(harness: AfriRideHarness) -> dict:
    rider_id = "idempotency-rider-1"
    rider_token = harness.token("RIDER", rider_id)
    key = _idempotency("idempotency-race", uuid4().hex[:10], "1")
    payloads = (
        {
            "passenger_id": rider_id,
            "pickup": "A",
            "destination": "B",
            "ride_id": f"idempotency-race-a-{uuid4().hex[:8]}",
        },
        {
            "passenger_id": rider_id,
            "pickup": "A",
            "destination": "C",
            "ride_id": f"idempotency-race-b-{uuid4().hex[:8]}",
        },
    )

    def create(payload: dict) -> HttpResult:
        return harness.request(
            "POST",
            "/passenger/request-ride",
            token=rider_token,
            idempotency_key=key,
            payload={
                **payload,
                "client_event": _client_event(
                    event_id=f"{payload['ride_id']}-request",
                    actor_type="rider",
                    actor_id=rider_id,
                    action="POST /passenger/request-ride",
                    payload={"ride_id": payload["ride_id"]},
                ),
            },
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(create, payloads))

    successes = [result for result in results if _ok(result)]
    conflicts = [
        result
        for result in results
        if result.status_code == 409
        and _error_message(result.payload) == "idempotency_key_reused_with_different_payload"
    ]
    ok = len(successes) == 1 and len(conflicts) == 1
    return {
        "scenario": "idempotency-race",
        "ok": ok,
        "results": [
            {"status_code": result.status_code, "payload": result.payload}
            for result in results
        ],
    }


def run_lifecycle_load(harness: AfriRideHarness, *, rides: int, concurrency: int, drivers: int) -> dict:
    operator_token = harness.token("OPERATOR", "load-operator-1")
    driver_ids = tuple(f"load-driver-{index}" for index in range(1, drivers + 1))
    for driver_id in driver_ids:
        result = harness.request(
            "POST",
            "/driver/status",
            token=harness.token("DRIVER", driver_id),
            idempotency_key=_idempotency("driver-online", driver_id, "1"),
            payload={
                "driver_id": driver_id,
                "online": True,
                "client_event": _client_event(
                    event_id=f"driver-online-{driver_id}",
                    actor_type="driver",
                    actor_id=driver_id,
                    action="POST /driver/status",
                    payload={"driver_id": driver_id, "online": True},
                ),
            },
        )
        if not _ok(result):
            return {
                "scenario": "lifecycle-load",
                "ok": False,
                "stage": "driver-online",
                "driver_id": driver_id,
                "response": result.payload,
            }

    started = time.perf_counter()
    completed: list[dict] = []
    failures: list[dict] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_map = {
            executor.submit(
                run_full_lifecycle_case,
                harness,
                case_index=index,
                driver_id=driver_ids[(index - 1) % len(driver_ids)],
            ): index
            for index in range(1, rides + 1)
        }
        for future in as_completed(future_map):
            result = future.result()
            if result["ok"]:
                completed.append(result)
            else:
                failures.append(result)
    total_elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

    replay_health = harness.request("GET", "/system/replay/health", token=operator_token)
    evidence_summary = harness.request("GET", "/system/evidence", token=operator_token)
    guards = harness.request("GET", "/system/guards", token=operator_token)
    trace_validations = [
        harness.request("GET", f"/system/traces/{result['ride_id']}", token=operator_token).payload
        for result in completed
    ]
    lifecycle_trace_summary = {
        "total_rides": len(trace_validations),
        "valid_traces": sum(1 for payload in trace_validations if payload.get("valid") is True),
        "invalid_traces": sum(1 for payload in trace_validations if payload.get("valid") is not True),
        "missing_events": sum(len(payload.get("missing_transitions", ())) for payload in trace_validations),
        "replay_failures": sum(1 for payload in trace_validations if payload.get("replay_verified") is not True),
    }

    all_latencies = [
        latency
        for result in completed
        for latency in result["latency_ms"].values()
    ]
    average_latency_ms = round(sum(all_latencies) / len(all_latencies), 2) if all_latencies else None
    max_latency_ms = round(max(all_latencies), 2) if all_latencies else None

    ok = (
        not failures
        and all(payload.get("valid") is True for payload in trace_validations)
        and all(payload.get("replay_verified") is True for payload in trace_validations)
    )
    return {
        "scenario": "lifecycle-load",
        "ok": ok,
        "rides_requested": rides,
        "rides_completed": len(completed),
        "rides_failed": len(failures),
        "elapsed_ms": total_elapsed_ms,
        "average_step_latency_ms": average_latency_ms,
        "max_step_latency_ms": max_latency_ms,
        "replay_health": replay_health.payload,
        "evidence_summary_global": evidence_summary.payload,
        "guards_global": guards.payload,
        "lifecycle_trace_summary": lifecycle_trace_summary,
        "failures": failures,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AfriRide load and concurrency harness")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--scenario",
        choices=("lifecycle-load", "accept-race", "idempotency-race", "all"),
        default="all",
    )
    parser.add_argument("--rides", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--drivers", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--json-output", default="")
    return parser


def _preflight(harness: AfriRideHarness) -> None:
    health = harness.request("GET", "/health")
    if not _ok(health):
        raise RuntimeError(
            f"AfriRide API health check failed at {harness.base_url}/health "
            f"with status {health.status_code}"
        )


def _write_failure_report(path: str, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    harness = AfriRideHarness(args.base_url, timeout=args.timeout)
    try:
        _preflight(harness)
    except RuntimeError as exc:
        failure_payload = {
            "base_url": args.base_url,
            "ok": False,
            "scenario": args.scenario,
            "error": str(exc),
        }
        rendered = json.dumps(failure_payload, indent=2, sort_keys=True)
        print(rendered, file=sys.stderr)
        if args.json_output:
            _write_failure_report(args.json_output, failure_payload)
        return 2

    report: dict[str, dict] = {}

    try:
        if args.scenario in {"accept-race", "all"}:
            report["accept_race"] = run_accept_race(harness)
        if args.scenario in {"idempotency-race", "all"}:
            report["idempotency_race"] = run_idempotency_race(harness)
        if args.scenario in {"lifecycle-load", "all"}:
            report["lifecycle_load"] = run_lifecycle_load(
                harness,
                rides=args.rides,
                concurrency=args.concurrency,
                drivers=args.drivers,
            )
    except RuntimeError as exc:
        failure_payload = {
            "base_url": args.base_url,
            "ok": False,
            "scenario": args.scenario,
            "error": str(exc),
            "partial_results": report,
        }
        rendered = json.dumps(failure_payload, indent=2, sort_keys=True)
        print(rendered, file=sys.stderr)
        if args.json_output:
            _write_failure_report(args.json_output, failure_payload)
        return 2

    overall_ok = all(result.get("ok") for result in report.values())
    payload = {
        "base_url": args.base_url,
        "scenario": args.scenario,
        "ok": overall_ok,
        "results": report,
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    print(rendered)
    if args.json_output:
        _write_failure_report(args.json_output, payload)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
