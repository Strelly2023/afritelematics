# NovaTech EC2 First Test Run

Status: READY FOR FIRST REAL TEST RUN

Purpose: walk an operator through the first live EC2 test run using the
pilot HTTP deployment path.

## Preconditions

- EC2 host is reachable over SSH
- repository is present on the host
- Docker and Compose are installed
- `deploy/production/.env.production` has no placeholder values
- `AFRITECH_DOMAIN` is empty for pilot HTTP mode

## Test Run

1. Pull the latest code.

```bash
git pull
```

2. Start the pilot stack.

```bash
./scripts/deploy_production_zero_downtime.sh --base-url http://<host>
```

3. Confirm the API health gate passes.
4. Confirm the dashboard starts.
5. Confirm the edge starts on port 80.
6. Run the local production probe.

```bash
./scripts/run_local_production_probe.sh http://<host>
```

7. Run the pilot dataset validator.

```bash
python -m afritech.ci.afritech_pilot_dataset_simulation_validator
```

8. Run the field evidence validator.

```bash
python -m afritech.ci.afritech_field_evidence_runtime_validator
```

9. Run the reconciliation validator.

```bash
python -m afritech.ci.afritech_reconciliation_validator
```

10. Run the operator decision validator.

```bash
python -m afritech.ci.afritech_operator_decision_protocol_validator
```

11. Run the live pilot execution validator.

```bash
python -m afritech.ci.afritech_live_pilot_execution_validator
```

## Known-Good Outputs

These are the local outputs already observed against the current repository
state:

```text
NovaTech pilot dataset simulation validation PASSED
scenario_id=airport-zone-001 deployment_type=airport
operations=3 signals=21
dataset_hash=06a34178db405a1d713f7e70a84884e8b67bcfc850f3d818428f3dd0d1721321
```

```text
NovaTech field evidence runtime validation PASSED
signals=7 events=7 collection_hash=d64a42bfcd0d4d7a9911029934637c6d11bbda0d353fd9ffeb6c0f1dff70f6b0 proof_hash=526043c8884f6c0ad9ca25ff01ec2dc185087909c260aec414623886a96c5ca7 ingestion_hash=a888942959bc32ba927cff58fe371952023d1b633e7643935e4b93167dc82d0c validation_hash=089f5f8b8e3c3b79d9e5a3df82888f4b683893babd5fa308640299123096dcae
```

```text
NovaTech reconciliation validation PASSED
scenario_id=airport-zone-001 deployment_type=airport
operations=3 divergence_count=0
divergence_score=0.000000 recommendation=continue
```

```text
NovaTech operator decision protocol validation PASSED
adr=ADR-0044 rule=RULE-064 binding=BIND-042
```

```text
NovaTech live pilot execution validation PASSED
checklist=docs/operations/AFRITECH_LIVE_PILOT_EXECUTION_CHECKLIST.md
ec2_test_run=docs/operations/AFRITECH_EC2_FIRST_TEST_RUN.md
operator_scenario=docs/operations/AFRITECH_FIRST_OPERATOR_DECISION_SCENARIO.md
```

## Expected Result

- HTTP health returns 200
- pilot dataset simulation validates
- field evidence runtime validates
- reconciliation validates
- operator decision protocol validates
- live pilot execution validates

## Failure Result

If any gate fails, stop the pilot and record the failure as evidence.
