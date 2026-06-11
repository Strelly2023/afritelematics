from __future__ import annotations

from afritech.design.solid import solid_design_from_uml, validate_solid_design


def validate_uml_design(model: dict[str, object]) -> dict[str, object]:
    violations: list[str] = []
    diagram_type = model.get("diagram_type")
    if diagram_type not in {"class", "sequence", "activity", "state"}:
        violations.append("unsupported diagram type")
    if model.get("authority") != "design_time_non_authoritative":
        violations.append("UML model gained authority")
    if model.get("runtime_mutation_allowed") is not False:
        violations.append("UML model may mutate runtime")
    if diagram_type == "class" and not model.get("classes"):
        violations.append("class diagram must define at least one class")
    if diagram_type == "sequence" and not model.get("interactions"):
        violations.append("sequence diagram must define interactions")
    if diagram_type == "activity" and not model.get("steps"):
        violations.append("activity diagram must define steps")
    if diagram_type == "state" and not model.get("transitions"):
        violations.append("state diagram must define transitions")
    solid_validation = validate_solid_design(solid_design_from_uml(model))
    if solid_validation["valid"] is not True:
        violations.extend(f"SOLID: {violation}" for violation in solid_validation["violations"])
    return {
        "valid": not violations,
        "violations": tuple(violations),
        "solid_validation": solid_validation,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
        "governance_required": True,
    }


__all__ = ["validate_uml_design"]
