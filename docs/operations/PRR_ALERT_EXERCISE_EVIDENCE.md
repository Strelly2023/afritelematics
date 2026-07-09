# PRR Alert Exercise Evidence

This document records the alert checks exercised for PRR evidence collection.

## Tested Alerts

- ApiDown
- NginxDown
- DatabaseDown
- ContainerUnhealthy
- CertificateExpirySoon
- CpuHigh
- MemoryHigh
- DiskHigh
- ApiErrorRateHigh
- HighLatency

## Evidence Fields

Each alert record captures:

- alert_name
- severity
- simulated_or_live
- expected_result
- observed_result
- pass_fail
- timestamp

## Notes

- Alert rules are defined in `deploy/production/monitoring/prometheus/alerts.yml`.
- Alert routing is defined in `deploy/production/monitoring/alertmanager/alertmanager.yml`.
- The PRR evidence package preserves `ga_allowed: false`.
