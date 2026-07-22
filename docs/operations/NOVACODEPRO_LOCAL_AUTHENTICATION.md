# NovaCodePro local authentication runtime

## Supported local startup

Start the API from the repository root:

```bash
AFRITECH_ENV=test \
AFRITECH_JWT_SECRET=replace-with-a-local-secret \
./venv/bin/python -m uvicorn afritech.api.app:app --host 127.0.0.1 --port 8000
```

Start the frontend in another terminal:

```bash
cd novacodepro_portal
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

The Vite development server proxies same-origin `/v1` requests to `http://127.0.0.1:8000` by default. Override only when the API intentionally runs elsewhere:

```bash
VITE_NOVACODEPRO_PROXY_TARGET=http://127.0.0.1:18002 npm run dev -- --port 5173
```

`VITE_NOVACODEPRO_API_BASE_URL` remains available for an explicitly configured cross-origin API. Do not put credentials, tokens, or secrets in frontend environment variables.

## Route and API contract

Public authentication routes render before protected workspace bootstrap:

- `/novacodepro/login`
- `/novacodepro/forgot-password`
- `/novacodepro/reset-password`
- `/novacodepro/auth/callback`
- `/novacodepro/auth/help`

Protected routes verify the NovaID session through `GET /v1/novacodepro/session`, then resolve tenant, workspace and permissions. Login submits to `POST /v1/novacodepro/session/login`; refresh and logout use the matching `/refresh` and `/logout` operations. Cookies are sent with `credentials: include`; the frontend does not persist access or refresh tokens in local storage.

Only internal paths beginning `/novacodepro/` are accepted as `returnTo` destinations. Protocol-relative, external, malformed and public-auth destinations fall back to the dashboard.

## Health and smoke checks

```bash
curl -fsS http://127.0.0.1:8000/health
curl -i http://127.0.0.1:5173/novacodepro/login
cd novacodepro_portal
npx playwright test tests/browser/login-lifecycle.spec.js --project=chromium --reporter=line
```

## Troubleshooting `API_UNAVAILABLE`

1. Confirm the API responds at `/health` on the configured proxy target.
2. Confirm Vite was started from `novacodepro_portal` and inspect `VITE_NOVACODEPRO_PROXY_TARGET`.
3. Confirm `/v1/novacodepro/session` returns JSON, not the Vite base-path 404 page.
4. For cross-origin development, verify FastAPI allows the exact frontend origin and credentialed requests. Prefer the same-origin Vite proxy.
5. Confirm browser cookies are permitted for the host and that frontend/API hostnames are consistent; `localhost` and `127.0.0.1` are different cookie sites.
6. Use the displayed diagnostic reference when escalating. User-facing errors are deliberately sanitized and never contain stack traces or raw response objects.

An API outage does not replace the public login page. Sign-in attempts show the safe NovaID connectivity message while protected routes retain retry, sign-in and local-session recovery controls.
