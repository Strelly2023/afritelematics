from __future__ import annotations

from afritech.ci import (
    afriprog_design_invariant_validator,
    afriprog_dip_validator,
    afriprog_isp_validator,
    afriprog_lsp_validator,
    afriprog_ocp_validator,
    afriprog_srp_validator,
)
from afritech.design.solid import validate_solid_design
from afritech.design.uml import parse_uml, uml_to_proposal, validate_uml_design
from afritech.design.uml.uml_to_proposal import DESIGN_REQUIRED_VALIDATORS


def test_solid_design_validation_is_non_authoritative() -> None:
    validation = validate_solid_design(
        {
            "modules": ({"name": "FeedingService", "responsibilities": ("feeding",)},),
            "change_targets": ({"name": "IoTFeeding", "type": "domain_model", "mode": "extension"},),
            "inheritance": (
                {
                    "child": "AutoFeeding",
                    "parent_behaviors": ("schedule",),
                    "child_behaviors": ("schedule", "measure"),
                },
            ),
            "interfaces": ({"name": "Feeder", "unused_methods": ()},),
            "dependencies": ({"consumer": "FeedingService", "dependency_type": "interface"},),
        }
    )

    assert validation["valid"] is True
    assert validation["max_severity"] == "INFO"
    assert validation["findings"] == ()
    assert validation["authority"] == "design_quality_non_authoritative"
    assert validation["governance_required"] is True
    assert validation["activation_allowed"] is False
    assert validation["runtime_mutation_allowed"] is False


def test_solid_design_blocks_core_modification_and_mixed_responsibility() -> None:
    validation = validate_solid_design(
        {
            "modules": ({"name": "FarmService", "responsibilities": ("feeding", "finance")},),
            "change_targets": ({"name": "runtime_gate", "type": "runtime", "mode": "modification"},),
            "inheritance": (),
            "interfaces": (),
            "dependencies": (),
        }
    )

    assert validation["valid"] is False
    assert validation["max_severity"] == "CRITICAL"
    assert any("exactly one responsibility" in item for item in validation["violations"])
    assert any("protected runtime" in item for item in validation["violations"])
    assert {"principle": "SRP", "severity": "MAJOR", "message": "FarmService must declare exactly one responsibility"} in validation["findings"]
    assert {
        "principle": "OCP",
        "severity": "CRITICAL",
        "message": "runtime_gate modifies protected runtime instead of extending it",
    } in validation["findings"]


def test_uml_validation_embeds_solid_readiness() -> None:
    model = parse_uml("Farm\n- name\nChicken\n- age\n+ layEgg()", diagram_type="class")
    validation = validate_uml_design(model)

    assert validation["valid"] is True
    assert validation["solid_validation"]["valid"] is True
    assert validation["solid_validation"]["governance_required"] is True
    assert validation["activation_allowed"] is False


def test_uml_to_proposal_preserves_governed_design_boundary() -> None:
    model = parse_uml("FeedingSchedule\n- interval\n+ assignFeed()", diagram_type="class")
    proposal = uml_to_proposal(model).canonical_dict()

    assert "FeedingSchedule" in proposal["intent"]
    assert set(DESIGN_REQUIRED_VALIDATORS).issubset(set(proposal["required_validators"]))
    assert proposal["governance_required"] is True
    assert proposal["activation_allowed"] is False
    assert proposal["runtime_mutation_allowed"] is False
    assert proposal["replay_required"] is True
    assert proposal["rollback_required"] is True


def test_solid_validators_pass_directly() -> None:
    afriprog_srp_validator.validate()
    afriprog_ocp_validator.validate()
    afriprog_lsp_validator.validate()
    afriprog_isp_validator.validate()
    afriprog_dip_validator.validate()
    afriprog_design_invariant_validator.validate()
