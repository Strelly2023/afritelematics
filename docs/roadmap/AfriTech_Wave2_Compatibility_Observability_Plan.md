# AfriTech Wave 2 Compatibility Observability Plan

## Document Classification

```text
STATUS: WAVE 2 STARTER ARTIFACT
CLASSIFICATION: HUMAN COMPREHENSIBILITY AND COMPATIBILITY OBSERVABILITY PLAN
ROLE: MAKE EPOCHS, TRANSLATORS, AND REPLAY COMPATIBILITY UNDERSTANDABLE
BOUNDARY: OBSERVATION ONLY; DOES NOT DEFINE LEGITIMACY OR REPLAY TRUTH
```

Wave 1 established machine-enforced compatibility containment:

```text
policy -> registry -> validator -> tests -> GA gate
```

Wave 2 must now make that containment understandable to humans.

## Core Rule

```text
Compatibility dashboards explain semantic survivability.
They do not define semantic survivability.
```

Constitution defines legitimacy. Replay validates truth. Compatibility observability explains how historical replay remains accessible.

## Problem Statement

AfriTech is now:

1. temporally aware
2. semantically versioned
3. replay-governed
4. compatibility-contained
5. lifecycle-regulated

Without visualization, contributors will struggle to reason safely about:

1. active epochs
2. legacy-supported epochs
3. translator paths
4. fixture health
5. compatibility budgets
6. semantic lineage
7. retirement eligibility

The next risk is not correctness. It is human comprehensibility under correctness.

## Required Views

### 1. Epoch Lineage View

Purpose:

```text
Show the historical semantic path of AfriTech.
```

Must display:

1. epoch id
2. lifecycle status
3. active interface versions
4. accepted trace policy
5. fixture status
6. retirement eligibility

Operator questions answered:

1. Which epoch is active?
2. Which epochs are legacy-supported?
3. Which epochs are sealed or retired?
4. Which interfaces belong to each epoch?

### 2. Translator Map

Purpose:

```text
Show how old replay contexts remain accessible.
```

Must display:

1. source epoch
2. target interface
3. translator lifecycle status
4. compatibility class
5. fixture status
6. owner
7. retirement path
8. budget exception status

Operator questions answered:

1. Which translators exist?
2. Why does each translator exist?
3. Is any translator missing fixtures?
4. Has translator budget been exceeded?

### 3. Compatibility Health Dashboard

Purpose:

```text
Summarize whether semantic survivability is healthy.
```

Must show:

1. active epoch count
2. legacy-supported epoch count
3. active translator count
4. deprecated translator count
5. fixture failures
6. budget exceptions
7. retired epoch references
8. GA gate status

Health states:

| State | Meaning |
| --- | --- |
| Green | registries valid, fixtures passing, no budget violations |
| Amber | deprecated translators, retirement warnings, pending fixtures |
| Red | lifecycle invalid, budget exceeded, missing fixtures, retired epoch in active use |

### 4. Replay Failure Explanation View

Purpose:

```text
Translate compatibility failures into operator-understandable causes.
```

Example mapping:

| Failure | Human explanation |
| --- | --- |
| `MISSING_EPOCH_METADATA` | The trace does not declare which semantic rules should replay it. |
| `UNSUPPORTED_INTERFACE_VERSION` | This trace uses an interface version no longer available on the active replay path. |
| `TRANSLATOR_FIXTURES_MISSING` | A required translator exists but has not proven compatibility through fixtures. |
| `TRANSLATOR_BUDGET_EXCEEDED` | Multiple translators exist for the same source epoch and interface without approval. |
| `RETIRED_EPOCH_REFERENCED` | Active evidence still points to an epoch marked retired. |

### 5. Retirement Readiness View

Purpose:

```text
Prevent historical replay loss during lifecycle cleanup.
```

Must show:

1. trace populations by epoch
2. active operational dependencies
3. fixture archive status
4. legal or audit retention flags
5. historical access policy
6. operator warning status

Retirement may not proceed unless every safeguard is green.

## Data Sources

Initial dashboard data comes from:

1. `afritech/constitution/evolution/epoch_lifecycle_registry.yaml`
2. `afritech/constitution/evolution/replay_translator_registry.yaml`
3. `afritech/ci/epoch_lifecycle_validator.py`
4. compatibility fixture results
5. GA workflow results
6. future replay trace population index

No dashboard may infer hidden epoch state from runtime environment.

## Interaction Rules

Dashboards may:

1. display registry state
2. display validation state
3. display fixture state
4. explain failures
5. link to policies and source files
6. export diagnostic reports

Dashboards may not:

1. change epoch lifecycle status
2. approve translator exceptions
3. mutate compatibility fixtures
4. override validator failures
5. reinterpret replay results
6. declare constitutional legitimacy

## Guided Diagnostics

Every compatibility failure should include:

1. failure code
2. human explanation
3. affected epoch or translator
4. source registry file
5. required fix
6. command to revalidate

Example:

```text
Failure:
TRANSLATOR_FIXTURES_MISSING

Meaning:
Translator T-EPOCH-0-REPLAY is ACTIVE but fixture_status is not PASSING.

Fix:
Add compatibility fixtures or move translator back to PROPOSED.

Validate:
python3 -m afritech.ci.epoch_lifecycle_validator
```

## Wave 2 MVP Scope

The first implementation should be small:

1. read epoch lifecycle registry
2. read replay translator registry
3. run or display epoch lifecycle validator result
4. render epoch lineage table
5. render translator map table
6. render compatibility health summary
7. show guided diagnostics for validation failures

Out of scope for MVP:

1. mutating registry state
2. approving exceptions
3. editing epochs
4. editing translators
5. executing migrations
6. retiring epochs

## CLI Companion

Add a read-only CLI command:

```bash
python3 -m afritech.tools.compat_status status
```

Expected output:

```text
Compatibility health: green
Epoch lifecycle: valid
Active epochs: 1
Legacy-supported epochs: 0
Retired epochs: 0
Translators: 0
Deprecated translators: 0
Budget violations: 0
Fixture failures: 0
```

JSON output is available for automation:

```bash
python3 -m afritech.tools.compat_status status --format json
```

The CLI may return nonzero if validation fails, but it must not repair state.

In the GA gate, this command is a non-blocking reporting surface after the
blocking epoch lifecycle validator. The validator enforces compatibility
containment; the status command explains the current state.

## Observability Authority Guard

Compatibility observability has its own executable boundary check:

```bash
python3 -m afritech.ci.observability_authority_validator
```

This validator ensures compatibility observability surfaces remain:

1. read-only
2. non-authoritative
3. scoped to `OBSERVATION_ONLY`
4. forbidden from mutating epoch or translator registries
5. forbidden from approving exceptions
6. forbidden from validating truth or defining legitimacy

The compatibility status report stays non-blocking because it explains state.
The observability authority validator is blocking because it protects the
explanation surface from becoming governance.

## Success Criteria

Wave 2 compatibility observability is successful when:

1. a contributor can identify the active epoch in under one minute
2. a contributor can see all translators and their lifecycle status
3. a translator budget violation has a human-readable explanation
4. missing fixtures point to the affected translator
5. retired epoch references are visible
6. dashboard output matches the validator result
7. no UI or CLI surface can mutate compatibility state

## Final Boundary

Compatibility observability makes semantic survivability understandable.

```text
Dashboards explain.
Validators enforce.
Replay validates truth.
Constitution defines legitimacy.
```
