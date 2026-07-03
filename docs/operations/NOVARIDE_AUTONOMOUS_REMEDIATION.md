# NovaRide Autonomous Architecture Remediation

## Purpose

NovaRide autonomous remediation diagnoses architecture validator failures and
generates bounded fix plans. It is a governance assistant, not an execution
authority.

## Commands

Generate a remediation plan:

```bash
python -m architecture_validator.remediation.cli --output architecture_remediation_report.json
```

Record governed remediation actions after approval:

```bash
python -m architecture_validator.remediation.cli --apply --output architecture_remediation_report.json
```

You can override the learning memory path with `--learning-memory`.

High-risk actions still require human review unless explicitly authorized.
The remediation system requires human approval for high-risk changes.

## API

The operator API exposes:

```text
/v1/architecture/remediation
```

Optional query parameters:

- `live=true` re-runs validation before planning remediation.
- `apply=true` records governed remediation actions.
- `allow_risky=true` records high-risk actions as authorized.

## Safety Model

The remediation system SHALL:

- generate deterministic remediation plans
- classify risk
- preserve validator authority
- require human approval for high-risk changes
- re-run validation after remediation

The remediation system SHALL NOT:

- silently edit production source
- bypass CI
- mutate production data
- approve its own high-risk fixes

## Dashboard

The operator dashboard displays:

- proposed fixes
- self-healing status
- plan source
- human approval count
- safe versus approval-required actions

## Continuous Learning

The remediation system records governed learning signals after approved
remediation runs. That learning layer tracks:

- issue frequency
- fix success rate
- knowledge graph relationships between issue and fix
- optimization suggestions for stable patterns

Learning memory is stored in `architecture_learning_memory.json` unless a
different path is configured by the validator runtime or CLI. The learning surface is
read-only to operators and can be inspected through:

- `/v1/architecture/learning`
- `/metrics/architecture/learning`

## CI

The architecture workflow publishes:

- `compliance_report.json`
- `architecture_remediation_report.json`

These artifacts support review, audit, and future remediation automation.
