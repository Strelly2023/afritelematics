from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class TrustPolicy:
    policy_id: str
    name: str
    weight: int
    min_score: int
    evidence_key: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "weight": self.weight,
            "min_score": self.min_score,
            "evidence_key": self.evidence_key,
        }


@dataclass(frozen=True)
class PolicyVersion:
    policy_id: str
    name: str
    version: int
    source: str
    rules: tuple[dict[str, Any], ...]
    policy_hash: str
    status: str = "active"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "version": self.version,
            "source": self.source,
            "rules": list(self.rules),
            "policy_hash": self.policy_hash,
            "status": self.status,
        }


class PolicyDSL:
    def parse(self, source: str) -> dict[str, Any]:
        lines = [line.strip() for line in source.splitlines() if line.strip() and not line.strip().startswith("#")]
        if not lines or not lines[0].startswith("policy "):
            raise ValueError("policy DSL must start with: policy <name>")
        name = lines[0].split(" ", 1)[1].strip()
        rules: list[dict[str, Any]] = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) != 4 or parts[0] != "require":
                raise ValueError(f"unsupported policy DSL line: {line}")
            rules.append({"key": parts[1], "operator": parts[2], "value": _parse_value(parts[3])})
        return {"name": name, "rules": tuple(rules)}


class PolicyRegistry:
    def __init__(self) -> None:
        self._dsl = PolicyDSL()
        self._versions: dict[str, list[PolicyVersion]] = {}
        self.register(
            """
            policy novascript_default_trust
            require trust_score >= 70
            require risk_score <= 60
            require federation_verified == true
            require receipt_verified == true
            """
        )

    def register(self, source: str) -> dict[str, Any]:
        parsed = self._dsl.parse(source)
        name = str(parsed["name"])
        version = len(self._versions.get(name, [])) + 1
        policy_id = "policy-" + sha256(f"{name}:{version}".encode("utf-8")).hexdigest()[:12]
        policy = PolicyVersion(
            policy_id=policy_id,
            name=name,
            version=version,
            source=source.strip(),
            rules=parsed["rules"],
            policy_hash=sha256(source.strip().encode("utf-8")).hexdigest(),
        )
        self._versions.setdefault(name, []).append(policy)
        return policy.canonical_dict()

    def latest(self, name: str = "novascript_default_trust") -> PolicyVersion:
        versions = [version for version in self._versions.get(name, []) if version.status == "active"]
        if not versions:
            raise KeyError(name)
        return versions[-1]

    def list(self) -> list[dict[str, Any]]:
        return [
            version.canonical_dict()
            for versions in self._versions.values()
            for version in versions
        ]

    def evaluate(self, *, context: dict[str, Any], name: str = "novascript_default_trust") -> dict[str, Any]:
        policy = self.latest(name)
        results = []
        for rule in policy.rules:
            actual = context.get(rule["key"])
            results.append({**rule, "actual": actual, "satisfied": _compare(actual, rule["operator"], rule["value"])})
        allowed = all(item["satisfied"] for item in results)
        decision_id = "decision-" + sha256(
            f"{policy.policy_id}:{policy.version}:{sorted(context.items())}".encode("utf-8")
        ).hexdigest()[:12]
        return {
            "decision_id": decision_id,
            "allowed": allowed,
            "policy_id": policy.policy_id,
            "policy_name": policy.name,
            "policy_version": policy.version,
            "policy_hash": policy.policy_hash,
            "rule_results": results,
        }

    def transition(self, *, policy_id: str, status: str) -> dict[str, Any]:
        if status not in {"active", "deprecated", "retired"}:
            raise ValueError("policy status must be active, deprecated, or retired")
        for name, versions in self._versions.items():
            for index, version in enumerate(versions):
                if version.policy_id == policy_id:
                    updated = PolicyVersion(
                        policy_id=version.policy_id,
                        name=version.name,
                        version=version.version,
                        source=version.source,
                        rules=version.rules,
                        policy_hash=version.policy_hash,
                        status=status,
                    )
                    versions[index] = updated
                    return {
                        "mode": "policy_registry_lifecycle_management",
                        "policy_id": policy_id,
                        "policy_name": name,
                        "status": status,
                        "transition_hash": sha256(f"{policy_id}:{status}".encode()).hexdigest(),
                    }
        raise KeyError(policy_id)


class PolicyDrivenTrustEngine:
    def __init__(self) -> None:
        self._policies = (
            TrustPolicy("policy-repository-structure", "repository_structure", 25, 15, "repository_graph"),
            TrustPolicy("policy-architecture-alignment", "architecture_alignment", 25, 15, "architecture_knowledge"),
            TrustPolicy("policy-debt-control", "technical_debt_control", 20, 12, "technical_debt"),
            TrustPolicy("policy-deterministic-artifacts", "deterministic_artifacts", 15, 15, "artifact_control"),
            TrustPolicy("policy-governance-receipt", "governance_receipt_required", 15, 15, "governance_receipt"),
        )

    def policies(self) -> list[dict[str, Any]]:
        return [policy.canonical_dict() for policy in self._policies]

    def evaluate(
        self,
        *,
        prompt: str,
        graph: dict[str, Any],
        debt: dict[str, Any],
        architecture: dict[str, Any],
        deterministic_artifacts: bool = True,
    ) -> dict[str, Any]:
        evidence = {
            "repository_graph": _score_repository_graph(graph),
            "architecture_knowledge": _score_architecture(architecture),
            "technical_debt": _score_debt(debt),
            "artifact_control": 100 if deterministic_artifacts else 0,
            "governance_receipt": 100,
        }
        decisions = []
        total = 0
        for policy in self._policies:
            evidence_score = int(evidence.get(policy.evidence_key, 0))
            weighted = round(evidence_score * policy.weight / 100)
            total += weighted
            decisions.append(
                {
                    "policy_id": policy.policy_id,
                    "name": policy.name,
                    "evidence_score": evidence_score,
                    "weighted_score": weighted,
                    "satisfied": weighted >= policy.min_score,
                }
            )
        status = "approved" if all(item["satisfied"] for item in decisions) and total >= 70 else "needs_review"
        policy_hash = sha256(str(sorted((item["policy_id"], item["weighted_score"]) for item in decisions)).encode()).hexdigest()
        return {
            "engine": "policy_driven_trust",
            "trust_score": min(100, max(0, total)),
            "status": status,
            "policy_hash": policy_hash,
            "prompt_digest": prompt[:80],
            "decisions": decisions,
            "policies": self.policies(),
        }

    def evaluate_dsl(self, *, context: dict[str, Any], policy_name: str = "novascript_default_trust") -> dict[str, Any]:
        return get_policy_registry().evaluate(context=context, name=policy_name)


def _parse_value(raw: str) -> Any:
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        return raw.strip('"')


def _compare(actual: Any, operator: str, expected: Any) -> bool:
    if operator == "==":
        return actual == expected
    if operator == "!=":
        return actual != expected
    if operator == ">=":
        return int(actual) >= int(expected)
    if operator == "<=":
        return int(actual) <= int(expected)
    if operator == ">":
        return int(actual) > int(expected)
    if operator == "<":
        return int(actual) < int(expected)
    raise ValueError(f"unsupported operator: {operator}")


def _score_repository_graph(graph: dict[str, Any]) -> int:
    signals = graph.get("signals", {})
    file_count = int(signals.get("file_count", len(graph.get("nodes", []))))
    language_count = int(signals.get("language_count", 1))
    return min(100, 55 + min(file_count, 8) * 4 + min(language_count, 4) * 3)


def _score_architecture(architecture: dict[str, Any]) -> int:
    entries = architecture.get("entries", [])
    return min(100, 60 + len(entries) * 12)


def _score_debt(debt: dict[str, Any]) -> int:
    return max(0, 100 - int(debt.get("score", 0)))


_DEFAULT_POLICY_TRUST_ENGINE = PolicyDrivenTrustEngine()
_DEFAULT_POLICY_REGISTRY = PolicyRegistry()


def get_policy_trust_engine() -> PolicyDrivenTrustEngine:
    return _DEFAULT_POLICY_TRUST_ENGINE


def get_policy_registry() -> PolicyRegistry:
    return _DEFAULT_POLICY_REGISTRY
