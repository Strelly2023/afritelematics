# NovaTrust Partner SDK Guide

The NovaTrust SDKs consume only public, read-only verification endpoints.

## Public Contract

```text
/trust/explorer/{trust_id}
/trust/explorer/{trust_id}/signature
/trust/explorer/{trust_id}/compliance-report
/trust/explorer/{trust_id}/anchor
/trust/explorer/{trust_id}/anchor/blockchain
/trust/explorer/{trust_id}/bundle.zip
```

The explorer endpoint returns HTML by default. SDK and CLI clients request JSON
with:

```text
Accept: application/json
```

## Python

```python
from afritech.sdk.novatrust import NovaTrustClient

client = NovaTrustClient("http://16.176.215.89")
result = client.verify("sandbox-demo")

print(result.verified)
print(result.bundle_url)
```

## JavaScript

```js
import { NovaTrustClient } from "./novatrust-js/index.js";

const client = new NovaTrustClient({ baseUrl: "http://16.176.215.89" });
const result = await client.verify("sandbox-demo");

console.log(result.signatureVerified);
console.log(result.bundleUrl);
```

## Verification Boundary

The SDK verifies packet/signature integrity. It does not grant execution
authority and does not call private NovaTech APIs.
