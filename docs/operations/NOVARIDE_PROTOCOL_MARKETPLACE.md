# NovaRide Protocol Marketplace

## Purpose

The NovaRide Protocol Marketplace is the governed catalog for the open protocol
ecosystem. It exposes first-party app listings, developer publishing surfaces,
SDK distribution, trust verification surfaces, and partner integrations.

It is read-only from the perspective of external consumers. Publishing and
listing approval remain policy-gated through NovaPower and verification gates
remain owned by NovaTrust.

## API Surface

- `GET /v1/novaride/developer/marketplace`
- `GET /v1/architecture/protocol-marketplace`

## Marketplace Layers

- NovaRide App Store
- NovaRide Developer Marketplace
- NovaRide Trust Marketplace
- NovaRide Partner Marketplace

## Governing Rules

- All listings SHALL be versioned.
- All listings SHALL pass sandbox, trust, and compatibility review before publication.
- All SDK distributions SHALL remain contract-generated and versioned.
- All marketplace publishing SHALL remain advisory until NovaPower approves execution.
- All trust and replay claims SHALL remain verifiable through NovaTrust.

## Publishing Pipeline

1. Submit listing metadata.
2. Validate in sandbox.
3. Review trust and security gates.
4. Verify protocol compatibility.
5. Publish to the governed catalog.
