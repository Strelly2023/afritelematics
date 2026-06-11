# AfriTech

## Sovereign Distributed Execution Ledger Protocol

![Python](https://img.shields.io/badge/python-3.11-blue)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Security](https://img.shields.io/badge/security-zero--trust-blue)
![Consensus](https://img.shields.io/badge/consensus-byzantine--resilient-purple)
![License](https://img.shields.io/badge/license-Private-red)

AfriTech is a Sovereign Distributed Execution Ledger Protocol (SDELP).

It combines deterministic execution, signed proofs, Byzantine-resilient consensus, trust scoring, ledger-backed state, replay verification, and an observable service layer.

## Core Principle

```text
Execution = Proof = Consensus = Ledger = State
```

## System Pipeline

```text
Client
  |
Network (TLS + handshake)
  |
P2P Gossip
  |
Execution Kernel
  |
Proof Generation
  |
Consensus Engine
  |
Audit Ledger (Blocks)
  |
State Machine
  |
Service Layer
```

## Architecture

| Layer | Description |
| --- | --- |
| Network | Secure communication with WebSocket/WSS, signed handshakes, nonce replay protection, and DHT discovery |
| Execution | Deterministic runtime and admission-controlled execution |
| Consensus | Proof validation, aggregation, quorum, and finalization |
| Trust | Reputation scoring, slashing, and peer isolation |
| Ledger | Immutable execution history using hash-linked blocks |
| State | Deterministic ledger projection using contract reducers |
| Services | Read-only application facade over derived state |
| Observability | Metrics, tracing, chain export, and dashboard helpers |

## Features

- Zero-trust networking with Ed25519 identity and TLS/WSS support
- Deterministic execution kernel
- Proof-based computation
- Byzantine-resilient consensus
- Trust scoring and slashing
- Immutable execution ledger
- Replay-verifiable state machine
- Read-only service layer
- Observability stack
- 20-node adversarial simulation coverage

## Testing

Validated surfaces include:

- 2-node execution
- 5-node consensus
- 20-node adversarial simulation
- Hardening and instability simulations
- Logistics, finance, and supply-chain protocol scenarios
- AfriRide ledger-backed ride coordination scenario

Run the focused protocol suite:

```bash
python3 -m pytest \
  afritech/tests/distributed/test_docs_and_tools_suite.py \
  afritech/tests/distributed/test_activation_scale_and_services.py \
  afritech/tests/distributed/test_protocol_hardening_and_adversarial.py \
  afritech/tests/distributed/test_sovereign_ledger_protocol.py
```

## AfriRide Pilot

AfriTech powers a controlled AfriRide distributed coordination scenario:

- ride matching
- pricing
- trip completion
- receipt generation
- consensus-confirmed execution blocks
- ledger-derived ride and receipt state

Live pilot activation remains gated. Repository-side readiness does not authorize real riders or production field execution.

## Security Guarantees

- Ed25519 identity
- Signed execution proofs
- Replay protection with nonce and timestamp validation
- TLS/WSS-capable transport
- Quorum-enforced consensus
- Trust penalties for invalid and mismatching behavior

## CLI Usage

```bash
python3 -m afritech.cli.main start-node
python3 -m afritech.cli.main simulate-5-node
python3 -m afritech.cli.main simulate-20-node
python3 -m afritech.cli.main inspect-chain
python3 -m afritech.cli.main run-pilot-check
```

If installed as a console script:

```bash
afritech simulate-20-node --json
```

## Public Verifier

External proof validation is available as a standalone public verifier:

```bash
python3 -m afritech.verify ./proof-bundle.json --format text
./scripts/run_public_verifier.sh ./proof-bundle.json --format json
```

Bundle and protocol references:

- `docs/protocol/AFRITECH_EXECUTION_PROTOCOL.md`
- `afritech/verify/public_verifier_bundle.schema.json`

## Observability

- Metrics collection
- Execution tracing
- Chain export
- Proof export
- State inspection
- Dashboard summary helpers

## Getting Started

```bash
pip install -r requirements.txt
python3 -m afritech.cli.main run-pilot-check --json
python3 -m afritech.cli.main simulate-20-node --json
```

## Pilot Activation

Pilot activation is intentionally gated:

```text
authorized = false
```

Activation may only be considered after backend, device, operator, replay, emergency, and evidence gates pass.

## Documentation

Start with:

- [System Overview](docs/architecture/system_overview.md)
- [Protocol Definition](docs/protocol/protocol_definition.md)
- [Ledger Model](docs/ledger/ledger.md)
- [State Machine](docs/state/state_machine.md)
- [Pilot Activation Checklist](docs/pilot/AFRIRIDE_PILOT_ACTIVATION_CHECKLIST.md)

## Final Position

AfriTech is a sovereign execution protocol capable of running real-world distributed systems, with live deployment controlled by explicit operational gates.
