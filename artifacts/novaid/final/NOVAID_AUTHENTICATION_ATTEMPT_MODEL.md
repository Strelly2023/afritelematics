# Authentication-attempt model

Temporary lockout persists only a tenant-bound HMAC identifier reference, failure count, observation start, lock expiry and update time. The broader detailed attempt-event table exists but is not yet populated for every factor and network/device dimension.
