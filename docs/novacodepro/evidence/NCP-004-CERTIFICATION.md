# NCP-004 Certification Evidence

Certification level: internal implementation verified

Evidence:

- deterministic governed AI execution flow is implemented in `afritech/novacodepro/ncp004.py`
- API router is mounted at `/v1/novacodepro/ai`
- portal shell renders the NovaAI workspace in `novacodepro_portal/src/novacodepro/NCP004Portal.jsx`
- regression tests pass for backend and portal surfaces

Current blocker:

- full browser-based E2E certification is blocked by the absence of a browser automation framework in the local repository
