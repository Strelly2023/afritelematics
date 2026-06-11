from __future__ import annotations


def parse_state_diagram(source: str) -> dict[str, object]:
    transitions: list[dict[str, str]] = []
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if "->" not in line:
            continue
        left, right = line.split("->", 1)
        transitions.append({"from": left.strip(), "to": right.strip()})
    return {
        "diagram_type": "state",
        "transitions": tuple(transitions),
        "authority": "design_time_non_authoritative",
        "runtime_mutation_allowed": False,
    }


__all__ = ["parse_state_diagram"]
