# Shared revocation model

Database state is authoritative. `ProcessLocalRevocationStore` supports deterministic tests. `RedisRevocationStore` supplies tenant-bound expiring keys and publication as a fast path. No Redis service or multi-instance propagation test was executed.
