# NovaRide architecture update

The repository now has a complete buildable operations package (`apps/novaride-operations`) with a Vite entrypoint and package-local tests.
The canonical runtime and auth surfaces remain:
- `afritech/api/app.py`
- `afritech/novaride_runtime/*`
- `afritech/novaid/*`
- `afriride_system/django_app/apps/afripay/*`

The major remaining constraints are operational and external rather than missing local code paths.
