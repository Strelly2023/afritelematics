# Password change flow

Implemented locally: validate active PASSWORD_OTP session, verify current password, enforce policy/history, supersede the active credential, create a new scrypt credential, increment security version, and revoke sessions/families atomically. Shared publication and complete event catalog remain partial.
