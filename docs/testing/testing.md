# Testing

## Protocol Test Suites

- Sovereign ledger protocol tests
- System integration hardening tests
- Adversarial attack simulation tests
- Activation, scale, and service tests

## Key Scenarios

- async execution stress
- network instability
- partial node failure
- tampered hash
- wrong-result minority
- metadata tampering
- replay duplicate
- quorum failure
- 20-node adversarial network

## Run

```bash
python3 -m pytest afritech/tests/distributed/test_sovereign_ledger_protocol.py
python3 -m pytest afritech/tests/distributed/test_protocol_hardening_and_adversarial.py
python3 -m pytest afritech/tests/distributed/test_activation_scale_and_services.py
```
