# API contract

Implemented in `afritech.novaid.api`: `/register`, `/verify`, `/authenticate`, `/mfa/verify`, and `/token/refresh`. Requests require tenant, correlation, and request headers; registration also requires idempotency. Authentication failures are generic. Remaining Phase 3 endpoints and trusted tenant derivation from authenticated claims remain incomplete.
