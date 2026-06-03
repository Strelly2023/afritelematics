"""Read-only YAML to Django-object documentary governance projection."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .models import (
    ENFORCEMENT_AUTHORITY,
    PROJECTION_IS_DOCUMENTARY_ONLY,
    PROJECTION_STATUS,
    RUNTIME_AUTHORITY,
    GovernanceADR,
    GovernanceBinding,
    GovernanceCICheck,
    GovernanceInvariant,
    GovernanceNextStep,
    GovernanceNonClaim,
    GovernanceRule,
)


READ_ONLY = True
PROJECTION_DIRECTION = "YAML_TO_DJANGO_PROJECTION"
FORBIDDEN_REVERSE_DIRECTION = "DJANGO_PROJECTION_TO_AUTHORITY"

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_ROOT = ROOT / "afritech/governance"


@dataclass(frozen=True)
class GovernanceProjectionBundle:
    """In-memory documentary projection produced from governance YAML."""

    adrs: list[GovernanceADR] = field(default_factory=list)
    invariants: list[GovernanceInvariant] = field(default_factory=list)
    rules: list[GovernanceRule] = field(default_factory=list)
    bindings: list[GovernanceBinding] = field(default_factory=list)
    ci_checks: list[GovernanceCICheck] = field(default_factory=list)
    non_claims: list[GovernanceNonClaim] = field(default_factory=list)
    next_steps: list[GovernanceNextStep] = field(default_factory=list)


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"governance projection source must be a mapping: {path}")
    return payload


def project_governance(root: Path = GOVERNANCE_ROOT) -> GovernanceProjectionBundle:
    """Project governance YAML into unsaved documentary Django model objects."""

    bundle = GovernanceProjectionBundle()
    for path in sorted((root / "adr").glob("ADR-*.yaml")):
        project_adr(path, bundle)
    for path in sorted((root / "rules").glob("RULE-*.yaml")):
        project_rule_file(path, bundle)
    for path in sorted((root / "bindings").glob("BIND-*.yaml")):
        project_binding_file(path, bundle)
    return bundle


def project_adr(path: Path, bundle: GovernanceProjectionBundle) -> None:
    payload = load_yaml(path)
    adr = payload.get("adr")
    if not isinstance(adr, dict):
        return

    adr_id = str(adr.get("id", path.stem))
    boundary = adr.get("constitutional_boundary") or {}
    runtime_authoritative = bool(
        isinstance(boundary, dict) and boundary.get("runtime_authoritative") is True
    )
    bundle.adrs.append(
        GovernanceADR(
            **_base_kwargs(path, adr_id, str(adr.get("title", "")), adr),
            status=str(adr.get("status", "")),
            adr_type=str(adr.get("type", "")),
            runtime_authoritative_declared=runtime_authoritative,
        )
    )

    for invariant in _mapping_items(adr.get("invariants")):
        invariant_id = str(invariant.get("id", ""))
        bundle.invariants.append(
            GovernanceInvariant(
                **_base_kwargs(path, invariant_id, invariant_id, invariant),
                adr_id=adr_id,
                description=str(invariant.get("description", "")),
            )
        )

    for rule in _mapping_items(adr.get("rules")):
        rule_id = str(rule.get("id", ""))
        bundle.rules.append(
            GovernanceRule(
                **_base_kwargs(path, rule_id, rule_id, rule),
                adr_id=adr_id,
                description=str(rule.get("description", "")),
            )
        )

    for binding in _mapping_items(adr.get("bindings")):
        binding_id = str(binding.get("id", ""))
        bundle.bindings.append(
            GovernanceBinding(
                **_base_kwargs(path, binding_id, binding_id, binding),
                adr_id=adr_id,
                target=str(binding.get("target", "")),
                description=str(binding.get("description", "")),
            )
        )

    ci = adr.get("ci") if isinstance(adr.get("ci"), dict) else {}
    for check in tuple(ci.get("required_checks", ())) + tuple(ci.get("tests", ())):
        check_name = str(check)
        bundle.ci_checks.append(
            GovernanceCICheck(
                **_base_kwargs(path, check_name, check_name, {"check": check_name}),
                adr_id=adr_id,
                check_name=check_name,
            )
        )

    for index, statement in enumerate(adr.get("non_claims", ())):
        source_id = f"{adr_id}-NON-CLAIM-{index + 1}"
        bundle.non_claims.append(
            GovernanceNonClaim(
                **_base_kwargs(path, source_id, source_id, {"statement": statement}),
                adr_id=adr_id,
                statement=str(statement),
            )
        )

    next_step = adr.get("next_admissible_step")
    if next_step:
        source_id = f"{adr_id}-NEXT-STEP"
        bundle.next_steps.append(
            GovernanceNextStep(
                **_base_kwargs(path, source_id, source_id, {"statement": next_step}),
                adr_id=adr_id,
                statement=str(next_step),
            )
        )


def project_rule_file(path: Path, bundle: GovernanceProjectionBundle) -> None:
    payload = load_yaml(path)
    rule_id = str(payload.get("id", path.stem))
    title = str(payload.get("name") or payload.get("title") or rule_id)
    bundle.rules.append(
        GovernanceRule(
            **_base_kwargs(path, rule_id, title, payload),
            adr_id=_first_link(payload.get("linked_adr")),
            description=str(payload.get("description", "")),
        )
    )


def project_binding_file(path: Path, bundle: GovernanceProjectionBundle) -> None:
    payload = load_yaml(path)
    binding_id = str(payload.get("id", path.stem))
    title = str(payload.get("name") or payload.get("title") or binding_id)
    bundle.bindings.append(
        GovernanceBinding(
            **_base_kwargs(path, binding_id, title, payload),
            adr_id=_first_link(payload.get("linked_adr")),
            target=str(payload.get("target", "")),
            description=str(payload.get("description", "")),
        )
    )


def _base_kwargs(
    path: Path, source_id: str, title: str, payload: dict[str, Any]
) -> dict[str, Any]:
    return {
        "source_path": str(path.relative_to(ROOT)),
        "source_id": source_id,
        "title": title,
        "projection_status": PROJECTION_STATUS,
        "projection_is_documentary_only": PROJECTION_IS_DOCUMENTARY_ONLY,
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "payload": payload,
    }


def _mapping_items(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def _first_link(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0])
    if isinstance(value, str):
        return value
    return ""
