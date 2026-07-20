#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release._common import dump_json, dump_text, load_json, load_yaml, repo_root


@dataclass
class GateResult:
    id: str
    statement: str
    mandatory: bool
    evaluation_type: str
    evaluator: str
    evidence_required: list[str]
    result: str
    reason: str


def worktree_clean(root: Path) -> bool:
    return subprocess.run(["git", "-C", str(root), "status", "--porcelain=v1"], check=True, capture_output=True, text=True).stdout.strip() == ""


def candidate_valid(root: Path, product: str) -> bool:
    path = root / "release" / "candidates" / f"{product.upper()}_RC.json"
    if not path.exists():
        return False
    data = load_json(path)
    return len(str(data.get("commit_sha") or "")) == 40 and data.get("selection_status") == "SELECTED"


def traceability_valid(root: Path, product: str) -> bool:
    path = root / "release" / "traceability" / f"{product.upper()}_TRACEABILITY.yaml"
    return path.exists() and bool(load_yaml(path).get("requirements"))


def evaluate_product(root: Path, product: str) -> dict[str, Any]:
    gate = load_yaml(root / "release" / "gates" / f"{product.upper()}_GA_GATES.yaml")
    entry: list[GateResult] = []
    exit_: list[GateResult] = []
    for criterion in gate.get("entry_criteria", []):
        if criterion["id"].endswith("001"):
            result, reason = ("PASS", "") if candidate_valid(root, product) else ("FAIL", "candidate manifest missing or invalid")
        elif criterion["id"].endswith("002"):
            result, reason = ("PASS", "") if worktree_clean(root) else ("FAIL", "worktree dirty")
        elif criterion["id"].endswith("003"):
            scope = load_yaml(root / "release" / "scopes" / "INITIAL_GA_SCOPE.yaml")
            result, reason = ("PASS", "") if scope.get("scope_id") == "INITIAL-GA-AU-VIC-001" else ("FAIL", "scope mismatch")
        else:
            result, reason = ("NOT_RUN", "")
        entry.append(GateResult(result=result, reason=reason, **{k: criterion[k] for k in ("id", "statement", "mandatory", "evaluation_type", "evaluator", "evidence_required")}))
    for criterion in gate.get("exit_criteria", []):
        if product == "novaride" and criterion["id"] == "NR-EXIT-001":
            result, reason = ("PASS", "") if traceability_valid(root, product) else ("FAIL", "traceability missing")
        elif product == "novaride" and criterion["id"] == "NR-EXIT-002":
            result, reason = ("BLOCKED", "external approval not present")
        elif product in {"novaid", "novapay"} and criterion["id"].endswith("001"):
            result, reason = ("BLOCKED", "external approvals not present")
        else:
            result, reason = ("BLOCKED", "commit-bound evidence incomplete")
        exit_.append(GateResult(result=result, reason=reason, **{k: criterion[k] for k in ("id", "statement", "mandatory", "evaluation_type", "evaluator", "evidence_required")}))
    product_pass = all(item.result == "PASS" for item in entry + exit_ if item.mandatory)
    if product_pass:
        classification = "GA_READY"
    elif any(item.result == "PASS" for item in entry + exit_):
        classification = "CONTROLLED_PILOT_READY"
    else:
        classification = "RC_SELECTED_NOT_CERTIFIED"
    return {
        "schema_version": gate.get("schema_version", "1.0"),
        "product": product,
        "release_candidate_id": gate.get("release_candidate_id"),
        "entry_criteria": [asdict(item) for item in entry],
        "exit_criteria": [asdict(item) for item in exit_],
        "classification": classification,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "decision": "PASS" if product_pass else "BLOCKED",
    }


def main() -> int:
    root = repo_root()
    out_dir = root / "artifacts" / "release-baseline" / "gates"
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for product in ("novaid", "novaride", "novapay"):
        result = evaluate_product(root, product)
        results[product] = result
        dump_json(out_dir / f"{product.upper()}_GATE_RESULT.json", result)
    dump_text(
        out_dir / "GA_GATE_SUMMARY.md",
        "# GA gate summary\n\n" + "\n".join(f"- {p}: {r['classification']} ({r['decision']})" for p, r in results.items()) + "\n",
    )
    print(json.dumps({"generated_at_utc": datetime.now(timezone.utc).isoformat(), "products": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
