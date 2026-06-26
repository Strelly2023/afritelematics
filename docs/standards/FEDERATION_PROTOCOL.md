# NovaFederation Protocol

NovaFederation provides node discovery, trust-root exchange, protocol
negotiation, signed evidence propagation, remote verification, remote replay
requests, revocation distribution, and federation policy.

Peers are untrusted by default. Admission requires node identity, trust roots,
supported version vector, tenant/domain scope, data-use purpose, rate limits,
revocation endpoint, and signed federation agreement. Messages require unique
IDs, canonical payload hashes, sender signatures, audience, expiry, replay
protection, and correlation IDs.

Federation never grants local payment, settlement, policy override, licensing,
or mutation authority. Remote replay returns verification evidence; the local
domain decides whether that evidence satisfies local policy. Partitions,
revocations, incompatible versions, and compromised keys fail closed while
preserving local sovereign operation.
