"""UML design layer for non-authoritative AfriProgramming proposals."""

from afritech.design.uml.activity_diagram import parse_activity_diagram
from afritech.design.uml.class_diagram import parse_class_diagram
from afritech.design.uml.sequence_diagram import parse_sequence_diagram
from afritech.design.uml.state_diagram import parse_state_diagram
from afritech.design.uml.uml_parser import parse_uml
from afritech.design.uml.uml_to_proposal import uml_to_proposal
from afritech.design.uml.uml_validators import validate_uml_design

__all__ = [
    "parse_activity_diagram",
    "parse_class_diagram",
    "parse_sequence_diagram",
    "parse_state_diagram",
    "parse_uml",
    "uml_to_proposal",
    "validate_uml_design",
]
