# External Verifier SDK Rollout

## Objective

Make external partners depend on AfriTech verification without moving authority
away from trace and replay.

## SDK surfaces

- `PartnerVerificationClient`
- `TrustNetworkClient`
- `PartnerRegistryClient`
- `PublicVerifierClient`

## Rollout stages

1. sandbox package handoff
2. staging partner integration
3. registry publication test
4. public verification handoff
5. live controlled onboarding

## Required tutorial flow

- generate a verification request
- publish a trust registry entry
- fetch the public verification packet
- compare SDK-local decode with public endpoint output
- confirm that public verification does not create authority
