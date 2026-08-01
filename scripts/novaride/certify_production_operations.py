#!/usr/bin/env python3
"""Fail-closed operational certification for a target NovaRide environment."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
K8S = ROOT / "deploy" / "novaride" / "production"


def static_checks() -> dict[str, dict[str, object]]:
    deployment = yaml.safe_load((K8S / "api-deployment.yaml").read_text())
    hpa = yaml.safe_load((K8S / "hpa.yaml").read_text())
    pdb = yaml.safe_load((K8S / "pdb.yaml").read_text())
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    checks = {
        "ha_topology": (
            deployment["spec"]["replicas"] >= 3
            and bool(deployment["spec"]["template"]["spec"].get("topologySpreadConstraints"))
        ),
        "rolling_deployment": (
            deployment["spec"]["strategy"]["type"] == "RollingUpdate"
            and deployment["spec"]["strategy"]["rollingUpdate"]["maxUnavailable"] <= 1
        ),
        "health_probes": all(
            name in container for name in ("startupProbe", "readinessProbe", "livenessProbe")
        ),
        "autoscaling": hpa["spec"]["minReplicas"] >= 3,
        "disruption_budget": pdb["spec"]["minAvailable"] >= 2,
        "backup_command": "pg_dump" in (
            ROOT / "scripts" / "novaride" / "backup_runtime.sh"
        ).read_text(),
        "restore_command": "pg_restore" in (
            ROOT / "scripts" / "novaride" / "restore_runtime.sh"
        ).read_text(),
        "monitoring_rules": (
            ROOT / "deploy" / "novaride" / "monitoring" / "alerts-production.yml"
        ).exists(),
        "release_governance": (
            ROOT / "scripts" / "novaride" / "validate_production_readiness.py"
        ).exists(),
    }
    return {
        name: {"status": "PASS" if passed else "FAIL", "live": False}
        for name, passed in checks.items()
    }


def kubectl_json(*args: str) -> dict:
    result = subprocess.run(
        ["kubectl", *args, "-o", "json"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return json.loads(result.stdout)


def live_checks(namespace: str) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {
        gate: {
            "status": "BLOCKED",
            "live": True,
            "reason": "authenticated exercise evidence was not supplied",
        }
        for gate in (
            "live_backup_restore",
            "live_dr_rto_rpo",
            "live_monitoring_alert_delivery",
            "live_deployment_rollback",
        )
    }
    try:
        deployment = kubectl_json("-n", namespace, "get", "deployment", "novaride-api")
        desired = deployment["spec"]["replicas"]
        available = deployment.get("status", {}).get("availableReplicas", 0)
        results["live_api_replicas"] = {
            "status": "PASS" if desired >= 3 and available == desired else "FAIL",
            "live": True,
            "desired": desired,
            "available": available,
        }
        pods = kubectl_json("-n", namespace, "get", "pods", "-l", "app=novaride-api")
        node_names = {
            item.get("spec", {}).get("nodeName") for item in pods.get("items", [])
        }
        node_names.discard(None)
        zones: set[str] = set()
        for node_name in node_names:
            node = kubectl_json("get", "node", node_name)
            zone = node.get("metadata", {}).get("labels", {}).get(
                "topology.kubernetes.io/zone"
            )
            if zone:
                zones.add(zone)
        results["live_zone_distribution"] = {
            "status": "PASS" if len(zones) >= 2 else "FAIL",
            "live": True,
            "zones": sorted(zones),
        }
    except (subprocess.SubprocessError, KeyError, json.JSONDecodeError) as exc:
        results["live_kubernetes"] = {
            "status": "BLOCKED",
            "live": True,
            "reason": str(exc),
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", default="novaride-production")
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--output",
        default="artifacts/novaride/production-operations/certification.json",
    )
    args = parser.parse_args()

    checks = static_checks()
    if args.live:
        checks.update(live_checks(args.namespace))
    else:
        for gate in (
            "live_kubernetes_failover",
            "live_backup_restore",
            "live_dr_rto_rpo",
            "live_monitoring_alert_delivery",
            "live_deployment_rollback",
        ):
            checks[gate] = {
                "status": "BLOCKED",
                "live": True,
                "reason": "run against the target environment with authenticated evidence",
            }

    statuses = {entry["status"] for entry in checks.values()}
    final = "PASS" if statuses == {"PASS"} else ("FAIL" if "FAIL" in statuses else "BLOCKED")
    payload = {
        "certification": "NOVARIDE_PRODUCTION_OPERATIONS",
        "generated_at": datetime.now(UTC).isoformat(),
        "final_status": final,
        "checks": checks,
    }
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(output)
    return 0 if final == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
