# Redis failure policy

Database state is authoritative. Redis revocation gives an immediate rejection fast path; cache misses require durable validation. Refresh and high-risk operations must fail closed when durable revocation state cannot be established. The complete outage/recovery/message-ordering test matrix remains incomplete.
