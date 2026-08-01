# NovaID authoritative route map

Durable routes under `/v1/novaid`: `register`, `verify`, `authenticate`, `mfa/challenge`, `mfa/verify`, `token/refresh`, `me`, `sessions`, session revoke, `logout`, `logout-all`, `password/change`, `password/reset/request`, and `password/reset/complete`.

Compatibility-only deprecated routes: `/v1/novaid/legacy/auth` and `/v1/novaid/legacy/sessions`. No duplicate durable/legacy path-and-method pair was found in the composed NovaID routers.
