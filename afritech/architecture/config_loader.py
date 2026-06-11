"""Small YAML-like loader for governed architecture config files.

The repo may run in environments without PyYAML, so this loader supports the
bounded subset of YAML used by dashboard registry and navigation config files.
"""

from __future__ import annotations

from pathlib import Path


def _coerce_scalar(value: str) -> object:
    text = value.strip()
    if text == "":
        return ""
    if text in {"true", "True"}:
        return True
    if text in {"false", "False"}:
        return False
    if text.isdigit():
        return int(text)
    if (
        (text.startswith('"') and text.endswith('"'))
        or (text.startswith("'") and text.endswith("'"))
    ):
        return text[1:-1]
    return text


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _preprocess(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        if raw_line.lstrip().startswith("#"):
            continue
        lines.append(raw_line.rstrip())
    return lines


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
                raise RuntimeError("invalid list indentation in yaml-like config")
            content = line.strip()[2:].strip()
            index += 1

            if content == "":
                child, index = _parse_block(lines, index, indent + 2)
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
                    if next_indent == indent + 2 and not next_line.lstrip().startswith("- "):
                        nested_key, nested_value = next_line.strip().split(":", 1)
                        index += 1
                        if nested_value.strip() == "":
                            child, index = _parse_block(lines, index, indent + 4)
                            item[nested_key.strip()] = child
                        else:
                            item[nested_key.strip()] = _coerce_scalar(nested_value)
                        continue
                    if next_indent == indent + 2 and next_line.lstrip().startswith("- "):
                        child, index = _parse_block(lines, index, indent + 2)
                        existing = item.get(key.strip())
                        if existing in {"", None}:
                            item[key.strip()] = child
                        else:
                            item.setdefault("_items", child)
                        break
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
            raise RuntimeError("invalid mapping indentation in yaml-like config")
        if line.lstrip().startswith("- "):
            break
        key, value = line.strip().split(":", 1)
        index += 1
        if value.strip() == "":
            child, index = _parse_block(lines, index, indent + 2)
            result_dict[key.strip()] = child
        else:
            result_dict[key.strip()] = _coerce_scalar(value)
    return result_dict, index


def load_yaml_like(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        payload = yaml.safe_load(text)
        if not isinstance(payload, dict):
            raise RuntimeError("yaml payload must decode to a mapping")
        return payload
    except ModuleNotFoundError:
        lines = _preprocess(text)
        payload, _ = _parse_block(lines, 0, 0)
        if not isinstance(payload, dict):
            raise RuntimeError("yaml-like payload must decode to a mapping")
        return payload


__all__ = ["load_yaml_like"]
