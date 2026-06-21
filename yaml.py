"""Repo-local YAML shim for environments without PyYAML.

This module provides the small subset of the PyYAML API used by the AfriTech
tooling and commit hooks. It prefers JSON-compatible round-trips for dumping
and uses the bounded YAML-like parser already present in the architecture
config loader for repo-authored config files.
"""

from __future__ import annotations

import json
import importlib.machinery
import importlib.util
from pathlib import Path
import sys
from typing import Any, Iterable

_REAL_YAML = None
_THIS_DIR = str(Path(__file__).resolve().parent)

for _entry in [entry for entry in sys.path if entry not in {"", _THIS_DIR}]:
    _spec = importlib.machinery.PathFinder.find_spec("yaml", [_entry])
    if _spec and _spec.origin and _spec.origin != __file__:
        _real_spec = importlib.util.spec_from_file_location(
            "pyyaml_real",
            _spec.origin,
            submodule_search_locations=_spec.submodule_search_locations,
        )
        if _real_spec and _real_spec.loader is not None:
            _module = importlib.util.module_from_spec(_real_spec)
            sys.modules[_real_spec.name] = _module
            _real_spec.loader.exec_module(_module)
            _REAL_YAML = _module
        break


class YAMLError(Exception):
    """Fallback YAML parse/dump error."""


def _coerce_stream(stream: Any) -> str:
    if hasattr(stream, "read"):
        text = stream.read()
    else:
        text = stream
    if text is None:
        return ""
    if isinstance(text, bytes):
        return text.decode("utf-8")
    return str(text)


def _coerce_scalar(value: str) -> object:
    text = value.strip()
    if text == "":
        return ""
    if text in {"null", "Null", "NULL", "~"}:
        return None
    if text in {"true", "True"}:
        return True
    if text in {"false", "False"}:
        return False
    if text.isdigit():
        return int(text)
    try:
        if "." in text:
            return float(text)
    except Exception:
        pass
    if (
        (text.startswith('"') and text.endswith('"'))
        or (text.startswith("'") and text.endswith("'"))
    ):
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_coerce_scalar(item) for item in _split_comma(inner)]
    if text.startswith("{") and text.endswith("}"):
        return _parse_inline_mapping(text[1:-1])
    return text


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _preprocess(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        lines.append(raw_line.rstrip())
    return lines


def _split_comma(text: str) -> list[str]:
    parts: list[str] = []
    current = []
    depth = 0
    quote: str | None = None
    for char in text:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
            continue
        if char in "[{(":
            depth += 1
        elif char in "]})" and depth > 0:
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_inline_mapping(text: str) -> dict[str, object]:
    mapping: dict[str, object] = {}
    if not text.strip():
        return mapping
    for item in _split_comma(text):
        if ":" not in item:
            raise YAMLError(f"invalid inline mapping item: {item}")
        key, value = item.split(":", 1)
        mapping[key.strip()] = _coerce_scalar(value)
    return mapping


def _next_significant_indent(lines: list[str], index: int) -> int | None:
    while index < len(lines):
        line = lines[index]
        if line.lstrip().startswith("#") or not line.strip():
            index += 1
            continue
        return _indent_of(line)
    return None


def _parse_block(lines: list[str], index: int, indent: int) -> tuple[object, int]:
    if index >= len(lines):
        return {}, index

    is_list = lines[index].lstrip().startswith("- ")
    if is_list:
        result: list[object] = []
        while index < len(lines):
            line = lines[index]
            current_indent = _indent_of(line)
            if current_indent < indent or not line.lstrip().startswith("- "):
                break
            if current_indent != indent:
                raise YAMLError("invalid list indentation in yaml-like config")
            content = line.strip()[2:].strip()
            index += 1

            if content in {"|", ">"}:
                collected: list[str] = []
                next_indent = _next_significant_indent(lines, index)
                block_indent = next_indent if next_indent is not None and next_indent > indent else indent + 2
                while index < len(lines):
                    next_line = lines[index]
                    next_line_indent = _indent_of(next_line)
                    if next_line_indent < block_indent:
                        break
                    collected.append(next_line[block_indent:] if len(next_line) >= block_indent else "")
                    index += 1
                result.append("\n".join(collected).rstrip())
                continue

            if content == "":
                next_indent = _next_significant_indent(lines, index)
                child_indent = next_indent if next_indent is not None and next_indent >= indent else indent + 2
                child, index = _parse_block(lines, index, child_indent)
                result.append(child)
                continue

            if ":" in content:
                key, value = content.split(":", 1)
                item: dict[str, object] = {key.strip(): _coerce_scalar(value)}
                while index < len(lines):
                    next_line = lines[index]
                    next_indent = _indent_of(next_line)
                    if next_indent <= indent:
                        break
                    if next_line.lstrip().startswith("#"):
                        index += 1
                        continue
                    if next_line.lstrip().startswith("- ") and next_indent == indent + 2:
                        child, index = _parse_block(lines, index, next_indent)
                        existing = item.get(key.strip())
                        if existing in {"", None}:
                            item[key.strip()] = child
                        else:
                            item.setdefault("_items", child)
                        break
                    if ":" in next_line.strip():
                        nested_key, nested_value = next_line.strip().split(":", 1)
                        index += 1
                        if nested_value.strip() in {"|", ">"}:
                            collected: list[str] = []
                            next_scalar_indent = _next_significant_indent(lines, index)
                            block_indent = (
                                next_scalar_indent
                                if next_scalar_indent is not None and next_scalar_indent > next_indent
                                else next_indent + 2
                            )
                            while index < len(lines):
                                scalar_line = lines[index]
                                scalar_indent = _indent_of(scalar_line)
                                if scalar_indent < block_indent:
                                    break
                                collected.append(
                                    scalar_line[block_indent:]
                                    if len(scalar_line) >= block_indent
                                    else ""
                                )
                                index += 1
                            item[nested_key.strip()] = "\n".join(collected).rstrip()
                        elif nested_value.strip() == "":
                            next_child_indent = _next_significant_indent(lines, index)
                            child_indent = next_child_indent if next_child_indent is not None and next_child_indent > next_indent else next_indent + 2
                            child, index = _parse_block(lines, index, child_indent)
                            item[nested_key.strip()] = child
                        else:
                            item[nested_key.strip()] = _coerce_scalar(nested_value)
                        continue
                    child, index = _parse_block(lines, index, next_indent)
                    item.setdefault("_children", child)
                    break
                result.append(item)
                continue

            result.append(_coerce_scalar(content))
        return result, index

    result_dict: dict[str, object] = {}
    while index < len(lines):
        line = lines[index]
        current_indent = _indent_of(line)
        if current_indent < indent:
            break
        if current_indent != indent:
            raise YAMLError("invalid mapping indentation in yaml-like config")
        if line.lstrip().startswith("- "):
            break

        key, value = line.strip().split(":", 1)
        index += 1

        if value.strip() in {"|", ">"}:
            collected: list[str] = []
            next_indent = _next_significant_indent(lines, index)
            block_indent = next_indent if next_indent is not None and next_indent > indent else indent + 2
            while index < len(lines):
                next_line = lines[index]
                next_line_indent = _indent_of(next_line)
                if next_line_indent < block_indent:
                    break
                collected.append(next_line[block_indent:] if len(next_line) >= block_indent else "")
                index += 1
            result_dict[key.strip()] = "\n".join(collected).rstrip()
            continue

        if value.strip() == "":
            next_indent = _next_significant_indent(lines, index)
            child_indent = next_indent if next_indent is not None and next_indent >= indent else indent + 2
            child, index = _parse_block(lines, index, child_indent)
            result_dict[key.strip()] = child
        else:
            result_dict[key.strip()] = _coerce_scalar(value)
    return result_dict, index


def safe_load(stream: Any) -> Any:
    text = _coerce_stream(stream).strip()
    if not text:
        return None

    if _REAL_YAML is not None:
        return _REAL_YAML.safe_load(text)

    try:
        return json.loads(text)
    except Exception:
        pass

    try:
        lines = _preprocess(text)
        payload, _ = _parse_block(lines, 0, 0)
        return payload
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise YAMLError(str(exc)) from exc


def safe_dump(data: Any, stream: Any = None, sort_keys: bool = True, **_: Any) -> str:
    if _REAL_YAML is not None:
        text = _REAL_YAML.safe_dump(data, sort_keys=sort_keys)
    else:
        text = json.dumps(data, indent=2, sort_keys=sort_keys, ensure_ascii=False)
    if stream is not None and hasattr(stream, "write"):
        stream.write(text)
    return text


def dump(data: Any, *args: Any, **kwargs: Any) -> str:
    return safe_dump(data, *args, **kwargs)


def load(stream: Any) -> Any:
    return safe_load(stream)


def safe_load_all(stream: Any):  # pragma: no cover - unused by hooks, provided for compatibility
    yield safe_load(stream)


def dump_all(documents: Any, *args: Any, **kwargs: Any) -> str:  # pragma: no cover - compatibility
    return safe_dump(documents, *args, **kwargs)


__all__ = [
    "YAMLError",
    "dump",
    "dump_all",
    "load",
    "safe_dump",
    "safe_load",
    "safe_load_all",
]
