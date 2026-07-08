# Internal QA Failure and Regression Matrix

## Failure Modes
- Missing APK artifact
- Checksum mismatch
- Missing icon resource
- Missing tab or button
- Missing API contract surface
- Live payment path enabled
- Production credentials detected
- Protected endpoint missing bearer validation
- Receipt missing simulated-payment flag

## Regression Baselines
- Private development suite remains green
- NovaRide app tests remain green
- NovaPay app tests remain green
- NovaID app tests remain green
- Simulated-vs-real payment boundary tests remain green
- Scenario catalog tests remain green
- Enterprise scenario registry tests remain green

## Exit Criteria
Internal QA can advance only when every failure mode above is either absent or explicitly mitigated with a verified guardrail and the regression baselines remain green.
