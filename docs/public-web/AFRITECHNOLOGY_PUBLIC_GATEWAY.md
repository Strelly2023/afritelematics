# AfriTechnology Public Gateway

`afritechnology.com` is the canonical public corporate and product website. It
must not serve the AfriRide operator dashboard or any authenticated internal
workspace.

Implemented surfaces:

- `apps/public-web`: public React/Vite website with dynamic API loading and
  approved fallback content.
- `/v1/public/site`: governed public site metadata and navigation.
- `/v1/public/products`: governed product catalog records with lifecycle and
  availability labels.
- `/v1/public/trust`: public trust records with owner, scope, and evidence
  references.
- `/v1/public/status`: public status data that does not invent uptime.
- `/v1/public/search`: public product discovery.
- `/v1/public/contact-requests`: guided contact intake with reference tracking.

Routing rules:

- `afritechnology.com` and `www.afritechnology.com` are public website hosts.
- `app.afritechnology.com` is the customer application gateway and emits
  `X-Robots-Tag: noindex, nofollow`.
- `novacodepro.afritechnology.com` remains the NovaCodePro platform host.
- API and verification hosts remain separate from the public web experience.

Honest completion state:

- Repository implementation: complete for public gateway v1.
- Operational verification: pending live deployment checks.
- Human accessibility review: pending.
- Search indexing correction: pending crawler recrawl after deployment.
- Contact email/CRM delivery: API contract implemented; live provider routing
  pending credentials and production evidence.

