"""Fail-closed validation for the NovaTech constitutional platform contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
import yaml

from afritech.core_platform.signing import verify_packet_signature
from afritech.platform_contracts.registry import (
    architecture_metrics,
    capability_graph,
    schema_registry_manifest,
)
from afritech.platform_contracts.runtime import (
    ApiLifecycle,
    ProductLifecycle,
    TrustLevel,
    VersionVector,
    validate_capability_dependencies,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = Path("afritech/platform_contracts/platform.yaml")
CONTRACT_SCHEMA = Path("afritech/platform_contracts/platform.schema.json")


class PlatformContractViolation(RuntimeError):
    """Raised when the platform's human and machine contracts drift."""


class PlatformContractValidator:
    def __init__(self, root: Path = ROOT) -> None:
        self.root = root

    def validate(self) -> bool:
        contract = self._yaml(CONTRACT)
        schema = self._json(CONTRACT_SCHEMA)
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(contract),
            key=lambda error: tuple(str(item) for item in error.absolute_path),
        )
        if errors:
            detail = "; ".join(error.message for error in errors)
            raise PlatformContractViolation(f"platform contract schema violation: {detail}")

        self._validate_paths(contract)
        self._validate_capabilities(contract)
        self._validate_trust_levels(contract)
        self._validate_lifecycles(contract)
        self._validate_versions(contract)
        self._validate_data_schemas(contract)
        self._validate_schema_publications(contract)
        self._validate_developer_artifacts(contract)
        self._validate_api_schema_alignment()
        self._validate_document_contract(contract)
        return True

    def _validate_paths(self, contract: dict[str, Any]) -> None:
        paths = [
            contract["constitution"],
            contract["root_contract"],
            contract["operations_contract"],
            *contract["companion_standards"],
            *contract["data_contracts"].values(),
            *contract["developer_artifacts"].values(),
        ]
        missing = [path for path in paths if not (self.root / path).is_file()]
        if missing:
            raise PlatformContractViolation(f"referenced platform files missing: {missing}")

    def _validate_capabilities(self, contract: dict[str, Any]) -> None:
        try:
            validate_capability_dependencies(contract["capabilities"])
        except ValueError as exc:
            raise PlatformContractViolation(str(exc)) from exc
        identifiers = {item["id"] for item in contract["capabilities"]}
        mandatory = {
            "infrastructure",
            "identity",
            "policy",
            "execution",
            "evidence",
            "replay",
            "federation",
            "products",
            "ai",
        }
        if not mandatory.issubset(identifiers):
            raise PlatformContractViolation(
                f"mandatory capabilities missing: {sorted(mandatory - identifiers)}"
            )

    def _validate_trust_levels(self, contract: dict[str, Any]) -> None:
        levels = contract["trust_levels"]
        expected = [(item.value, item.name) for item in TrustLevel]
        actual = [(item["level"], item["id"]) for item in levels]
        if actual != expected:
            raise PlatformContractViolation("trust levels must be contiguous and canonical")
        previous: set[str] = set()
        for item in levels:
            current = set(item["requires"])
            if not previous.issubset(current):
                raise PlatformContractViolation("trust-level requirements must be monotonic")
            previous = current

    def _validate_lifecycles(self, contract: dict[str, Any]) -> None:
        product_states = [item["state"] for item in contract["product_lifecycle"]]
        api_states = [item["state"] for item in contract["api_lifecycle"]]
        if product_states != [item.value for item in ProductLifecycle]:
            raise PlatformContractViolation("product lifecycle ordering is not canonical")
        if api_states != [item.value for item in ApiLifecycle]:
            raise PlatformContractViolation("API lifecycle ordering is not canonical")

    def _validate_versions(self, contract: dict[str, Any]) -> None:
        vector = VersionVector(**contract["version_vector"])
        if vector.platform != contract["version"] or vector.contract != contract["version"]:
            raise PlatformContractViolation(
                "platform and contract versions must match the root contract version"
            )

    def _validate_data_schemas(self, contract: dict[str, Any]) -> None:
        for name, relative_path in contract["data_contracts"].items():
            schema = self._json(Path(relative_path))
            try:
                Draft202012Validator.check_schema(schema)
            except Exception as exc:
                raise PlatformContractViolation(f"invalid {name} JSON Schema: {exc}") from exc
            if schema.get("additionalProperties") is not False:
                raise PlatformContractViolation(
                    f"{name} authoritative schema must fail closed on unknown fields"
                )

    def _validate_schema_publications(self, contract: dict[str, Any]) -> None:
        history_path = self.root / contract["developer_artifacts"]["schema_publications"]
        history = json.loads(history_path.read_text(encoding="utf-8"))
        current = schema_registry_manifest()
        published = history.get("schemas", {})
        for publication in current["schemas"]:
            name = publication["name"]
            if name not in published:
                raise PlatformContractViolation(f"schema publication missing: {name}")
            if published[name].get("sha256") != publication["schema_digest"]:
                raise PlatformContractViolation(f"schema publication digest drift: {name}")
            signed = {
                key: publication[key]
                for key in (
                    "name",
                    "schema_id",
                    "digest_algorithm",
                    "schema_digest",
                    "contract_version",
                )
            }
            if not verify_packet_signature(signed, publication["signature"]):
                raise PlatformContractViolation(f"schema publication signature invalid: {name}")

    def _validate_developer_artifacts(self, contract: dict[str, Any]) -> None:
        graph = capability_graph()
        if graph["acyclic"] is not True:
            raise PlatformContractViolation("capability graph must be acyclic")
        metrics = architecture_metrics()
        if metrics["overall"] < 100:
            raise PlatformContractViolation(
                f"platform architecture metrics below full compliance: {metrics}"
            )
        version = contract["version_vector"]
        for key in ("sdk_python", "sdk_typescript", "sdk_kotlin", "sdk_swift"):
            text = (
                self.root / contract["developer_artifacts"][key]
            ).read_text(encoding="utf-8")
            for value in version.values():
                if value not in text:
                    raise PlatformContractViolation(
                        f"{key} does not expose complete version vector"
                    )
        portal = (
            self.root / contract["developer_artifacts"]["developer_portal"]
        ).read_text(encoding="utf-8")
        for term in ("signed schema", "Version negotiation", "SDK artifacts"):
            if term not in portal:
                raise PlatformContractViolation(
                    f"developer portal missing contract surface: {term}"
                )

    def _validate_api_schema_alignment(self) -> None:
        from afritech.api.core_platform_api import GovernedRequestPayload

        model_schema = (
            GovernedRequestPayload.model_json_schema()
            if hasattr(GovernedRequestPayload, "model_json_schema")
            else GovernedRequestPayload.schema()
        )
        canonical = self._json(
            Path("afritech/platform_contracts/schemas/request.schema.json")
        )
        if set(model_schema.get("properties", {})) != set(canonical["properties"]):
            raise PlatformContractViolation(
                "governed request API fields drifted from canonical request schema"
            )
        if set(model_schema.get("required", ())) != set(canonical["required"]):
            raise PlatformContractViolation(
                "governed request API required fields drifted from canonical request schema"
            )
        if model_schema.get("additionalProperties") is not False:
            raise PlatformContractViolation(
                "governed request API must reject unknown fields"
            )

    def _validate_document_contract(self, contract: dict[str, Any]) -> None:
        root_text = (self.root / contract["root_contract"]).read_text(encoding="utf-8")
        constitution_text = (self.root / contract["constitution"]).read_text(encoding="utf-8")
        required_root_terms = (
            "Capability architecture",
            "Universal governed execution",
            "Trust levels",
            "Sovereign multi-tenancy",
            "AI governance",
            "Developer platform",
            "Version vector",
            "NovaFederation",
            "novatech_platform_contract_validator",
        )
        for term in required_root_terms:
            if term not in root_text:
                raise PlatformContractViolation(f"root contract missing section: {term}")
        for article in range(1, 11):
            roman = _roman(article)
            if f"Article {roman}" not in constitution_text:
                raise PlatformContractViolation(
                    f"platform constitution missing Article {roman}"
                )
        for path in contract["companion_standards"]:
            text = (self.root / path).read_text(encoding="utf-8").strip()
            if not text.startswith("# ") or len(text) < 300:
                raise PlatformContractViolation(f"companion standard is incomplete: {path}")

    def _yaml(self, relative_path: Path) -> dict[str, Any]:
        path = self.root / relative_path
        if not path.is_file():
            raise PlatformContractViolation(f"missing YAML contract: {relative_path}")
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise PlatformContractViolation(f"YAML contract must be an object: {relative_path}")
        return payload

    def _json(self, relative_path: Path) -> dict[str, Any]:
        path = self.root / relative_path
        if not path.is_file():
            raise PlatformContractViolation(f"missing JSON contract: {relative_path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise PlatformContractViolation(f"JSON contract must be an object: {relative_path}")
        return payload


def _roman(value: int) -> str:
    numerals = (
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )
    result = ""
    remaining = value
    for number, symbol in numerals:
        while remaining >= number:
            result += symbol
            remaining -= number
    return result


def validate(root: Path = ROOT) -> bool:
    return PlatformContractValidator(root).validate()


def main() -> int:
    try:
        validate()
    except (PlatformContractViolation, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"NovaTech platform contract validation FAILED: {exc}")
        return 1
    print("NovaTech platform contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
