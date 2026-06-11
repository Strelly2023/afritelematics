# AfriTech External Verifier CLI Package

Status: EXTERNAL USER PACKAGE GUIDE

Purpose: package the verifier as a tool external users can install and run
without internal repository context.

## Commands

- `afritech-verify`
- `afritech-verify-session`

## Installation Paths

1. `pip install .`
2. `pipx install .`
3. distribute a built wheel to partners

## Core Usage

```bash
afritech-verify \
  --base-url https://trust.example.com \
  --expect-network sepolia \
  --write-report verifier-report.json
```

## First Session Usage

```bash
afritech-verify-session \
  --base-url https://trust.example.com \
  --partner "First Partner" \
  --expect-network sepolia \
  --report-out partner-session.json
```

## Distribution Rules

- external users consume public endpoints only
- operator credentials are not required
- reports can be archived as evidence bundles
- Mainnet promotion should happen only after Sepolia session success
