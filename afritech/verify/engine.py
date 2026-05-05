from __future__ import annotations

"""
AfriTech Constitutional Replay Engine
=====================================

Machine-checkable replay verification of AfriTech constitutional history.

This module:
- Reads epoch history, registry state, and ADR metadata
- Verifies lawful derivation of the terminal state
- Performs NO writes and NO enforcement
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List
import yaml


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_FILE = ROOT / "registry" / "registry.yaml"
EPOCH_HISTORY_DIR = ROOT / "registry" / "history"
ADR_DIR = ROOT / "adr"


# ---------------------------------------------------------------------
# Replay result model
# ---------------------------------------------------------------------

@dataclass
class ReplayResult:
    valid: bool
    terminal_epoch: int | None
    violations: List[str]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_epochs() -> List[dict]:
    epoch_files = sorted(EPOCH_HISTORY_DIR.glob("epoch_*.yaml"))
    if not epoch_files:
        raise ValueError("No epoch history found")

    epochs: List[dict] = []
    for path in epoch_files:
        data = _load_yaml(path)
        if "epoch" not in data or "number" not in data["epoch"]:
            raise ValueError(f"Invalid epoch file structure: {path}")
        epochs.append(data)
    return epochs


# ---------------------------------------------------------------------
# Core verification
# ---------------------------------------------------------------------

def verify_replay() -> ReplayResult:
    """
    Verify constitutional replay validity.

    Returns:
        ReplayResult(valid, terminal_epoch, violations)
    """
    violations: List[str] = []

    # Load artifacts
    try:
        epochs = _load_epochs()
        registry = _load_yaml(REGISTRY_FILE)
    except Exception as exc:
        return ReplayResult(False, None, [str(exc)])

    # -----------------------------------------------------------------
    # Epoch continuity & monotonicity
    # -----------------------------------------------------------------

    for i in range(1, len(epochs)):
        prev_num = epochs[i - 1]["epoch"]["number"]
        curr_num = epochs[i]["epoch"]["number"]
        parent = epochs[i]["epoch"].get("parent")

        if curr_num != prev_num + 1:
            violations.append(
                f"Epoch monotonicity violated: {prev_num} → {curr_num}"
            )

        if parent != prev_num:
            violations.append(
                f"Epoch parent mismatch at epoch {curr_num}: "
                f"parent={parent}, expected={prev_num}"
            )

    # -----------------------------------------------------------------
    # Seal continuity (finalized epochs must end SEALED)
    # -----------------------------------------------------------------

    for e in epochs:
        num = e["epoch"]["number"]
        sealing = e.get("sealing", {})

        if sealing.get("resealed") is not True:
            violations.append(f"Epoch {num} not resealed")

        if sealing.get("seal_status") != "SEALED":
            violations.append(f"Epoch {num} seal_status is not SEALED")

    # -----------------------------------------------------------------
    # Registry ↔ terminal epoch agreement
    # -----------------------------------------------------------------

    registry_epoch = registry.get("epoch", {}).get("current")
    terminal_epoch = epochs[-1]["epoch"]["number"]

    if registry_epoch != terminal_epoch:
        violations.append(
            f"Registry current epoch {registry_epoch} "
            f"does not match terminal replay epoch {terminal_epoch}"
        )

    # -----------------------------------------------------------------
    # ADR legitimacy (each advancement must reference an existing ADR)
    # -----------------------------------------------------------------

    for e in epochs[1:]:  # epoch 0 has no parent to authorize
        num = e["epoch"]["number"]
        adr = e.get("epoch", {}).get("authority", {}).get("adr")

        if not adr:
            violations.append(f"Epoch {num} missing ADR authority")
            continue

        adr_path = ADR_DIR / f"{adr}.md"
        if not adr_path.exists():
            violations.append(
                f"Epoch {num} references missing ADR '{adr}'"
            )

    # -----------------------------------------------------------------
    # Final result
    # -----------------------------------------------------------------

    if violations:
        return ReplayResult(False, terminal_epoch, violations)

    return ReplayResult(True, terminal_epoch, [])