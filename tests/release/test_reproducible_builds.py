from __future__ import annotations

from pathlib import Path

from scripts.release.verify_reproducible_builds import compare_hash_trees, hash_tree


def test_compare_hash_trees_reports_identical_files(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "a.txt").write_text("hello", encoding="utf-8")
    (right / "a.txt").write_text("hello", encoding="utf-8")
    (left / "nested").mkdir()
    (right / "nested").mkdir()
    (left / "nested" / "b.txt").write_text("world", encoding="utf-8")
    (right / "nested" / "b.txt").write_text("world", encoding="utf-8")

    result = compare_hash_trees(hash_tree(left), hash_tree(right))

    assert result["status"] == "IDENTICAL"
    assert result["identical_files"] == 2
    assert result["differing_files"] == []
    assert result["missing_files"] == []
    assert result["extra_files"] == []


def test_compare_hash_trees_detects_drift(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "a.txt").write_text("hello", encoding="utf-8")
    (right / "a.txt").write_text("HELLO", encoding="utf-8")

    result = compare_hash_trees(hash_tree(left), hash_tree(right))

    assert result["status"] == "DIFFERENT"
    assert len(result["differing_files"]) == 1
