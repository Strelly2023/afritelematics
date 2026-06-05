# Developer Getting Started

## Install

Use the repository Python environment.

## Run Focused Validation

```bash
python3 -m pytest afritech/tests/distributed/test_sovereign_ledger_protocol.py
python3 -m pytest afritech/tests/distributed/test_protocol_hardening_and_adversarial.py
python3 -m pytest afritech/tests/distributed/test_activation_scale_and_services.py
```

## CLI

```bash
python3 -m afritech.cli.main run-pilot-check
python3 -m afritech.cli.main simulate-network
python3 -m afritech.cli.main inspect-chain
```

## Core Principle

Do not write authoritative state directly. Commit proof-backed blocks and derive state from the ledger.
