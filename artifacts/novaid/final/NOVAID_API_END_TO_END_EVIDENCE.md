# NovaID API end-to-end evidence

FastAPI `TestClient` executed register → verify → password authenticate → MFA challenge resend/supersession → OTP MFA → access/refresh issuance → `/me` → session list → logout → old-access-token rejection. The actual host application's OpenAPI schema also contains the authoritative routes. Result: PASS locally. This is not a live-server or browser certificate.
