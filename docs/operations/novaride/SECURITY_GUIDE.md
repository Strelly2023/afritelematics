# NovaRide Security Guide

Requirements implemented in the production-operated layer:

- production refuses memory persistence
- signed mobile synchronization
- nonce replay prevention
- device binding
- tenant and region context propagation
- no credentials in Kubernetes manifests
- network policy and least-privilege service accounts
- evidence integrity hashes
- readiness certificate status guards

Do not log passwords, tokens, full payment details, identity documents, or private key material.
