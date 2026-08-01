# WebAuthn step-up model

An authenticated session moves from ACTIVE to STEP_UP_REQUIRED. Its challenge is bound to the session and identity. A valid active credential assertion restores ACTIVE with `PHISHING_RESISTANT` strength and a five-minute freshness window. Failed assertions do not upgrade it.
