"""Validate and summarize the mature AfriTech core pillar layers."""

from __future__ import annotations

from dataclasses import dataclass

from afritech.ci import afritech_constitution_v1_validator


class AfriTechCorePillarsValidationError(RuntimeError):
    """Raised when the mature AfriTech core pillar taxonomy is invalid."""


@dataclass(frozen=True)
class CorePillarSummary:
    pillar_id: str
    name: str
    layer_id: str
    layer_name: str
    layer_purpose: str
    summary: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "pillar_id": self.pillar_id,
            "name": self.name,
            "layer_id": self.layer_id,
            "layer_name": self.layer_name,
            "layer_purpose": self.layer_purpose,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class CorePillarLayerSummary:
    layer_id: str
    name: str
    purpose: str
    legitimacy_boundary: str
    pillars: tuple[CorePillarSummary, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "layer_id": self.layer_id,
            "name": self.name,
            "purpose": self.purpose,
            "legitimacy_boundary": self.legitimacy_boundary,
            "pillar_count": len(self.pillars),
            "pillars": [pillar.canonical_dict() for pillar in self.pillars],
        }


@dataclass(frozen=True)
class AfriTechCorePillarsReport:
    layers: tuple[CorePillarLayerSummary, ...]

    @property
    def pillar_count(self) -> int:
        return sum(len(layer.pillars) for layer in self.layers)

    @property
    def verified(self) -> bool:
        return len(self.layers) == 5 and self.pillar_count == 18

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": "afritech.core_pillars_validation_report.v1",
            "layer_count": len(self.layers),
            "pillar_count": self.pillar_count,
            "verified": self.verified,
            "layers": [layer.canonical_dict() for layer in self.layers],
        }


def validate() -> AfriTechCorePillarsReport:
    payload = afritech_constitution_v1_validator.load_constitution()
    afritech_constitution_v1_validator.validate()
    layers_payload = payload.get("core_pillar_layers")
    if not isinstance(layers_payload, list):
        raise AfriTechCorePillarsValidationError("core_pillar_layers missing")

    layers: list[CorePillarLayerSummary] = []
    for layer in layers_payload:
        if not isinstance(layer, dict):
            raise AfriTechCorePillarsValidationError("core pillar layer invalid")

        pillars_payload = layer.get("pillars")
        if not isinstance(pillars_payload, list):
            raise AfriTechCorePillarsValidationError(
                f"{layer.get('id')} pillars missing"
            )

        layer_id = str(layer["id"])
        layer_name = str(layer["name"])
        layer_purpose = str(layer["purpose"])
        pillars = tuple(
            CorePillarSummary(
                pillar_id=str(pillar["id"]),
                name=str(pillar["name"]),
                layer_id=layer_id,
                layer_name=layer_name,
                layer_purpose=layer_purpose,
                summary=str(pillar["summary"]),
            )
            for pillar in pillars_payload
            if isinstance(pillar, dict)
        )
        layers.append(
            CorePillarLayerSummary(
                layer_id=layer_id,
                name=layer_name,
                purpose=layer_purpose,
                legitimacy_boundary=str(layer["legitimacy_boundary"]),
                pillars=pillars,
            )
        )

    report = AfriTechCorePillarsReport(layers=tuple(layers))
    if not report.verified:
        raise AfriTechCorePillarsValidationError(
            "core pillar report must contain 5 layers and 18 pillars"
        )
    return report


def format_summary(report: AfriTechCorePillarsReport) -> str:
    lines = [
        "AfriTech core pillars validation PASSED",
        f"layer_count={len(report.layers)} pillar_count={report.pillar_count}",
    ]
    for layer in report.layers:
        lines.append(f"- {layer.name}: {layer.purpose}")
        for pillar in layer.pillars:
            lines.append(f"  - {pillar.name}: {pillar.summary}")
    return "\n".join(lines)


def main() -> int:
    try:
        report = validate()
    except AfriTechCorePillarsValidationError as exc:
        print(f"AfriTech core pillars validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
