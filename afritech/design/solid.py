from __future__ import annotations

SEVERITY_ORDER = {
    "INFO": 0,
    "MINOR": 1,
    "MAJOR": 2,
    "CRITICAL": 3,
}

PROTECTED_CORE_TARGETS = frozenset(
    {
        "constitution",
        "governance",
        "validators",
        "replay",
        "runtime",
        "contracts",
    }
)


def validate_solid_design(design: dict[str, object]) -> dict[str, object]:
    results = {
        "srp": validate_srp(design.get("modules", ())),
        "ocp": validate_ocp(design.get("change_targets", ())),
        "lsp": validate_lsp(design.get("inheritance", ())),
        "isp": validate_isp(design.get("interfaces", ())),
        "dip": validate_dip(design.get("dependencies", ())),
    }
    violations = tuple(
        violation
        for result in results.values()
        for violation in result["violations"]
    )
    findings = tuple(
        finding
        for result in results.values()
        for finding in result["findings"]
    )
    return {
        "valid": not violations,
        "principles": results,
        "violations": violations,
        "findings": findings,
        "max_severity": _max_severity(findings),
        "authority": "design_quality_non_authoritative",
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
        "governance_required": True,
    }


def validate_srp(modules: object) -> dict[str, object]:
    findings: list[dict[str, str]] = []
    for module in _as_sequence(modules):
        name = str(module.get("name", "unnamed"))
        responsibilities = _as_sequence(module.get("responsibilities", ()))
        if len(responsibilities) != 1:
            findings.append(
                _finding(
                    principle="SRP",
                    severity="MAJOR",
                    message=f"{name} must declare exactly one responsibility",
                )
            )
    return _result(findings)


def validate_ocp(change_targets: object) -> dict[str, object]:
    findings: list[dict[str, str]] = []
    for target in _as_sequence(change_targets):
        name = str(target.get("name", "unnamed"))
        target_type = str(target.get("type", ""))
        mode = str(target.get("mode", ""))
        if target_type in PROTECTED_CORE_TARGETS and mode != "extension":
            findings.append(
                _finding(
                    principle="OCP",
                    severity="CRITICAL",
                    message=f"{name} modifies protected {target_type} instead of extending it",
                )
            )
    return _result(findings)


def validate_lsp(inheritance: object) -> dict[str, object]:
    findings: list[dict[str, str]] = []
    for relation in _as_sequence(inheritance):
        child = str(relation.get("child", "child"))
        parent_behaviors = set(_as_sequence(relation.get("parent_behaviors", ())))
        child_behaviors = set(_as_sequence(relation.get("child_behaviors", ())))
        missing = sorted(parent_behaviors - child_behaviors)
        if missing:
            findings.append(
                _finding(
                    principle="LSP",
                    severity="MAJOR",
                    message=f"{child} does not preserve parent behavior: {', '.join(missing)}",
                )
            )
    return _result(findings)


def validate_isp(interfaces: object) -> dict[str, object]:
    findings: list[dict[str, str]] = []
    for interface in _as_sequence(interfaces):
        name = str(interface.get("name", "interface"))
        unused = _as_sequence(interface.get("unused_methods", ()))
        if unused:
            findings.append(
                _finding(
                    principle="ISP",
                    severity="MINOR",
                    message=f"{name} exposes unused methods: {', '.join(map(str, unused))}",
                )
            )
    return _result(findings)


def validate_dip(dependencies: object) -> dict[str, object]:
    findings: list[dict[str, str]] = []
    for dependency in _as_sequence(dependencies):
        consumer = str(dependency.get("consumer", "consumer"))
        dependency_type = str(dependency.get("dependency_type", ""))
        if dependency_type not in {"interface", "abstraction", "protocol"}:
            findings.append(
                _finding(
                    principle="DIP",
                    severity="MAJOR",
                    message=f"{consumer} depends on concrete dependency type: {dependency_type}",
                )
            )
    return _result(findings)


def solid_design_from_uml(model: dict[str, object]) -> dict[str, object]:
    diagram_type = model.get("diagram_type")
    if diagram_type == "class":
        classes = _as_sequence(model.get("classes", ()))
        return {
            "modules": tuple(
                {
                    "name": item.get("name", "unnamed"),
                    "responsibilities": (f"{item.get('name', 'unnamed')} domain behavior",),
                }
                for item in classes
            ),
            "change_targets": ({"name": "uml_design_input", "type": "domain_model", "mode": "extension"},),
            "inheritance": (),
            "interfaces": (),
            "dependencies": (),
        }
    return {
        "modules": ({"name": f"{diagram_type}_workflow", "responsibilities": (f"{diagram_type} workflow",)},),
        "change_targets": ({"name": "uml_design_input", "type": "workflow", "mode": "extension"},),
        "inheritance": (),
        "interfaces": (),
        "dependencies": (),
    }


def _result(findings: list[dict[str, str]]) -> dict[str, object]:
    return {
        "valid": not findings,
        "violations": tuple(finding["message"] for finding in findings),
        "findings": tuple(findings),
        "max_severity": _max_severity(tuple(findings)),
    }


def _finding(principle: str, severity: str, message: str) -> dict[str, str]:
    return {
        "principle": principle,
        "severity": severity,
        "message": message,
    }


def _max_severity(findings: tuple[dict[str, str], ...]) -> str:
    if not findings:
        return "INFO"
    return max((finding["severity"] for finding in findings), key=lambda item: SEVERITY_ORDER[item])


def _as_sequence(value: object) -> tuple:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return (value,)


__all__ = [
    "PROTECTED_CORE_TARGETS",
    "SEVERITY_ORDER",
    "solid_design_from_uml",
    "validate_dip",
    "validate_isp",
    "validate_lsp",
    "validate_ocp",
    "validate_solid_design",
    "validate_srp",
]
