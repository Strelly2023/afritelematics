from __future__ import annotations


def parse_class_diagram(source: str) -> dict[str, object]:
    classes: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("-") and current is not None:
            current["attributes"].append(line[1:].strip())
        elif line.startswith("+") and current is not None:
            current["methods"].append(line[1:].strip())
        elif "->" not in line and ":" not in line:
            current = {"name": line, "attributes": [], "methods": []}
            classes.append(current)
    return {
        "diagram_type": "class",
        "classes": tuple(classes),
        "authority": "design_time_non_authoritative",
        "runtime_mutation_allowed": False,
    }


__all__ = ["parse_class_diagram"]
