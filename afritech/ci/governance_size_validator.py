from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "afritech/governance"
POLICY = ROOT / "afritech/ci/governance_size_policy.yaml"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_policy() -> dict[str, Any]:
    payload = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail("governance size policy must be a mapping")
    return payload


def run() -> None:
    thresholds = load_policy().get("thresholds")
    if not isinstance(thresholds, dict):
        fail("governance size policy missing thresholds")

    yaml_files = sorted(GOVERNANCE.rglob("*.yaml"))
    total_bytes = sum(path.stat().st_size for path in yaml_files)

    max_files = int(thresholds["max_yaml_files"])
    max_bytes = int(thresholds["max_yaml_bytes"])

    if len(yaml_files) > max_files:
        fail(f"governance YAML file count exceeds threshold: {len(yaml_files)} > {max_files}")

    if total_bytes > max_bytes:
        fail(f"governance YAML bytes exceed threshold: {total_bytes} > {max_bytes}")

    ratio = float(thresholds.get("compression_audit_ratio", 0.9))
    audit_files = len(yaml_files) >= max_files * ratio
    audit_bytes = total_bytes >= max_bytes * ratio

    print("✅ Governance size validation PASSED")
    print(f"✅ YAML files: {len(yaml_files)}/{max_files}")
    print(f"✅ YAML bytes: {total_bytes}/{max_bytes}")
    if audit_files or audit_bytes:
        print("⚠️ Compression audit threshold reached")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"❌ Governance size validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
