from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RULE = ROOT / "afritech/governance/rules/RULE-NOVACODEPRO-GOVERNANCE-GATES.yaml"
OLD_RULES = (
    ROOT / "afritech/governance/rules/RULE-NOVACODEPRO-ACCESSIBILITY-GATE.yaml",
    ROOT / "afritech/governance/rules/RULE-NOVACODEPRO-EXECUTIVE-APPROVAL.yaml",
    ROOT / "afritech/governance/rules/RULE-NOVACODEPRO-OBSERVABILITY-EVIDENCE.yaml",
    ROOT / "afritech/governance/rules/RULE-NOVACODEPRO-PAYMENT-ACTIVATION.yaml",
    ROOT / "afritech/governance/rules/RULE-NOVACODEPRO-PRR-APPROVAL.yaml",
    ROOT / "afritech/governance/rules/RULE-NOVACODEPRO-VISUAL-REGRESSION-GATE.yaml",
)


def test_novacodepro_governance_gates_are_consolidated() -> None:
    payload = yaml.safe_load(RULE.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)

    assert payload["id"] == "RULE-NOVACODEPRO-GOVERNANCE-GATES"
    assert payload["status"] == "active"
    assert payload["scope"] == "novacodepro/release"
    assert payload["effective_version"] == 1

    consolidated_from = payload["consolidated_from"]
    assert tuple(consolidated_from) == tuple(str(path.relative_to(ROOT)) for path in OLD_RULES)

    rule_texts = payload["rules"]
    assert isinstance(rule_texts, list)
    assert len(rule_texts) == 6
    assert any("Accessibility verification requires executed tools" in item for item in rule_texts)
    assert any(
        "Real payment activation requires independent finance" in item
        for item in rule_texts
    )

    legacy = payload["legacy_rule_catalog"]
    assert isinstance(legacy, list)
    assert {entry["id"] for entry in legacy} == {
        "RULE-NOVACODEPRO-ACCESSIBILITY-GATE",
        "RULE-NOVACODEPRO-EXECUTIVE-APPROVAL",
        "RULE-NOVACODEPRO-OBSERVABILITY-EVIDENCE",
        "RULE-NOVACODEPRO-PAYMENT-ACTIVATION",
        "RULE-NOVACODEPRO-PRR-APPROVAL",
        "RULE-NOVACODEPRO-VISUAL-REGRESSION-GATE",
    }


def test_removed_novacodepro_rule_files_are_gone() -> None:
    assert all(not path.exists() for path in OLD_RULES)
