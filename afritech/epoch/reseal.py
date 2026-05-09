# afritech/epoch/reseal.py

"""
AfriTech Epoch Reseal Engine

Purpose:
Recompute and seal epoch hash chain after mutation.

Guarantees:
- deterministic hashing
- immutable sealed state
- chain continuity
- replay compatibility

All failures → engine.fail()
"""

from __future__ import annotations

import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List

from afritech.guards.engine import fail, ViolationClass


# -----------------------------------------------------------------
# HASH UTIL (STRICTLY DETERMINISTIC)
# -----------------------------------------------------------------

def _compute_epoch_hash(epoch_record: Dict[str, Any]) -> str:
    """
    Deterministic SHA256 hash of epoch.
    Excludes hash_chain and uses canonical YAML.
    """

    data = dict(epoch_record)
    data.pop("hash_chain", None)

    encoded = yaml.dump(
        data,
        sort_keys=True,
        allow_unicode=True,
        default_flow_style=False,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


# -----------------------------------------------------------------
# YAML UTILITIES
# -----------------------------------------------------------------

def _load_yaml(path: Path) -> Dict[str, Any]:

    if not path.exists():
        fail(f"epoch_file_not_found:{path}", ViolationClass.B_STRUCTURAL)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception:
        fail("yaml_parse_error", ViolationClass.B_STRUCTURAL)

    if not isinstance(data, dict):
        fail("invalid_yaml_structure", ViolationClass.B_STRUCTURAL)

    return data


def _save_yaml(path: Path, data: Dict[str, Any]):

    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                sort_keys=False,
                allow_unicode=True,
                default_flow_style=False,
            )
    except Exception:
        fail("yaml_write_error", ViolationClass.B_STRUCTURAL)


# -----------------------------------------------------------------
# VALIDATION HELPERS
# -----------------------------------------------------------------

def _require_fields(data: Dict[str, Any], fields: List[str]):

    for field in fields:
        if field not in data:
            fail(f"missing_epoch_field:{field}", ViolationClass.B_STRUCTURAL)


def _get_epoch_files(history_dir: Path) -> List[Path]:

    files = list(history_dir.glob("epoch_*.yaml"))

    if not files:
        fail("no_epoch_files_found", ViolationClass.A_FATAL)

    try:
        files.sort(key=lambda p: int(p.stem.split("_")[1]))
    except Exception:
        fail("invalid_epoch_filename_structure", ViolationClass.B_STRUCTURAL)

    return files


# -----------------------------------------------------------------
# MAIN RESEAL FUNCTION
# -----------------------------------------------------------------

def reseal_epoch(history_dir: Path, epoch_filename: str) -> bool:
    """
    Reseal a single epoch file.
    """

    epoch_path = history_dir / epoch_filename
    epoch_data = _load_yaml(epoch_path)

    # -------------------------------------------------------------
    # STRUCTURAL VALIDATION
    # -------------------------------------------------------------

    _require_fields(epoch_data, ["epoch_id", "version"])

    version = epoch_data["version"]

    if not isinstance(version, int) or version < 0:
        fail("invalid_epoch_version", ViolationClass.B_STRUCTURAL)

    # -------------------------------------------------------------
    # PREVIOUS HASH (FIXED BUG)
    # -------------------------------------------------------------

    if version == 0:
        previous_hash = "GENESIS"
    else:
        prev_path = history_dir / f"epoch_{version - 1}.yaml"
        prev_data = _load_yaml(prev_path)

        previous_hash = (
            prev_data.get("hash_chain", {})
            .get("epoch_hash")
        )

        if not previous_hash:
            fail(
                f"missing_previous_epoch_hash:{version-1}",
                ViolationClass.A_FATAL,
            )

    # -------------------------------------------------------------
    # COMPUTE CURRENT HASH
    # -------------------------------------------------------------

    computed_hash = _compute_epoch_hash(epoch_data)

    # -------------------------------------------------------------
    # UPDATE HASH CHAIN
    # -------------------------------------------------------------

    epoch_data["hash_chain"] = {
        "previous_epoch_hash": previous_hash,
        "epoch_hash": computed_hash,
    }

    # -------------------------------------------------------------
    # ENFORCE SEALED + INACTIVE STATE (CRITICAL)
    # -------------------------------------------------------------

    epoch_data["sealed"] = True
    epoch_data["active"] = False

    # -------------------------------------------------------------
    # SYNCHRONIZE GOVERNANCE SEALING BLOCK
    # -------------------------------------------------------------

    if "epoch" in epoch_data:
        epoch_block = epoch_data["epoch"]
        sealing = epoch_block.get("sealing", {})

        sealing["seal_status"] = "SEALED"
        sealing["resealed"] = True

        epoch_block["sealing"] = sealing
        epoch_data["epoch"] = epoch_block

    # -------------------------------------------------------------
    # SAVE BACK
    # -------------------------------------------------------------

    _save_yaml(epoch_path, epoch_data)

    return True


# -----------------------------------------------------------------
# RESEAL FULL HISTORY
# -----------------------------------------------------------------

def reseal_all(history_dir: Path) -> bool:
    """
    Reseal entire epoch chain in strict order.
    """

    if not history_dir.exists():
        fail("history_directory_missing", ViolationClass.B_STRUCTURAL)

    for f in _get_epoch_files(history_dir):
        reseal_epoch(history_dir, f.name)

    return True


# -----------------------------------------------------------------
# VERIFY HASH CHAIN
# -----------------------------------------------------------------

def verify_hash_chain(history_dir: Path) -> bool:
    """
    Verify full epoch hash chain integrity.
    """

    files = _get_epoch_files(history_dir)

    previous_hash = None

    for f in files:
        data = _load_yaml(f)

        stored = data.get("hash_chain", {})
        current_hash = stored.get("epoch_hash")
        chain_prev = stored.get("previous_epoch_hash")

        if not current_hash:
            fail(f"missing_epoch_hash:{f.name}", ViolationClass.B_STRUCTURAL)

        recomputed = _compute_epoch_hash(data)

        if current_hash != recomputed:
            fail(f"epoch_hash_mismatch:{f.name}", ViolationClass.A_FATAL)

        if previous_hash is not None and chain_prev != previous_hash:
            fail(f"hash_chain_broken:{f.name}", ViolationClass.A_FATAL)

        previous_hash = current_hash

    return True
