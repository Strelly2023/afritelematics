"""Validate the non-binding AfriTech Constitution v1.0 doctrine artifact."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, cast

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION = ROOT / "afritech/constitution/AFRITECH_CONSTITUTION_V1.yaml"

REQUIRED_ROOT_KEYS: set[str] = {
    "schema",
    "version",
    "status",
    "authority",
    "scope",
    "foundational_principle",
    "canonical_statement",
    "constitutional_pillars",
    "core_pillar_layers",
    "ecosystem_pillars",
    "core_definitions",
    "hierarchy",
    "constitutional_rules",
    "layer_responsibilities",
    "doctrines",
    "system_dynamics",
    "expansion_rules",
    "canonical_language",
}

REQUIRED_BRANCHES: dict[str, str] = {
    "AfriCPPT": "GOVERNANCE",
    "AfriTPPS": "EXECUTION",
    "AfriProgramming": "ENGINEERING",
    "AFRIPower": "INTELLIGENCE",
}

REQUIRED_BRANCH_DOMAINS: dict[str, str] = {
    "AfriCPPT": "GOVERNANCE",
    "AfriTPPS": "EXECUTION",
    "AFRIPower": "INTELLIGENCE",
    "AfriProgramming": "ENGINEERING",
}

REQUIRED_CANONICAL_PHRASES: tuple[str, ...] = (
    "four constitutional pillars",
    "Deterministic Truth",
    "Orchestration",
    "Data Locality",
    "Observability",
    "four ecosystem pillars",
    "AfriCPPT governs",
    "AfriTPPS executes",
    "AfriProgramming builds",
    "AFRIPower explains",
    "eighteen core pillars",
)

REQUIRED_CORE_PILLAR_LAYERS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "CONSTITUTIONAL_KERNEL": (
        "Constitutional Kernel",
        "Defines truth.",
        (
            "DETERMINISTIC_EXECUTION",
            "REPLAY_LEGITIMACY",
            "CLOSED_WORLD_ADMISSIBILITY",
            "CANONICAL_IDENTITY",
            "CONSTITUTIONAL_AUTHORITY",
        ),
    ),
    "RUNTIME": (
        "Runtime and Operational",
        "Defines lawful execution behavior.",
        (
            "DATA_LOCALITY",
            "CONTINUITY_PRESERVATION",
            "ENTROPY_CONTAINMENT",
            "OBSERVABILITY_ISOLATION",
        ),
    ),
    "DISTRIBUTED_SCALE": (
        "Distributed Scale",
        "Defines lawful scaling.",
        (
            "PARTITIONED_DETERMINISTIC_SCALE",
            "WITNESS_INTEGRITY",
            "MULTI_NODE_CONVERGENCE",
        ),
    ),
    "GOVERNANCE": (
        "Governance and Proof",
        "Prevents conceptual inflation.",
        (
            "PROOF_BOUND_GOVERNANCE",
            "PRESERVE_OR_ISOLATE",
            "AUTHORITY_COMPRESSION",
        ),
    ),
    "HUMAN_ECOSYSTEM": (
        "Human and Ecosystem",
        "Defines why the system exists.",
        (
            "HUMAN_CONTINUITY",
            "ECONOMIC_CONTINUITY",
            "INFRASTRUCTURE_SOVEREIGNTY",
        ),
    ),
}

REQUIRED_CONSTITUTIONAL_PILLARS: dict[str, dict[str, str]] = {
    "DETERMINISTIC_TRUTH": {
        "name": "Deterministic Truth",
        "constitutional_function": "Replay Governance",
    },
    "ORCHESTRATION": {
        "name": "Orchestration",
        "constitutional_function": "Replay-Safe Execution",
    },
    "DATA_LOCALITY": {
        "name": "Data Locality",
        "constitutional_function": "Compute Near Data",
    },
    "OBSERVABILITY": {
        "name": "Observability",
        "constitutional_function": "Explain Without Authority",
    },
}

REQUIRED_ECOSYSTEM_PILLARS: dict[str, dict[str, str]] = {
    "AfriCPPT": {"role": "GOVERNANCE", "canonical_action": "governs"},
    "AfriTPPS": {"role": "EXECUTION", "canonical_action": "executes"},
    "AfriProgramming": {"role": "ENGINEERING", "canonical_action": "builds"},
    "AFRIPower": {"role": "INTELLIGENCE", "canonical_action": "explains"},
}

REQUIRED_BRANCH_PURPOSES: dict[str, str] = {
    "AfriCPPT": "Defines what is allowed.",
    "AfriTPPS": "Defines how work gets executed.",
    "AfriProgramming": "Builds and verifies software systems.",
    "AFRIPower": "Transforms evidence into intelligence.",
}

REQUIRED_BRANCH_QUESTIONS: dict[str, str] = {
    "AfriCPPT": "What should be done?",
    "AfriTPPS": "How should it be executed?",
    "AfriProgramming": "How do we build it?",
    "AFRIPower": "What can we learn from it?",
}

REQUIRED_BRANCH_OUTPUTS: dict[str, set[str]] = {
    "AfriCPPT": {
        "ADR",
        "Invariant",
        "Rule",
        "Binding",
        "Guard",
        "Policy",
        "Governance Model",
    },
    "AfriTPPS": {
        "Capabilities",
        "Workflows",
        "Processes",
        "Programs",
        "Operational Models",
        "Execution Metrics",
    },
    "AfriProgramming": {
        "Code",
        "Tests",
        "Validators",
        "Runtime Systems",
        "Proof Artifacts",
        "Software Platforms",
    },
    "AFRIPower": {
        "Insights",
        "Dashboards",
        "Reports",
        "Graph Projections",
        "Explanations",
        "Enterprise Intelligence Views",
    },
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(message)
    return cast(dict[str, Any], value)


def require_non_empty_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        fail(message)
    return cast(list[Any], value)


def require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list):
        fail(message)
    return cast(list[Any], value)


def require_string(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(message)
    return cast(str, value)


def optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def load_constitution(path: Path = CONSTITUTION) -> dict[str, Any]:
    if not path.exists():
        fail(f"constitution file missing: {path.relative_to(ROOT)}")

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        fail(f"constitution YAML does not parse: {exc}")

    return require_mapping(payload, "constitution YAML root must be a mapping")


def validate_required_root_keys(payload: dict[str, Any]) -> None:
    missing = REQUIRED_ROOT_KEYS - set(payload)
    if missing:
        fail(f"constitution missing root keys: {sorted(missing)}")


def validate_canonical_relationship(payload: dict[str, Any]) -> None:
    statement = require_string(
        payload.get("canonical_statement"),
        "canonical_statement must be a non-empty string",
    )

    missing = [
        phrase for phrase in REQUIRED_CANONICAL_PHRASES if phrase not in statement
    ]
    if missing:
        fail(f"canonical relationship missing phrases: {missing}")


def validate_hierarchy(payload: dict[str, Any]) -> None:
    hierarchy = require_mapping(payload.get("hierarchy"), "hierarchy must be a mapping")

    if hierarchy.get("root") != "AfriTech":
        fail("hierarchy root must be AfriTech")

    layers = require_non_empty_list(
        hierarchy.get("layers"),
        "hierarchy.layers must be a non-empty list",
    )

    branch_ids: list[str] = []
    discovered_roles: dict[str, str] = {}
    for index, layer in enumerate(layers):
        layer = require_mapping(layer, f"hierarchy.layers[{index}] must be a mapping")

        branch_id = require_string(layer.get("id"), f"hierarchy.layers[{index}] missing branch id")
        role = require_string(layer.get("role"), f"hierarchy.layers[{index}] missing role")

        branch_ids.append(branch_id)
        discovered_roles[branch_id] = role

    duplicates = sorted(
        {branch_id for branch_id in branch_ids if branch_ids.count(branch_id) > 1}
    )
    if duplicates:
        fail(f"duplicate hierarchy branch IDs: {duplicates}")

    missing_branches = set(REQUIRED_BRANCHES) - set(branch_ids)
    if missing_branches:
        fail(f"hierarchy missing required branches: {sorted(missing_branches)}")

    extra_branches = set(branch_ids) - set(REQUIRED_BRANCHES)
    if extra_branches:
        fail(f"hierarchy contains unexpected branches: {sorted(extra_branches)}")

    role_mismatches = {
        branch_id: (discovered_roles.get(branch_id), expected_role)
        for branch_id, expected_role in REQUIRED_BRANCHES.items()
        if discovered_roles.get(branch_id) != expected_role
    }
    if role_mismatches:
        fail(f"hierarchy role mismatch: {role_mismatches}")

    if branch_ids != list(REQUIRED_BRANCHES):
        fail(f"hierarchy branch order mismatch: {branch_ids!r}")


def validate_constitutional_pillars(payload: dict[str, Any]) -> None:
    pillars = require_non_empty_list(
        payload.get("constitutional_pillars"),
        "constitutional_pillars must be a non-empty list",
    )

    pillar_ids: list[str] = []
    discovered: dict[str, dict[str, Any]] = {}
    for index, pillar in enumerate(pillars):
        pillar = require_mapping(
            pillar,
            f"constitutional_pillars[{index}] must be a mapping",
        )

        pillar_id = require_string(
            pillar.get("id"),
            f"constitutional_pillars[{index}] missing id",
        )

        pillar_ids.append(pillar_id)
        discovered[pillar_id] = pillar

        for key in (
            "name",
            "constitutional_function",
            "purpose",
            "question_answered",
            "authority_boundary",
        ):
            require_string(pillar.get(key), f"constitutional pillar {pillar_id} missing {key}")

    if pillar_ids != list(REQUIRED_CONSTITUTIONAL_PILLARS):
        fail(f"constitutional pillar order mismatch: {pillar_ids!r}")

    extra = set(pillar_ids) - set(REQUIRED_CONSTITUTIONAL_PILLARS)
    if extra:
        fail(f"unexpected constitutional pillars: {sorted(extra)}")

    missing = set(REQUIRED_CONSTITUTIONAL_PILLARS) - set(pillar_ids)
    if missing:
        fail(f"missing constitutional pillars: {sorted(missing)}")

    for pillar_id, expected in REQUIRED_CONSTITUTIONAL_PILLARS.items():
        pillar = discovered[pillar_id]
        for key, expected_value in expected.items():
            if pillar.get(key) != expected_value:
                fail(
                    f"constitutional pillar {pillar_id} {key} mismatch: "
                    f"{pillar.get(key)!r}"
                )


def validate_ecosystem_pillars(payload: dict[str, Any]) -> None:
    pillars = require_non_empty_list(
        payload.get("ecosystem_pillars"),
        "ecosystem_pillars must be a non-empty list",
    )

    pillar_ids: list[str] = []
    discovered: dict[str, dict[str, Any]] = {}
    for index, pillar in enumerate(pillars):
        pillar = require_mapping(pillar, f"ecosystem_pillars[{index}] must be a mapping")

        pillar_id = require_string(pillar.get("id"), f"ecosystem_pillars[{index}] missing id")

        pillar_ids.append(pillar_id)
        discovered[pillar_id] = pillar

    if pillar_ids != list(REQUIRED_ECOSYSTEM_PILLARS):
        fail(f"ecosystem pillar order mismatch: {pillar_ids!r}")

    extra = set(pillar_ids) - set(REQUIRED_ECOSYSTEM_PILLARS)
    if extra:
        fail(f"unexpected ecosystem pillars: {sorted(extra)}")

    missing = set(REQUIRED_ECOSYSTEM_PILLARS) - set(pillar_ids)
    if missing:
        fail(f"missing ecosystem pillars: {sorted(missing)}")

    for pillar_id, expected in REQUIRED_ECOSYSTEM_PILLARS.items():
        pillar = discovered[pillar_id]
        for key, expected_value in expected.items():
            if pillar.get(key) != expected_value:
                fail(
                    f"ecosystem pillar {pillar_id} {key} mismatch: "
                    f"{pillar.get(key)!r}"
                )


def validate_core_pillar_layers(payload: dict[str, Any]) -> None:
    layers = require_non_empty_list(
        payload.get("core_pillar_layers"),
        "core_pillar_layers must be a non-empty list",
    )

    layer_ids: list[str] = []
    total_pillars = 0
    for index, layer in enumerate(layers):
        layer = require_mapping(layer, f"core_pillar_layers[{index}] must be a mapping")

        layer_id = require_string(layer.get("id"), f"core_pillar_layers[{index}] missing id")
        layer_ids.append(layer_id)

        if layer_id not in REQUIRED_CORE_PILLAR_LAYERS:
            fail(f"unexpected core pillar layer: {layer_id}")

        expected_name, expected_purpose, expected_pillars = (
            REQUIRED_CORE_PILLAR_LAYERS[layer_id]
        )
        if layer.get("name") != expected_name:
            fail(f"{layer_id} name mismatch: {layer.get('name')!r}")
        if layer.get("purpose") != expected_purpose:
            fail(f"{layer_id} purpose mismatch: {layer.get('purpose')!r}")
        require_string(layer.get("legitimacy_boundary"), f"{layer_id} missing legitimacy_boundary")

        pillars = require_non_empty_list(
            layer.get("pillars"),
            f"{layer_id} pillars must be a non-empty list",
        )

        pillar_ids: list[str] = []
        for pillar_index, pillar in enumerate(pillars):
            pillar = require_mapping(
                pillar,
                f"{layer_id}.pillars[{pillar_index}] must be a mapping",
            )
            pillar_id = require_string(
                pillar.get("id"),
                f"{layer_id}.pillars[{pillar_index}] missing id",
            )
            require_string(pillar.get("name"), f"{pillar_id} missing name")
            require_string(pillar.get("summary"), f"{pillar_id} missing summary")
            pillar_ids.append(pillar_id)

        if tuple(pillar_ids) != expected_pillars:
            fail(f"{layer_id} pillar order mismatch: {pillar_ids!r}")
        total_pillars += len(pillar_ids)

    if layer_ids != list(REQUIRED_CORE_PILLAR_LAYERS):
        fail(f"core pillar layer order mismatch: {layer_ids!r}")
    if total_pillars != 18:
        fail(f"core pillar count must be 18, got {total_pillars}")


def validate_branch_responsibilities(payload: dict[str, Any]) -> None:
    responsibilities = require_mapping(
        payload.get("layer_responsibilities"),
        "layer_responsibilities must be a mapping",
    )

    for branch_id, expected_domain in REQUIRED_BRANCH_DOMAINS.items():
        branch = require_mapping(
            responsibilities.get(branch_id),
            f"{branch_id} responsibilities missing",
        )

        domain = branch.get("domain")
        if domain != expected_domain:
            fail(f"{branch_id} domain must be {expected_domain}, got {domain!r}")

        items = require_non_empty_list(
            branch.get("responsibilities"),
            f"{branch_id} must define at least one responsibility",
        )
        if not all(isinstance(item, str) and item.strip() for item in items):
            fail(f"{branch_id} responsibilities must be non-empty strings")

        if branch.get("purpose") != REQUIRED_BRANCH_PURPOSES[branch_id]:
            fail(f"{branch_id} purpose mismatch: {branch.get('purpose')!r}")

        if branch.get("question_answered") != REQUIRED_BRANCH_QUESTIONS[branch_id]:
            fail(
                f"{branch_id} question_answered mismatch: "
                f"{branch.get('question_answered')!r}"
            )

        outputs = require_list(branch.get("outputs"), f"{branch_id} outputs must be a list")
        missing_outputs = REQUIRED_BRANCH_OUTPUTS[branch_id] - set(outputs)
        if missing_outputs:
            fail(f"{branch_id} outputs missing: {sorted(missing_outputs)}")

    chain = responsibilities["AfriCPPT"].get("canonical_chain")
    expected_chain = ["ADR", "INVARIANT", "RULE", "BINDING", "GUARD", "CI"]
    if chain != expected_chain:
        fail(f"AfriCPPT canonical chain mismatch: {chain!r}")


def validate_core_definitions(payload: dict[str, Any]) -> None:
    definitions = require_mapping(
        payload.get("core_definitions"),
        "core_definitions must be a mapping",
    )

    required_definition_keys = {
        "afritech",
        "afri_programming",
        "afri_cppt",
        "afri_tpps",
        "afri_power",
    }
    missing = required_definition_keys - set(definitions)
    if missing:
        fail(f"core_definitions missing entries: {sorted(missing)}")

    for key in required_definition_keys:
        definition = require_mapping(
            definitions.get(key),
            f"core_definitions.{key} must be a mapping",
        )
        if not optional_string(definition.get("role")):
            fail(f"core_definitions.{key} missing role")
        if not optional_string(definition.get("definition")):
            fail(f"core_definitions.{key} missing definition")


def validate(path: Path = CONSTITUTION) -> None:
    payload = load_constitution(path)
    validate_required_root_keys(payload)
    validate_canonical_relationship(payload)
    validate_core_definitions(payload)
    validate_constitutional_pillars(payload)
    validate_core_pillar_layers(payload)
    validate_ecosystem_pillars(payload)
    validate_hierarchy(payload)
    validate_branch_responsibilities(payload)


def main() -> int:
    try:
        validate()
        print("AfriTech Constitution v1.0 validation PASSED")
        return 0
    except Exception as exc:
        print(f"AfriTech Constitution v1.0 validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
