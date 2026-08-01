# Recovery code model

Codes are cryptographically random and returned once. Only tenant/identity-bound HMACs are stored. ACTIVE codes atomically become USED; regeneration supersedes active batches; revocation preserves used history. Generation requires an active phishing-resistant session with fresh step-up.
