from __future__ import annotations

from pathlib import Path

import pytest

from afritech.extensions.afriprog.code_executor.ast_editor import ASTEditor
from afritech.extensions.afriprog.code_executor.diff_model import Diff
from afritech.extensions.afriprog.code_executor.executor_preview import (
    PatchPreviewExecutor,
    run_patch_preview,
)
from afritech.extensions.afriprog.code_executor.patch_generator import PatchGenerator
from afritech.extensions.afriprog.code_executor.patch_model import Patch
from afritech.extensions.afriprog.code_executor.safe_write import (
    SafeWriteDisabledError,
    safe_delete,
    safe_rename,
    safe_write,
    write_status,
)
from afritech.extensions.afriprog.code_executor.sandbox import (
    SandboxError,
    validate_path,
)
from afritech.extensions.afriprog.task_planner.task_model import Task
from afritech.extensions.afriprog.task_planner.task_types import RiskLevel, TaskType


def test_patch_model_is_proposal_only_and_hashes_are_stable():
    patch = Patch(
        file_path="afritech/extensions/afriprog/code_executor/example.py",
        original_content="a = 1\n",
        updated_content="a = 2\n",
    )

    data = patch.canonical_dict()

    assert data["write_permitted"] is False
    assert data["changed"] is True
    assert len(data["patch_hash"]) == 64


def test_diff_model_detects_empty_and_changed_diff():
    empty = Diff(
        file_path="afritech/extensions/afriprog/code_executor/example.py",
        diff_text="",
    )
    changed = Diff(
        file_path="afritech/extensions/afriprog/code_executor/example.py",
        diff_text="-a\n+b",
    )

    assert empty.is_empty is True
    assert changed.changed is True
    assert len(changed.diff_hash) == 64


def test_sandbox_allows_extensions_and_rejects_core_paths():
    allowed = validate_path(
        "afritech/extensions/afriprog/code_executor/patch_model.py"
    )

    assert allowed == "afritech/extensions/afriprog/code_executor/patch_model.py"

    with pytest.raises(SandboxError):
        validate_path("afritech/runtime/replay.py")

    with pytest.raises(SandboxError):
        validate_path("../afritech/extensions/escape.py")

    with pytest.raises(SandboxError):
        validate_path("afritech/extensions_evil/escape.py")


def test_ast_editor_inspects_python_and_insert_is_idempotent():
    editor = ASTEditor()

    content = """
import os

class Example:
    pass

def run():
    return True
"""

    summary = editor.inspect_python(content)

    assert summary.classes == ("Example",)
    assert summary.functions == ("run",)
    assert "os" in summary.imports

    inserted = editor.insert_text(content, "# Proposal")
    inserted_again = editor.insert_text(inserted, "# Proposal")

    assert inserted == inserted_again


def test_safe_write_surface_is_disabled():
    with pytest.raises(SafeWriteDisabledError):
        safe_write(
            "afritech/extensions/afriprog/code_executor/example.py",
            "content",
        )

    with pytest.raises(SafeWriteDisabledError):
        safe_delete(
            "afritech/extensions/afriprog/code_executor/example.py"
        )

    with pytest.raises(SafeWriteDisabledError):
        safe_rename(
            "afritech/extensions/afriprog/code_executor/a.py",
            "afritech/extensions/afriprog/code_executor/b.py",
        )

    status = write_status()

    assert status["write_enabled"] is False
    assert status["status"] == "proposal_only"


def test_patch_generator_creates_missing_element_proposal(tmp_path: Path):
    repo_file = Path("afritech/extensions/afriprog/code_executor/tmp_test_file.py")
    repo_file.write_text("VALUE = 1\n", encoding="utf-8")

    try:
        task = Task(
            task_id="TASK-0001",
            task_type=TaskType.MISSING_ELEMENT.value,
            description="Missing element",
            target_files=(str(repo_file),),
            risk_level=RiskLevel.LOW.value,
            requires_write=False,
            source_tests=(),
        )

        patch = PatchGenerator().generate_patch(task)

        assert patch is not None
        assert patch.write_permitted is False
        assert patch.changed is True
        assert "AfriProgramming Proposal" in patch.updated_content

    finally:
        repo_file.unlink(missing_ok=True)


def test_patch_generator_rejects_core_target_path():
    task = Task(
        task_id="TASK-0001",
        task_type=TaskType.MISSING_ELEMENT.value,
        description="Missing element",
        target_files=("afritech/runtime/replay.py",),
        risk_level=RiskLevel.LOW.value,
        requires_write=False,
        source_tests=(),
    )

    assert PatchGenerator().generate_patch(task) is None


def test_executor_preview_generates_diff_for_extension_file(tmp_path: Path):
    target = Path("afritech/extensions/afriprog/code_executor/tmp_preview.py")
    target.write_text("VALUE = 1\n", encoding="utf-8")

    try:
        result = run_patch_preview(
            failure_text="ImportError: cannot import name MissingElement",
            root=".",
            candidate_files=(str(target),),
        )

        data = result.canonical_dict()

        assert data["mode"] == "PHASE_3_PATCH_PROPOSAL_ONLY"
        assert data["write_enabled"] is False
        assert data["patch_applied"] is False
        assert data["patch"] is not None
        assert data["diff"] is not None

    finally:
        target.unlink(missing_ok=True)


def test_executor_preview_default_candidates_are_repo_relative():
    result = run_patch_preview(
        failure_text="ImportError: cannot import name MissingElement",
        root=".",
    )

    data = result.canonical_dict()

    assert data["patch"] is not None
    assert data["diff"] is not None
    assert data["patch"]["file_path"].startswith("afritech/extensions/afriprog/")


def test_executor_preview_rejects_missing_root(tmp_path: Path):
    with pytest.raises(Exception):
        PatchPreviewExecutor(root=tmp_path / "missing")
