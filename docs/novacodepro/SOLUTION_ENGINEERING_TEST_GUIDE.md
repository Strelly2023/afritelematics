# Solution Engineering Test Guide

Run the portal checks from `novacodepro_portal`:

```bash
npm test
npm run build
```

Run the backend contract suite that the portal depends on:

```bash
python -m pytest -q \
  tests/novacodepro/test_solution_engineering.py \
  tests/novacodepro/test_workflow_fabric.py \
  afritech/tests/api/test_novacodepro_service_processes.py
```

The browser smoke script lives at `scripts/novacodepro/verify_solution_portal.sh`.
