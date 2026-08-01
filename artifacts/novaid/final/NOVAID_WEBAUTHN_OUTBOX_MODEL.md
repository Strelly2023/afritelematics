# WebAuthn outbox model

Migrations define tenant, event type, resource, monotonically positive event version, secret-rejecting payload, delivery state, availability, attempts, optimistic version, and consumer checkpoints. Recovery completion also writes through the existing transactional security outbox.
