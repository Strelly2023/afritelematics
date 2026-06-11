# AfriPro Workspace Verification

## Purpose

This verification flow closes the environment gaps that can make the AfriPro
workspace appear incomplete even when the implementation is present.

The required framework dependencies already live in the repository virtual
environment:

- `pytest`
- `fastapi`
- `django`

## One-command verification

Run:

```bash
scripts/run_afroprog_workspace_checks.sh
```

This executes:

- AfriPro workspace service tests
- AfriPro governance guard test
- FastAPI adapter tests
- Django runtime template smoke test
- AfriTech gateway architecture tests
- React dashboard production build

## Why the venv matters

Running `python3` directly may fail to import:

- `pytest`
- `fastapi`
- `django`

Use `venv/bin/python` for repo-backed verification so the tests run against the
intended local environment.
