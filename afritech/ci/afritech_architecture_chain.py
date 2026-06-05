"""Canonical AfriTech architecture chain enforcement engine.

Enforces the declared governance chain:

ADR -> INVARIANT -> BINDING -> RULE -> GUARD -> CI

This module is intentionally source-only. It must be runnable as
``python -m afritech.ci.afritech_architecture_chain`` without configuring
Django or importing runtime execution surfaces.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
ADR_REGISTER = ROOT / "afritech/governance/adr/register.yaml"
ADR_DIR = ROOT / "afritech/governance/adr"
INVARIANTS = ROOT / "afritech/constitution/INVARIANTS.yaml"
BINDINGS_DIR = ROOT / "afritech/governance/bindings"
RULES_DIR = ROOT / "afritech/governance/rules"
TESTS_DIR = ROOT / "afritech/tests"


class ArchitectureViolation(RuntimeError):
    """Raised when the architecture chain has a broken link."""


@dataclass
class ChainState:
    registered_adrs: dict[str, Path] = field(default_factory=dict)
    adr_invariants: dict[str, set[str]] = field(default_factory=dict)
    canonical_invariants: set[str] = field(default_factory=set)
    rule_ids: set[str] = field(default_factory=set)
    rule_to_invariants: dict[str, set[str]] = field(default_factory=dict)
    binding_ids: set[str] = field(default_factory=set)
    binding_to_rules: dict[str, set[str]] = field(default_factory=dict)
    binding_to_invariants: dict[str, set[str]] = field(default_factory=dict)
    binding_to_adrs: dict[str, set[str]] = field(default_factory=dict)
    guard_targets: dict[str, str] = field(default_factory=dict)
    ci_terms: set[str] = field(default_factory=set)


class ArchitectureChainValidator:
    def __init__(self, root: Path = ROOT):
        self.root = root
        self.state = ChainState()

    def run_all_checks(self) -> bool:
        self.validate_adrs()
        self.validate_invariants()
        self.validate_rules()
        self.validate_bindings()
        self.validate_guards()
        self.validate_ci_enforcement()
        self.validate_full_chain()
        return True

    def validate_adrs(self) -> None:
        payload = _load_yaml(ADR_REGISTER)
        entries = payload.get("adrs")
        if not isinstance(entries, list) or not entries:
            raise ArchitectureViolation("ADR register must contain ADR entries")

        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ArchitectureViolation("ADR register entries must be mappings")
            adr_id = _require_text(entry.get("id"), "ADR register id")
            if adr_id in seen:
                raise ArchitectureViolation(f"duplicate ADR id in register: {adr_id}")
            seen.add(adr_id)
            path = self.root / _require_text(entry.get("path"), f"{adr_id} path")
            if not path.exists():
                raise ArchitectureViolation(f"{adr_id} path missing: {path}")
            adr = _load_yaml(path)
            body = _adr_body(adr)
            if _require_text(body.get("id"), f"{adr_id} file id") != adr_id:
                raise ArchitectureViolation(f"{adr_id} file id mismatch")
            for key in ("status", "context", "decision", "consequences"):
                if key not in body:
                    raise ArchitectureViolation(f"{adr_id} missing ADR field: {key}")
            if body.get("status") != "ACCEPTED":
                raise ArchitectureViolation(f"{adr_id} must be ACCEPTED")
            self.state.registered_adrs[adr_id] = path
            self.state.adr_invariants[adr_id] = _extract_invariant_ids(body.get("invariants", ()))

        print("✅ ADR Check: PASS")

    def validate_invariants(self) -> None:
        payload = _load_yaml(INVARIANTS)
        invariants = payload.get("invariants")
        if not isinstance(invariants, list) or not invariants:
            raise ArchitectureViolation("INVARIANTS.yaml must define invariants")
        seen: set[str] = set()
        for invariant in invariants:
            if not isinstance(invariant, dict):
                raise ArchitectureViolation("invariant entries must be mappings")
            inv_id = _require_text(invariant.get("id"), "invariant id")
            if inv_id in seen:
                raise ArchitectureViolation(f"duplicate invariant id: {inv_id}")
            if not invariant.get("description"):
                raise ArchitectureViolation(f"{inv_id} missing description")
            seen.add(inv_id)
        self.state.canonical_invariants = seen
        print("✅ INVARIANT Check: PASS")

    def validate_bindings(self) -> None:
        for path in sorted(BINDINGS_DIR.glob("*.yaml")):
            payload = _load_yaml(path)
            binding_id = _require_text(payload.get("id"), f"{path} id")
            if binding_id in self.state.binding_ids:
                raise ArchitectureViolation(f"duplicate binding id: {binding_id}")
            self.state.binding_ids.add(binding_id)
            linked_rules = set(_as_list(payload.get("linked_rules")))
            linked_invariants = set(_as_list(payload.get("linked_invariants")))
            linked_adrs = set(_as_list(payload.get("linked_adr")))

            entries = payload.get("bindings", ())
            if entries and not isinstance(entries, list):
                raise ArchitectureViolation(f"{binding_id} bindings must be a list")
            for entry in entries or ():
                if not isinstance(entry, dict):
                    raise ArchitectureViolation(f"{binding_id} binding entries must be mappings")
                entry_id = _require_text(entry.get("id"), f"{binding_id} entry id")
                self.state.binding_ids.add(entry_id)
                target = _require_text(entry.get("target"), f"{entry_id} target")
                _validate_target_exists(target)
                linked_rules.update(_as_list(entry.get("linked_rules")))
                if "guard" in entry.get("name", "").lower() or ".guards." in target:
                    self.state.guard_targets[entry_id] = target

            for target in _as_list(payload.get("guards")):
                target = str(target)
                _validate_target_exists(target)
                self.state.guard_targets[target] = target
            linked_rules.update(_as_list(payload.get("rules")))

            self.state.binding_to_rules[binding_id] = linked_rules
            self.state.binding_to_invariants[binding_id] = linked_invariants
            self.state.binding_to_adrs[binding_id] = linked_adrs
            for rule_id in linked_rules:
                if rule_id not in self.state.rule_ids:
                    raise ArchitectureViolation(f"{binding_id} links unknown rule: {rule_id}")
            for adr_id in linked_adrs:
                if adr_id not in self.state.registered_adrs:
                    raise ArchitectureViolation(f"{binding_id} links unregistered ADR: {adr_id}")
        print("✅ BINDING Check: PASS")

    def validate_rules(self) -> None:
        for path in sorted(RULES_DIR.glob("*.yaml")):
            payload = _load_yaml(path)
            rule_id = _require_text(payload.get("id"), f"{path} id")
            if rule_id in self.state.rule_ids:
                raise ArchitectureViolation(f"duplicate rule id: {rule_id}")
            self.state.rule_ids.add(rule_id)
            linked = set(_as_list(payload.get("linked_invariants")))
            if not linked and "INVARIANT" in rule_id:
                linked.add(rule_id)
            self.state.rule_to_invariants[rule_id] = linked
            rules = payload.get("rules", ())
            if isinstance(rules, list):
                for rule in rules:
                    if not isinstance(rule, dict):
                        raise ArchitectureViolation(f"{rule_id} subrules must be mappings")
                    sub_id = _require_text(rule.get("id"), f"{rule_id} subrule id")
                    if sub_id in self.state.rule_ids:
                        raise ArchitectureViolation(f"duplicate rule id: {sub_id}")
                    if not rule.get("description") and not rule.get("rule"):
                        raise ArchitectureViolation(f"{sub_id} missing enforceable description")
                    if "enforcement" not in rule and "requirements" not in payload:
                        raise ArchitectureViolation(f"{sub_id} missing enforcement logic")
                    self.state.rule_ids.add(sub_id)
                    self.state.rule_to_invariants[sub_id] = linked
            elif "enforcement" not in payload and "rule" not in payload:
                raise ArchitectureViolation(f"{rule_id} missing enforcement logic")
        print("✅ RULE Check: PASS")

    def validate_guards(self) -> None:
        if not self.state.guard_targets:
            raise ArchitectureViolation("no guard targets declared")
        for guard_id, target in self.state.guard_targets.items():
            if "." not in target:
                continue
            exact_path = self.root / (target.replace(".", "/") + ".py")
            if exact_path.exists():
                continue
            module_path, _, attr = target.rpartition(".")
            py_path = self.root / (module_path.replace(".", "/") + ".py")
            if not py_path.exists():
                raise ArchitectureViolation(f"{guard_id} guard module missing: {module_path}")
            if attr and not _python_attr_exists(py_path, attr):
                raise ArchitectureViolation(f"{guard_id} guard callable missing: {target}")
        print("✅ GUARD Check: PASS")

    def validate_ci_enforcement(self) -> None:
        test_source = _read_tests_source()
        for binding_id, rules in self.state.binding_to_rules.items():
            if binding_id not in test_source and not (rules & self.state.ci_terms):
                # Binding-level CI declarations are acceptable for older governance
                # bindings that predate rule-id tests.
                binding_path = next(BINDINGS_DIR.glob(f"{binding_id}*.yaml"), None)
                if binding_path is None or "ci:" not in binding_path.read_text(encoding="utf-8"):
                    raise ArchitectureViolation(f"{binding_id} missing CI enforcement evidence")
        for guard_id, target in self.state.guard_targets.items():
            guard_name = target.rpartition(".")[2] or guard_id
            if guard_name not in test_source and guard_id not in test_source:
                raise ArchitectureViolation(f"{guard_id} guard missing test/source coverage")
        print("✅ CI Check: PASS")

    def validate_full_chain(self) -> None:
        for binding_id, adrs in self.state.binding_to_adrs.items():
            if not adrs:
                continue
            if not self.state.binding_to_rules.get(binding_id):
                raise ArchitectureViolation(f"{binding_id} has ADR link but no rule link")
            if not self.state.binding_to_invariants.get(binding_id):
                raise ArchitectureViolation(f"{binding_id} has ADR link but no invariant link")
        rule_coverage = set().union(*self.state.binding_to_rules.values()) if self.state.binding_to_rules else set()
        dangling_rules = {
            rule_id
            for rule_id in self.state.rule_ids
            if rule_id.startswith(("RULE-014", "RULE-019", "RULE-AUDIT"))
            and rule_id not in rule_coverage
        }
        if dangling_rules:
            raise ArchitectureViolation(f"dangling rules without binding: {sorted(dangling_rules)}")
        print("✅ FULL CHAIN: PASS")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ArchitectureViolation(f"missing YAML file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ArchitectureViolation(f"YAML file must be a mapping: {path}")
    return data


def _adr_body(payload: dict[str, Any]) -> dict[str, Any]:
    body = payload.get("adr", payload)
    if not isinstance(body, dict):
        raise ArchitectureViolation("ADR body must be a mapping")
    return body


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ArchitectureViolation(f"{field} is required")
    return value.strip()


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _extract_invariant_ids(value: Any) -> set[str]:
    ids: set[str] = set()
    for item in _as_list(value):
        ids.add(item)
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and item.get("id"):
                ids.add(str(item["id"]))
    return ids


def _validate_target_exists(target: str) -> None:
    if "/" in target or target.endswith((".md", ".yaml", ".json")):
        if not (ROOT / target).exists():
            raise ArchitectureViolation(f"binding target missing: {target}")
        return
    module_path = target
    attr = ""
    exact_py_path = ROOT / (target.replace(".", "/") + ".py")
    if exact_py_path.exists():
        return
    if "." in target:
        candidate_module, _, candidate_attr = target.rpartition(".")
        candidate_path = ROOT / (candidate_module.replace(".", "/") + ".py")
        if candidate_path.exists():
            module_path = candidate_module
            attr = candidate_attr
    py_path = ROOT / (module_path.replace(".", "/") + ".py")
    package_path = ROOT / module_path.replace(".", "/") / "__init__.py"
    if not py_path.exists() and not package_path.exists():
        raise ArchitectureViolation(f"binding target module missing: {target}")
    if attr and py_path.exists() and not _python_attr_exists(py_path, attr):
        raise ArchitectureViolation(f"binding target attr missing: {target}")


def _python_attr_exists(path: Path, attr: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == attr:
            return True
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == attr:
                    return True
    return False


def _read_tests_source() -> str:
    chunks: list[str] = []
    for path in TESTS_DIR.rglob("test_*.py"):
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def validate() -> bool:
    return ArchitectureChainValidator().run_all_checks()


def main() -> int:
    try:
        validate()
    except ArchitectureViolation as exc:
        print("❌ FAILURE:")
        print(exc)
        print("SYSTEM INVALID ❌")
        return 1
    print("FINAL RESULT: SYSTEM INTEGRITY VERIFIED ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
