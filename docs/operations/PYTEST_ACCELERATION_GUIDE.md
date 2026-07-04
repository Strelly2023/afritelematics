# Pytest Acceleration Guide

This repository uses two testing modes:

- fast developer feedback for day-to-day changes
- full certification for release and governed validation

Fast tests are only a shortcut. They do not replace release validation.

## Registered markers

The repository registers these markers in `pytest.ini`:

- `fast`
- `unit`
- `integration`
- `contract`
- `governance`
- `slow`
- `mobile`
- `dashboard`
- `payments`
- `novapay`
- `novaride`
- `identity`
- `trust`
- `release`
- `serial`

## Daily commands

```bash
make test-fast
make test-changed
make test-lf
pytest -k "novapay and not slow"
```

### Fast command

```bash
pytest -m "not slow and not integration and not contract and not release"
```

Use this for local feedback when you are not changing governed release surfaces.

### Changed-file command

```bash
make test-changed
```

This runs the CI impact analyzer, writes:

- `ci_artifacts/impact_plan.json`
- `ci_artifacts/impact_summary.md`

and then executes only the impacted test suites.

If the analyzer detects sensitive paths, the command escalates to full release validation.

### Last-failed command

```bash
make test-lf
```

If pytest has no last-failed cache yet, the command falls back to the fast developer command.

## Full certification commands

```bash
make test-full
make test-release
```

`make test-full` runs:

```bash
python3 -m pytest -q --maxfail=0
```

`make test-release` starts with the same full pytest command and then runs:

- full pytest
- four-gate validation
- runtime-boundary validation
- secret scan
- docs validation
- dashboard build
- rider typecheck
- driver typecheck
- `git diff --check`

## Governance rule

Fast tests are for developer feedback only.
They must not be used to claim release readiness.

Release readiness requires `make test-release`.
