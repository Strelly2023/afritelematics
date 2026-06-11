from __future__ import annotations


def parse_sequence_diagram(source: str) -> dict[str, object]:
    interactions: list[dict[str, str]] = []
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if "->" not in line:
            continue
        left, right = line.split("->", 1)
        target, _, message = right.partition(":")
        interactions.append(
            {
                "from": left.strip(),
                "to": target.strip(),
                "message": message.strip(),
            }
        )
    return {
        "diagram_type": "sequence",
        "interactions": tuple(interactions),
        "authority": "design_time_non_authoritative",
        "runtime_mutation_allowed": False,
    }


__all__ = ["parse_sequence_diagram"]
