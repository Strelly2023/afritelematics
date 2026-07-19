# Governance YAML Consolidation Plan

## Summary

- Active governance YAML files before consolidation: 154
- Active governance YAML files after consolidation: 149
- Consolidated registry: `afritech/governance/rules/RULE-NOVACODEPRO-GOVERNANCE-GATES.yaml`

## Consolidated files

- `afritech/governance/rules/RULE-NOVACODEPRO-ACCESSIBILITY-GATE.yaml`
- `afritech/governance/rules/RULE-NOVACODEPRO-EXECUTIVE-APPROVAL.yaml`
- `afritech/governance/rules/RULE-NOVACODEPRO-OBSERVABILITY-EVIDENCE.yaml`
- `afritech/governance/rules/RULE-NOVACODEPRO-PAYMENT-ACTIVATION.yaml`
- `afritech/governance/rules/RULE-NOVACODEPRO-PRR-APPROVAL.yaml`
- `afritech/governance/rules/RULE-NOVACODEPRO-VISUAL-REGRESSION-GATE.yaml`

## Rationale

These documents were lightweight NovaCodePro release-gate fragments with overlapping policy intent. The consolidation keeps every requirement, preserves the original rule identifiers in `legacy_rule_catalog`, and exposes one canonical active registry for the release gates.

## Validation gates

- Governance size validator must pass with the active YAML count at or below 150.
- Regression tests must confirm the consolidated file contains all six legacy rules.
- Removed leaf files must no longer exist in the active governance tree.
- No current code, tests, or docs reference the removed leaf file paths.
