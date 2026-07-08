# Controlled Pilot Exit Criteria

Goal is to validate core workflows, security controls, RBAC, device trust, identity verification, payment flows, audit logs, and support processes.

Typical users: internal staff, trusted partners, selected drivers, selected merchants, test consumers, operations team.

Characteristics: approved users only, approved drivers only, approved merchants only, approved devices only, restricted access lists, simulated or tightly controlled payments, internal operational oversight, limited test geography, high-touch support.

Controlled Pilot exits only when:

- controlled-pilot tests passing, safety controls verified, no critical defects, governance approval granted.
- Access control passes for approved users and devices.
- NovaRide, NovaPay, and NovaID pilot flows pass.
- Cash procedure is validated.
- Monitoring and support are working.
- Incident response is tested.
- APK distribution is controlled-only and documented.
- No payment-safety violation remains.
- General availability remains false unless explicitly approved.
- Governance approval is granted.

## Do not exit if

- Any live payment path is active without approval.
- Any unapproved user, device, or operator can access pilot flows.
- Any critical incident is unresolved.
