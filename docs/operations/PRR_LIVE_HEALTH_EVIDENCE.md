# PRR Live Health Evidence

This document captures the live health surfaces required for PRR evidence.

## Public Endpoints

- `https://api.afritechnology.com/health`
- `https://api.afritechnology.com/live`
- `https://api.afritechnology.com/ready`
- `https://identity.afritechnology.com/healthz`
- `https://trust.afritechnology.com/healthz`
- `https://merchant.afritechnology.com/healthz`
- `https://developer.afritechnology.com/healthz`

## Evidence Record

Each entry records:

- status code
- response body
- timestamp
- pass/fail

## Notes

The source repository contains the health endpoint implementation, NGINX healthz probe, and Docker health checks. External reachability should be confirmed in the deployment environment that has DNS and runtime access to the live stack.
