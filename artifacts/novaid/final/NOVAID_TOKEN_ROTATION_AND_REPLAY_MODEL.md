# Token rotation and replay

Only domain-separated hashes persist. Rotation conditionally changes ACTIVE to USED and creates one linked successor in the transaction. Reuse changes the token to REPLAYED, revokes family and session, persists evidence, commits, then denies. Access tokens are not implemented in this Phase 3 slice.
