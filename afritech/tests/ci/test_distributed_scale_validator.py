"""
afritech.tests.ci.test_distributed_scale_validator

Tests for distributed scale CI validators.
"""

from __future__ import annotations

from pathlib import Path
import copy

import pytest
import yaml

from afritech.ci.distributed_partition_validator import (
    validate_distributed_partitions,
)
from afritech.ci.distributed_recovery_validator import (
    validate_distributed_recovery,
)
from afritech.ci.distributed_replay_validator import (
    validate_distributed_replay,
)
from afritech.ci.distributed_scale_validator import (
    DistributedScaleValidatorError,
    validate_distributed_scale,
    validate_scale_contract_file,
)
from afritech.ci.distributed_transcript_validator import (
    validate_distributed_transcripts,
)
from afritech.ci.distributed_worker_validator import (
    validate_distributed_workers,
)


SCALE_CONTRACT_PATH = Path("afritech/distributed/contracts/scale_contract.yaml")


# ============================================================
# SUCCESS CASES
# ============================================================

def test_distributed_scale_contract_validates():
    result = validate_distributed_scale()

    assert result.passed is True
    assert result.checked_contracts == 1
    assert result.failures == ()


def test_distributed_partition_validator_passes():
    result = validate_distributed_partitions()

    assert result.passed is True
    assert result.checked_partitions > 0
    assert result.checked_assignments > 0
    assert result.failures == ()


def test_distributed_worker_validator_passes():
    result = validate_distributed_workers()

    assert result.passed is True
    assert result.checked_workers > 0
    assert result.checked_records > 0
    assert result.failures == ()


def test_distributed_replay_validator_passes():
    result = validate_distributed_replay()

    assert result.passed is True
    assert result.checked_records > 0
    assert result.checked_results > 0
    assert result.failures == ()


def test_distributed_recovery_validator_passes():
    result = validate_distributed_recovery()

    assert result.passed is True
    assert result.checked_recoveries > 0
    assert result.failures == ()


def test_distributed_transcript_validator_is_safe_without_evidence_files():
    result = validate_distributed_transcripts()

    assert result.passed is True
    assert result.checked_transcripts >= 0
    assert result.failures == ()


def test_scale_contract_file_exists():
    assert SCALE_CONTRACT_PATH.exists()
    assert SCALE_CONTRACT_PATH.is_file()


# ============================================================
# FAILURE CASES (STRICT)
# ============================================================

def test_scale_contract_rejects_missing_top_level_key(tmp_path):
    data = _load_scale_contract()
    data.pop("distributed_scale_contract")

    path = _write_tmp(tmp_path, data)

    with pytest.raises(DistributedScaleValidatorError):
        validate_scale_contract_file(path)


def test_scale_contract_rejects_wrong_schema(tmp_path):
    data = _load_scale_contract()
    data["schema"] = "bad.schema"

    path = _write_tmp(tmp_path, data)

    with pytest.raises(DistributedScaleValidatorError):
        validate_scale_contract_file(path)


def test_scale_contract_rejects_wrong_authority(tmp_path):
    data = _load_scale_contract()
    data["metadata"]["authority"] = "ARCHITECTURE"

    path = _write_tmp(tmp_path, data)

    with pytest.raises(DistributedScaleValidatorError):
        validate_scale_contract_file(path)


def test_scale_contract_rejects_missing_forbidden_truth_bypass(tmp_path):
    data = _load_scale_contract()

    forbidden = list(data["distributed_scale_contract"]["forbidden"])
    forbidden.remove("bypass_replay")
    data["distributed_scale_contract"]["forbidden"] = forbidden

    path = _write_tmp(tmp_path, data)

    with pytest.raises(DistributedScaleValidatorError):
        validate_scale_contract_file(path)


def test_scale_contract_rejects_role_forbidden_overlap(tmp_path):
    data = _load_scale_contract()

    role = list(data["distributed_scale_contract"]["role"])
    role.append("bypass_replay")
    data["distributed_scale_contract"]["role"] = role

    path = _write_tmp(tmp_path, data)

    with pytest.raises(DistributedScaleValidatorError):
        validate_scale_contract_file(path)


def test_scale_contract_rejects_required_forbidden_overlap(tmp_path):
    data = _load_scale_contract()

    required = list(data["distributed_scale_contract"]["required"])
    required.append("bypass_replay")
    data["distributed_scale_contract"]["required"] = required

    path = _write_tmp(tmp_path, data)

    with pytest.raises(DistributedScaleValidatorError):
        validate_scale_contract_file(path)


def test_scale_contract_requires_worker_registration(tmp_path):
    data = _load_scale_contract()

    required = list(data["distributed_scale_contract"]["required"])
    required.remove("explicit_worker_registration")
    data["distributed_scale_contract"]["required"] = required

    path = _write_tmp(tmp_path, data)

    with pytest.raises(DistributedScaleValidatorError):
        validate_scale_contract_file(path)


def test_scale_contract_requires_ci_fail_mode(tmp_path):
    data = _load_scale_contract()
    data["ci_enforcement"]["failure_mode"] = "WARN_ONLY"

    path = _write_tmp(tmp_path, data)

    with pytest.raises(DistributedScaleValidatorError):
        validate_scale_contract_file(path)


def test_scale_contract_rejects_missing_distributed_validator(tmp_path):
    data = _load_scale_contract()

    validators = list(data["ci_enforcement"]["validators"])
    validators.remove("distributed_replay_validator")
    data["ci_enforcement"]["validators"] = validators

    path = _write_tmp(tmp_path, data)

    with pytest.raises(DistributedScaleValidatorError):
        validate_scale_contract_file(path)


def test_scale_contract_rejects_coordinator_truth_authority(tmp_path):
    data = _load_scale_contract()
    data["coordinator_semantics"]["authority"]["truth_authority"] = True

    path = _write_tmp(tmp_path, data)

    with pytest.raises(DistributedScaleValidatorError):
        validate_scale_contract_file(path)


def test_scale_contract_rejects_non_deterministic_partition_routing(tmp_path):
    data = _load_scale_contract()
    data["partition_semantics"]["routing"]["deterministic"] = False

    path = _write_tmp(tmp_path, data)

    with pytest.raises(DistributedScaleValidatorError):
        validate_scale_contract_file(path)


def test_scale_contract_rejects_non_replay_safe_worker_execution(tmp_path):
    data = _load_scale_contract()
    data["worker_semantics"]["execution"]["replay_equivalence_required"] = False

    path = _write_tmp(tmp_path, data)

    with pytest.raises(DistributedScaleValidatorError):
        validate_scale_contract_file(path)


# ============================================================
# HELPERS ✅ HARDENED
# ============================================================

def _load_scale_contract() -> dict[str, object]:
    return copy.deepcopy(
        yaml.safe_load(SCALE_CONTRACT_PATH.read_text(encoding="utf-8"))
    )


def _write_tmp(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "contract.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path
