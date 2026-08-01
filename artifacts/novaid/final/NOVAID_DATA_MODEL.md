# NovaID data model

Tenant owns identities and memberships. Identities own credentials, sessions, attempts and risk state. Sessions own refresh families; families own immutable token records linked by parent and replacement identifiers. Identity state transitions and security events are append-only evidence. Secrets are represented only by hashes or external references.
