# NovaTrust SOC2 Evidence Pack

Classification: submission-ready evidence index for auditor review.

## Scope

This pack covers the NovaTech trust evidence interface:

- public Trust Explorer
- audit PDF export
- Ed25519 signature endpoint
- compliance report endpoint
- deterministic anchor endpoint
- optional blockchain anchor adapter
- QR-style PNG verification image
- auditor ZIP bundle
- independent verifier CLI
- partner SDKs

It is an evidence package for review. It is not a SOC2 certification claim.

## Evidence Surfaces

```text
/trust/sandbox/demo
/trust/explorer/{trust_id}
/trust/explorer/{trust_id}/audit.pdf
/trust/explorer/{trust_id}/signature
/trust/explorer/{trust_id}/compliance-report
/trust/explorer/{trust_id}/anchor
/trust/explorer/{trust_id}/anchor/blockchain
/trust/explorer/{trust_id}/qr.png
/trust/explorer/{trust_id}/bundle.zip
/trust/auditor/dashboard?ids={id1},{id2}
```

## Control Mapping

| Control Area | NovaTrust Evidence | Review Procedure |
| --- | --- | --- |
| CC6 Access Controls | Public endpoints are read-only verification surfaces | Confirm no public endpoint mutates execution state |
| CC7 Monitoring | Auditor dashboard batches verification outcomes | Validate multi-receipt dashboard output |
| CC8 Change Management | CLI and SDKs verify immutable packet/signature pairs | Run `novatrust-verify` against a sandbox trust ID |
| CC9 Risk Mitigation | Deterministic anchor and optional blockchain adapter separate internal and external anchoring | Confirm `/anchor/blockchain` is disabled unless configured |
| Processing Integrity | Ed25519 signature verifies canonical packet payload | Verify `payload_hash` and signature using CLI or SDK |
| Confidentiality Boundary | Public artifacts contain verification evidence only | Review packet fields for secret material |
| Availability Evidence | ZIP bundle supports offline review | Download and inspect `bundle.zip` contents |

## Auditor Procedure

1. Open `/trust/sandbox/demo`.
2. Open the `explorer` link for `sandbox-demo`.
3. Download `audit.pdf`.
4. Fetch `signature`.
5. Fetch `compliance-report`.
6. Fetch `anchor`.
7. Confirm `/anchor/blockchain` reports `disabled` unless configured.
8. Download `bundle.zip`.
9. Run:

```bash
novatrust-verify \
  --base-url http://16.176.215.89 \
  --trust-id sandbox-demo \
  --write-dir ./verification-output
```

10. Confirm `NovaTrust verification: PASS`.

## Bundle Contract

```text
packet.json
signature.json
anchor.json
compliance-report.json
audit.pdf
verification-qr.png
README.txt
```

## Accuracy Boundaries

- The QR artifact is a QR-style PNG verification image, not a
  standards-compliant QR code.
- The deterministic anchor is not yet an external notarization system.
- The optional blockchain anchor adapter is disabled unless an external
  publisher is explicitly configured.
- SOC2 evidence mapping is review-ready, not a certification statement.

## Partner Verification SDKs

Python:

```python
from afritech.sdk.novatrust import NovaTrustClient

result = NovaTrustClient("http://16.176.215.89").verify("sandbox-demo")
assert result.verified
```

JavaScript:

```js
import { NovaTrustClient } from "./novatrust-js/index.js";

const client = new NovaTrustClient({ baseUrl: "http://16.176.215.89" });
const result = await client.verify("sandbox-demo");
console.log(result.signatureVerified);
```
