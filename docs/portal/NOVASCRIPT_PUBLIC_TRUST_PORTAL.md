# NovaScript Public Trust Portal

## 1. Overview

The NovaScript Public Trust Portal provides read-only access to verifiable trust artifacts for:

```text
customers
partners
auditors
regulators
```

## 2. Purpose

The portal exists to answer:

```text
Can this system be trusted?
Can its evidence be independently verified?
```

## 3. Core Principles

```text
read-only access
deterministic verification
no runtime dependency
no hidden logic
```

## 4. Public Endpoints

## 4.1 Receipt Verification

```http
GET /public/trust/{receipt_id}
```

Returns:

```text
receipt
verification result
signature validation
```

Proves:

```text
receipt is valid
receipt signature matches
fields are deterministic
```

Does not prove:

```text
correctness of code
production approval
legal compliance
```

## 4.2 Portable Verification Package

```http
GET /public/trust/{receipt_id}/package
```

Returns:

```text
receipt hash
certificate hash
assurance hash
proof hash
verification manifest
```

Proves:

```text
package can be validated offline
artifact integrity is preserved
NovaScript runtime is not required
```

## 4.3 Certificate Verification

```http
GET /public/certificates/{certificate_id}
```

Returns:

```text
certificate
certificate_hash
public key hash
issuer
subject
scope
```

Proves:

```text
certificate exists
certificate linkage is intact
issuer and subject are verifiable
```

## 4.4 Assurance Verification

```http
GET /public/assurance/{report_id}
```

Returns:

```text
assurance report
verification result
report hash
```

Proves:

```text
assurance report exists
report is linked to certificate chain
report hash is valid
```

## 5. User Experience

The portal should allow non-technical users to:

```text
paste receipt ID -> get trust result
download verification package
inspect certificate chain
verify assurance reports
```

## 6. Trust Interpretation Model

Portal responses should clearly distinguish:

```text
Verified
Not Verified
Insufficient Evidence
```

## 7. Security Model

```text
no mutation allowed
no write endpoints
no execution logic
deterministic outputs only
```

## 8. Boundary

The portal provides:

```text
transparency
verifiability
public access
```

The portal does not provide:

```text
control over systems
policy modification
runtime execution
legal certification
```

## Classification

```text
CUSTOMER-READY TRUST INTERFACE SPECIFICATION
```
