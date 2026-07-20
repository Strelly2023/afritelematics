#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release._common import dump_json, repo_root, load_json
from release_tools.release_context import release_context


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    root = repo_root()
    context = release_context(root)
    candidate = load_json(root / "release" / "candidates" / f"{args.product.upper()}_RC.json")
    reasons = []
    if not context.worktree_clean or context.staged_changes or context.untracked_files:
        reasons.append("dirty worktree")
    if candidate.get("commit_sha") != context.current_commit:
        reasons.append("candidate commit mismatch")
    evidence_manifest = root / "artifacts" / "release-baseline" / "evidence" / f"{args.product}" / "TRACEABILITY_SUMMARY.json"
    if not evidence_manifest.exists():
        reasons.append("missing evidence manifest")
    result = "REJECTED" if reasons else "PASS"
    cert = {
        "certificate_id": f"{args.candidate}-CERT-001",
        "product": args.product,
        "release_candidate_id": args.candidate,
        "commit_sha": candidate.get("commit_sha", ""),
        "repository_tree_hash": candidate.get("repository_tree_sha256", ""),
        "product_tree_hash": candidate.get("product_tree_sha256", ""),
        "scope_id": candidate.get("scope_id", ""),
        "environment_id": context.environment_id,
        "evidence_manifest_id": "TRACEABILITY_SUMMARY",
        "evidence_manifest_hash": hashlib.sha256(evidence_manifest.read_bytes()).hexdigest() if evidence_manifest.exists() else "",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generator_version": "1.0",
        "worktree_clean": context.worktree_clean,
        "result": result,
        "blocking_reasons": reasons,
        "approvals": [],
        "certificate_content_hash": "",
    }
    hash_input = dict(cert)
    hash_input["certificate_content_hash"] = ""
    cert["certificate_content_hash"] = hashlib.sha256(json.dumps(hash_input, sort_keys=True).encode("utf-8")).hexdigest()
    out = root / "artifacts" / "release-baseline" / "certificates" / args.product / f"{cert['certificate_id']}.json"
    dump_json(out, cert)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
