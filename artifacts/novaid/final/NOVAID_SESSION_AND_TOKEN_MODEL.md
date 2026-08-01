# NovaID session and token model

The normalized schema separates session, refresh family and refresh token records. Token hashes are unique; plaintext tokens are excluded. Rotation is modelled as ACTIVE → USED plus a linked replacement. Replay requires family and session revocation. The Phase 1 in-process implementation proves local behavior; durable and distributed rotation remains incomplete.
