# NovaCodePro authentication entry repair

Date: 2026-07-23

## Confirmed root cause

`App.jsx` called `GET /v1/novacodepro/session` unconditionally before evaluating the public login route. The recovery branch was also evaluated before the signed-out/login branch. On an ordinary port-5173 Vite start, the development proxy was absent unless `VITE_NOVACODEPRO_PROXY_TARGET` had been supplied. The request therefore reached Vite, which returned a plain-text base-path 404. `fetchBootstrap` converted its object-shaped failure with `String(error)`, producing `[object Object]`; `App` then rendered `API_UNAVAILABLE` instead of the login page.

Captured pre-fix response:

- Request: `GET http://127.0.0.1:15174/v1/novacodepro/session`
- Status: `404`
- Content type: `text/plain`
- Body: Vite reported that its public base URL was `/novacodepro/`

## Repair

- Public authentication paths render independently while background session verification remains fail-safe.
- Protected bootstrap begins only for protected routes or redirects a verified existing session.
- The default Vite `/v1` proxy targets the repository-standard API port 8000 and remains environment-overridable.
- `returnTo` accepts only validated internal protected NovaCodePro destinations.
- Authentication and recovery failures use a typed normalized model, safe messages and diagnostic references.
- Passwords start empty, are never logged or locally persisted, and are cleared after failed or successful submission; usernames remain available after a failed attempt.
- Existing credentialed cookie, refresh, logout, tenant, workspace and permission behavior is preserved.
- `npm run dev` now health-gates and launches the local FastAPI service before Vite; `npm run dev:frontend` preserves the previous frontend-only workflow for managed backends and Playwright.

## Browser certification

The real-service Playwright lifecycle covers direct login, public bootstrap isolation, keyboard order, invalid credentials, password clearing, successful NovaID login, session persistence after refresh, logout, protected-route redirection, open-redirect rejection, mobile usability, console/page errors and raw-object absence.

Evidence screenshots:

- `docs/evidence/novacodepro-login/desktop-1440.png`
- `docs/evidence/novacodepro-login/desktop-1280.png`
- `docs/evidence/novacodepro-login/tablet.png`
- `docs/evidence/novacodepro-login/mobile.png`
- Matching `-full.png` files retain the complete scrollable page at each viewport.

The screenshots use the repository's existing NovaCodePro image because the separately requested official `/branding/logos/NovaCodePro.png` asset is still unavailable.
