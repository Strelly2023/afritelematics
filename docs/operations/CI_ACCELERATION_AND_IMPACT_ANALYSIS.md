# CI Acceleration and Impact Analysis

This repository uses a two-track CI model:

- Fast CI for normal commits and pull requests.
- Full CI for nightly, release, protected-branch, and manual certification flows.

## Fast CI

Fast CI is driven by:

- `afritech.ci.impact`
- `afritech.ci.run_selected_tests`
- `.github/workflows/fast-ci.yml`

It performs:

- compile and lint checks
- four-gate validation
- runtime-boundary governance validation
- secret scan
- documentation link validation
- impacted pytest suites only
- impacted npm typechecks/builds only
- `git diff --check`

The impact analyzer reads:

- `git diff --name-only`
- `ci/impact/dependency_graph.yml`
- `ci/test_suites.yml`

It writes:

- `ci_artifacts/impact_plan.json`
- `ci_artifacts/impact_summary.md`

## Full CI

Full CI is the certification path.
It runs:

- full pytest
- dashboard build
- rider typecheck
- driver typecheck
- Android validation
- iOS validation when credentials exist
- docs link check
- secret scan
- governance validators
- proof and replay validators
- `git diff --check`

Full CI runs on:

- nightly schedule
- release branches
- protected branches
- manual dispatch

## Cache strategy

The workflows cache:

- pip
- npm
- Gradle
- pytest cache
- mypy cache
- ruff cache
- Expo cache
- Docker/buildx cache

## Safety rules

These checks are never skipped:

- architecture boundary checks
- four-gate validation
- runtime-boundary governance validation
- secret scan
- `git diff --check`

The analyzer forces full validation when changes touch:

- `afritech/constitution`
- `afritech/guards`
- `afritech/ci`
- replay / proof / trust code
- payments / ledger / settlement code
- auth / security code
- deployment files
- database migrations
- GitHub workflows
- dependency files
- release configs

## Manual override

To force full certification locally:

```bash
python -m pytest -n auto
python -m afritech.ci.four_gate_validator
python -m afritech.guards.guard_runtime_boundary_governance --fail-on-drift
python -m afritech.ci.secret_scan
python -m afritech.ci.docs_link_validator
git diff --check
```
