# AFRITECH Public Pilot Security Hardening

## Scope

This document defines the minimum security baseline for public-pilot operations.

## Controls

- Rate limiting on public and API surfaces
- Security headers on all HTTPS responses
- fail2ban for brute-force and noisy client containment
- TLS certificate renewal and expiry monitoring
- Strict secret handling via environment files and mounted secrets
- SSH hardening with key-only access and restricted source IPs
- API abuse controls on auth, payment, identity, and support endpoints

## Operational Expectations

- Do not expose production credentials outside governed deployment flows.
- Keep payment, identity, and support boundaries separated by service responsibility.
- Treat public-pilot logs as operational evidence, not free-form debug output.

## Review Gate

Any change to TLS, ingress, identity, payment, or support handling must be reviewed against this hardening baseline before public-pilot rollout.
