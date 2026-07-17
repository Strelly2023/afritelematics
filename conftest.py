from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DJANGO_APP = ROOT / "afriride_system/django_app"
PYTEST_RUNTIME = Path(
    os.environ.get("AFRITECH_PYTEST_RUNTIME", f"/tmp/afritech-pytest-{os.getpid()}")
)
PYTEST_WORKER = os.environ.get("PYTEST_XDIST_WORKER")
if PYTEST_WORKER:
    PYTEST_RUNTIME = PYTEST_RUNTIME / PYTEST_WORKER
PYTEST_RUNTIME.mkdir(parents=True, exist_ok=True)

# API modules construct persistent repositories at import time. Keep collection
# isolated from production filesystem defaults and from the tracked db.sqlite3.
_runtime_environment = {
    "NOVATECH_RUNTIME_CONTROL_SQLITE_PATH": PYTEST_RUNTIME / "runtime-control.sqlite3",
    "NOVATECH_EVIDENCE_ROOT": PYTEST_RUNTIME / "runtime-evidence",
    "AFRIRIDE_DB_PATH": PYTEST_RUNTIME / "pilot-state.sqlite3",
}
for _name, _path in _runtime_environment.items():
    if PYTEST_WORKER:
        # The controller's generated paths are inherited by xdist workers.
        # Override them so workers never share mutable runtime state.
        os.environ[_name] = str(_path)
    else:
        os.environ.setdefault(_name, str(_path))
os.environ.setdefault("AFRIPAY_CELERY_ALWAYS_EAGER", "1")

if str(DJANGO_APP) not in sys.path:
    sys.path.insert(0, str(DJANGO_APP))


def pytest_configure() -> None:
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "afriride_system.django_app.config.settings",
    )

    try:
        import django
        from django.apps import apps
    except ModuleNotFoundError:
        return

    if not apps.ready:
        django.setup()

    # Database creation belongs to pytest-django's django_db setup. Accessing the
    # connection during pytest_configure bypasses its blocker and makes clean
    # environments fail before collection.
