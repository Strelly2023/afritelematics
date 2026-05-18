from __future__ import annotations

import re
import sys
import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = ROOT / "afritech/constitution/core"
CORE_CONSTRAINTS = CORE_ROOT / "_constraints.yaml"
SEMANTIC_ATOMS_CORE = ROOT / "afritech/constitution/semantic_atoms_core.yaml"
SEMANTIC_ATOMS = ROOT / "afritech/constitution/semantic_atoms.yaml"
PROFILES = ROOT / "afritech/constitution/profiles.yaml"
AMENDMENTS = ROOT / "afritech/constitution/evolution/amendments.yaml"
EPOCHS = ROOT / "afritech/constitution/evolution/epochs.yaml"
ADVERSARIAL_INDEX = ROOT / "afritech/simulation/adversarial/index.yaml"
PROOF_ROOT = ROOT / "afritech/proofs"

DEFAULT_MAX_KERNEL_LINES = 50
DEFAULT_MIN_AXIOMS = 3
DEFAULT_MAX_AXIOMS = 5

SEM_ID = re.compile(r"^SEM-[A-Z]+-\d{3}$")
AX_ID = re.compile(r"^AX-[A-Z]+-\d{3}$")


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing file: {path}")

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        fail(f"invalid YAML in {path}: {exc}")

    if not isinstance(payload, dict):
        fail(f"{path} must be a mapping")

    return payload


def load_semantic_atoms() -> set[str]:
    payload = load_yaml(SEMANTIC_ATOMS_CORE)
    atoms = payload.get("semantic_atoms")

    if not isinstance(atoms, dict) or not atoms:
        fail("semantic_atoms_core.yaml must define semantic_atoms")

    ids = set()
    names = set()

    for atom_id, atom in atoms.items():
        if not SEM_ID.fullmatch(atom_id):
            fail(f"invalid semantic atom id: {atom_id}")
        if not isinstance(atom, dict):
            fail(f"{atom_id} must be a mapping")

        name = atom.get("name")
        if not isinstance(name, str) or not name:
            fail(f"{atom_id} missing name")
        if name in names:
            fail(f"duplicate semantic atom name: {name}")

        atom_hash = atom.get("hash")
        expected_hash = hashlib.sha256(
            json.dumps(
                {"id": atom_id, "name": name},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        if atom_hash != expected_hash:
            fail(f"{atom_id} semantic hash mismatch")

        ids.add(atom_id)
        names.add(name)

    return ids


def load_core_constraints() -> dict[str, int | bool]:
    payload = load_yaml(CORE_CONSTRAINTS)
    constraints = payload.get("constraints")

    if not isinstance(constraints, dict):
        fail("_constraints.yaml must define constraints")

    return {
        "max_files": int(constraints.get("max_files", 5)),
        "min_axioms_per_file": int(
            constraints.get("min_axioms_per_file", DEFAULT_MIN_AXIOMS)
        ),
        "max_axioms_per_file": int(
            constraints.get("max_axioms_per_file", DEFAULT_MAX_AXIOMS)
        ),
        "max_lines_per_file": int(
            constraints.get("max_lines_per_file", DEFAULT_MAX_KERNEL_LINES)
        ),
        "no_prose": constraints.get("no_prose") is True,
        "only_semantic_atoms_allowed": (
            constraints.get("only_semantic_atoms_allowed") is True
        ),
    }


def validate_dependency_closure(atom_ids: set[str]) -> None:
    payload = load_yaml(SEMANTIC_ATOMS)
    deps = (
        payload.get("semantic_structure", {})
        .get("dependencies", {})
    )

    if not isinstance(deps, dict):
        fail("semantic atom dependencies must be a mapping")

    graph: dict[str, set[str]] = defaultdict(set)
    indegree = {atom_id: 0 for atom_id in atom_ids}

    for atom_id, required in deps.items():
        if atom_id not in atom_ids:
            fail(f"dependency declared for undefined atom: {atom_id}")
        if not isinstance(required, dict):
            fail(f"dependency block for {atom_id} must be a mapping")

        depends_on = required.get("depends_on", [])
        if not isinstance(depends_on, list):
            fail(f"depends_on for {atom_id} must be a list")

        for dependency in depends_on:
            if dependency not in atom_ids:
                fail(f"{atom_id} depends on undefined atom: {dependency}")
            graph[dependency].add(atom_id)
            indegree[atom_id] += 1

    ready = deque(sorted(k for k, v in indegree.items() if v == 0))
    visited = 0

    while ready:
        node = ready.popleft()
        visited += 1
        for child in sorted(graph[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)

    if visited != len(atom_ids):
        fail("semantic atom dependency graph must be acyclic")


def validate_core_kernel(atom_ids: set[str]) -> set[str]:
    constraints = load_core_constraints()
    core_files = sorted(
        path for path in CORE_ROOT.glob("*.yaml")
        if not path.name.startswith("_")
    )
    if not core_files:
        fail("constitution/core must contain kernel files")
    if len(core_files) != constraints["max_files"]:
        fail(
            "constitution/core must contain exactly "
            f"{constraints['max_files']} kernel files"
        )

    axiom_ids: set[str] = set()
    axiom_dependencies: dict[str, set[str]] = {}

    for path in core_files:
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > constraints["max_lines_per_file"]:
            fail(f"{path} exceeds {constraints['max_lines_per_file']} lines")

        payload = load_yaml(path)
        axioms = payload.get("axioms")
        if not isinstance(axioms, list):
            fail(f"{path} must define axioms")
        if not (
            constraints["min_axioms_per_file"]
            <= len(axioms)
            <= constraints["max_axioms_per_file"]
        ):
            fail(
                f"{path} must define "
                f"{constraints['min_axioms_per_file']}-"
                f"{constraints['max_axioms_per_file']} axioms"
            )

        meta_invariants = payload.get("meta", {}).get("invariants", [])
        for atom_id in meta_invariants:
            if atom_id not in atom_ids:
                fail(f"{path} references undefined semantic atom {atom_id}")

        for axiom in axioms:
            if not isinstance(axiom, dict):
                fail(f"{path} contains non-mapping axiom")

            axiom_id = axiom.get("id")
            if not isinstance(axiom_id, str) or not AX_ID.fullmatch(axiom_id):
                fail(f"{path} contains invalid axiom id: {axiom_id}")
            if axiom_id in axiom_ids:
                fail(f"duplicate core axiom id: {axiom_id}")

            guarantees = axiom.get("guarantees")
            if not isinstance(guarantees, list) or not guarantees:
                fail(f"{axiom_id} must reference semantic guarantees")
            for atom_id in guarantees:
                if atom_id not in atom_ids:
                    fail(f"{axiom_id} references undefined atom {atom_id}")

            depends_on = axiom.get("depends_on")
            if not isinstance(depends_on, list):
                fail(f"{axiom_id} must declare depends_on")
            for dependency in depends_on:
                if not isinstance(dependency, str) or not AX_ID.fullmatch(dependency):
                    fail(f"{axiom_id} has invalid dependency {dependency}")

            statement = axiom.get("statement")
            if not isinstance(statement, str) or not statement.strip():
                fail(f"{axiom_id} must contain an atomic statement")
            if "\n" in statement:
                fail(f"{axiom_id} statement must be a single line")

            axiom_ids.add(axiom_id)
            axiom_dependencies[axiom_id] = set(depends_on)

    for axiom_id, dependencies in axiom_dependencies.items():
        unknown = dependencies - axiom_ids
        if unknown:
            fail(f"{axiom_id} depends on unknown axioms: {sorted(unknown)}")

    validate_acyclic_graph(axiom_dependencies, "core axiom dependency graph")

    return axiom_ids


def validate_acyclic_graph(graph: dict[str, set[str]], label: str) -> None:
    children: dict[str, set[str]] = defaultdict(set)
    indegree = {node: 0 for node in graph}

    for node, dependencies in graph.items():
        for dependency in dependencies:
            children[dependency].add(node)
            indegree[node] += 1

    ready = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    visited = 0

    while ready:
        node = ready.popleft()
        visited += 1
        for child in sorted(children[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)

    if visited != len(graph):
        fail(f"{label} must be acyclic")


def validate_profiles(atom_ids: set[str]) -> None:
    payload = load_yaml(PROFILES)
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        fail("profiles.yaml must define profiles")

    for name, profile in profiles.items():
        if not isinstance(profile, dict):
            fail(f"profile {name} must be a mapping")

        requires = profile.get("requires")
        forbids = profile.get("forbids")
        if not isinstance(requires, list) or not requires:
            fail(f"profile {name} must require semantic atoms")
        if not isinstance(forbids, list) or not forbids:
            fail(f"profile {name} must forbid runtime conditions")
        runtime_constraints = profile.get("runtime_constraints")
        if not isinstance(runtime_constraints, dict) or not runtime_constraints:
            fail(f"profile {name} must define runtime_constraints")
        if runtime_constraints.get("deterministic_only") is not True:
            fail(f"profile {name} must require deterministic_only")

        for atom_id in requires:
            if atom_id not in atom_ids:
                fail(f"profile {name} references undefined atom {atom_id}")


def validate_amendments(axiom_ids: set[str], atom_ids: set[str]) -> None:
    payload = load_yaml(AMENDMENTS)
    amendments = payload.get("amendments")
    if not isinstance(amendments, dict):
        fail("amendments.yaml must define amendments")

    known_targets = axiom_ids | atom_ids
    for amendment_id, amendment in amendments.items():
        if not isinstance(amendment, dict):
            fail(f"{amendment_id} must be a mapping")

        affects = amendment.get("affects")
        if not isinstance(affects, list) or not affects:
            fail(f"{amendment_id} must define affected targets")
        for target in affects:
            if target not in known_targets:
                fail(f"{amendment_id} affects unknown target {target}")

        if "compatibility" not in amendment:
            fail(f"{amendment_id} missing compatibility")
        if "migration_required" not in amendment:
            fail(f"{amendment_id} missing migration_required")
        if "migration_strategy" not in amendment:
            fail(f"{amendment_id} missing migration_strategy")
        if "compatibility_window" not in amendment:
            fail(f"{amendment_id} missing compatibility_window")


def validate_epochs(axiom_ids: set[str]) -> None:
    payload = load_yaml(EPOCHS)
    epochs = payload.get("epochs")

    if not isinstance(epochs, dict) or not epochs:
        fail("epochs.yaml must define epochs")

    for epoch_id, epoch in epochs.items():
        if not isinstance(epoch, dict):
            fail(f"{epoch_id} must be a mapping")

        active_axioms = epoch.get("active_axioms")
        if not isinstance(active_axioms, list) or not active_axioms:
            fail(f"{epoch_id} must define active_axioms")

        unknown = set(active_axioms) - axiom_ids
        if unknown:
            fail(f"{epoch_id} references unknown axioms: {sorted(unknown)}")


def validate_adversarial_index(atom_ids: set[str], axiom_ids: set[str]) -> None:
    payload = load_yaml(ADVERSARIAL_INDEX)
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, dict) or not scenarios:
        fail("adversarial index must define scenarios")

    known_targets = atom_ids | axiom_ids
    covered: set[str] = set()
    required_metrics = payload.get("metrics", {}).get("required", [])
    expected_metrics = {
        "determinism_violation",
        "replay_equivalence",
        "divergence_detected",
        "reconciliation_success",
    }

    if set(required_metrics) != expected_metrics:
        fail("adversarial index must declare required execution metrics")

    for scenario_id, scenario in scenarios.items():
        if not isinstance(scenario, dict):
            fail(f"{scenario_id} must be a mapping")

        targets = scenario.get("targets")
        if not isinstance(targets, list) or not targets:
            fail(f"{scenario_id} must target atoms or axioms")

        for target in targets:
            if target not in known_targets:
                fail(f"{scenario_id} targets unknown invariant {target}")
            covered.add(target)

    missing_atoms = atom_ids - covered
    missing_axioms = axiom_ids - covered

    if missing_atoms:
        fail(f"adversarial coverage missing atoms: {sorted(missing_atoms)}")
    if missing_axioms:
        fail(f"adversarial coverage missing axioms: {sorted(missing_axioms)}")


def validate_proof_targets(axiom_ids: set[str]) -> None:
    proof_files = [
        PROOF_ROOT / "determinism.md",
        PROOF_ROOT / "replay_admissibility.md",
        PROOF_ROOT / "closed_world_participation.md",
    ]

    for path in proof_files:
        if not path.exists():
            fail(f"missing proof target: {path}")

        text = path.read_text(encoding="utf-8")
        for section in ("Assumptions:", "Inference steps:", "Theorem:", "Sketch:"):
            if section not in text:
                fail(f"{path} missing section {section}")

        refs = set(re.findall(r"AX-[A-Z]+-\d{3}", text))
        if not refs:
            fail(f"{path} must reference core axioms")

        unknown = refs - axiom_ids
        if unknown:
            fail(f"{path} references unknown axioms: {sorted(unknown)}")


def run() -> None:
    atom_ids = load_semantic_atoms()
    validate_dependency_closure(atom_ids)
    axiom_ids = validate_core_kernel(atom_ids)
    validate_profiles(atom_ids)
    validate_amendments(axiom_ids, atom_ids)
    validate_epochs(axiom_ids)
    validate_adversarial_index(atom_ids, axiom_ids)
    validate_proof_targets(axiom_ids)

    print("✅ Semantic kernel validation PASSED")
    print(f"✅ Semantic atoms: {len(atom_ids)}")
    print(f"✅ Core axioms: {len(axiom_ids)}")
    print("✅ Profiles, evolution, adversarial coverage, proofs verified")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"❌ Semantic kernel validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
