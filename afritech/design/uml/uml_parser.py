from __future__ import annotations

from afritech.design.uml.activity_diagram import parse_activity_diagram
from afritech.design.uml.class_diagram import parse_class_diagram
from afritech.design.uml.sequence_diagram import parse_sequence_diagram
from afritech.design.uml.state_diagram import parse_state_diagram


def parse_uml(source: str, *, diagram_type: str) -> dict[str, object]:
    if diagram_type == "class":
        return parse_class_diagram(source)
    if diagram_type == "sequence":
        return parse_sequence_diagram(source)
    if diagram_type == "activity":
        return parse_activity_diagram(source)
    if diagram_type == "state":
        return parse_state_diagram(source)
    raise ValueError(f"unsupported UML diagram type: {diagram_type}")


__all__ = ["parse_uml"]
