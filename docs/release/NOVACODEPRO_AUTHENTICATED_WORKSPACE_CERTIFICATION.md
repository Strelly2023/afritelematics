# NovaCodePro authenticated workspace certification

## Scope

Certified routes:

- `/novacodepro/workspace`
- `/novacodepro/projects`
- `/novacodepro/requests`

The routes share the NCP-003 authenticated application shell and use the existing tenant-scoped workspace, project, request, activity, notification, member, task, approval, attachment, comment, and lifecycle APIs.

## Root causes corrected

1. Successful bootstrap redirected registered protected routes to the default dashboard instead of preserving the requested URL.
2. Structured bootstrap rebuilt permissions from a base role definition and discarded effective session-policy permissions such as `project.read` and `request.create`.
3. Structured bootstrap replaced the selected session workspace with a synthetic role workspace, producing inconsistent workspace context.
4. The legacy NCP-003 presentation combined creation forms, duplicate navigation, and internal implementation labels instead of a coherent product shell.

## Route-state and authorization model

| Condition | Result |
| --- | --- |
| Bootstrap in progress | Loading shell; no authorization decision |
| Missing or expired session | Safe login redirect with internal `returnTo` |
| Valid session and required capability | Requested route renders |
| Valid session and explicit capability denial | Contextual access-denied screen |
| Missing workspace | Workspace-required state or selector |
| Network/service failure | Service-unavailable state, never forbidden |

The backend remains authoritative. The frontend registry uses the effective permissions returned by the canonical session bootstrap, and workspace selection rotates the server session before clearing and reloading workspace-scoped data.

## Validation

- Frontend unit/component suite: 124 passed, 3 existing skips.
- Focused backend authentication and NCP-003 API suite: 7 passed.
- Declared NCP E2E suite: 3 passed, 2 existing browser-runtime marker skips.
- Real Chromium suite: 9 passed.
- Production frontend build: passed.
- Real project creation: passed through `/v1/novacodepro/projects`.
- Real request creation: passed through `/v1/novacodepro/requests`.
- Limited-role negative authorization: passed; regulator denied `project.read` while retaining authorized workspace access.
- Responsive certification: 1440×900, 1280×800, 768×1024, and 390×844.

## Accessibility review

The shell includes a skip link, semantic header/nav/main landmarks, `aria-current` navigation, labelled form controls, visible focus indicators, responsive touch targets, accessible dialog labelling, status live regions, and reduced-motion behavior. Complex modal focus trapping remains a candidate for a shared accessible-dialog primitive as the broader platform shell is consolidated.

## Evidence

Screenshots are stored under `docs/evidence/novacodepro-authenticated/`. Playwright retains screenshots, video, and traces automatically on failure; the certified run completed without failure artifacts.

## Broader platform limitation

This certification covers the authenticated NCP-003 foundation and its real request/project flows. Existing Requirements, Design, Architecture, Development, Quality, Delivery, and Operations modules remain separate portal shells and require incremental migration to the shared command/navigation shell. No unsupported backend capability is represented as complete.
