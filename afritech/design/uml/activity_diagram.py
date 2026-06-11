from __future__ import annotations


def parse_activity_diagram(source: str) -> dict[str, object]:
    steps = tuple(
        part.strip()
        for line in source.splitlines()
        for part in line.split("->")
        if part.strip()
    )
    return {
        "diagram_type": "activity",
        "steps": steps,
        "authority": "design_time_non_authoritative",
        "runtime_mutation_allowed": False,
    }


__all__ = ["parse_activity_diagram"]
