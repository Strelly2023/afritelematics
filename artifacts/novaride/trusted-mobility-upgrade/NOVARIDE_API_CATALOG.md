# NovaRide API catalog

- NovaID runtime and audit replay routes are mounted from `afritech/api/app.py`.
- NovaRide runtime routes remain under the canonical FastAPI app and `afritech/novaride_runtime_api.py`.
- AfriPay/NovaPay auth middleware now resolves role-token auth from the current configured secret.
- NovaCodePro and public web surfaces remain wired and tested.
