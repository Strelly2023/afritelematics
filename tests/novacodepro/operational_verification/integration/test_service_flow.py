from afritech.novacodepro.operational_verification.service import OperationalVerificationService


def test_create_execute_collect_and_generate_prr_flow() -> None:
    service = OperationalVerificationService()
    program = service.create_program({"release_id": "rel-1", "environment": "ci"})
    run = service.execute_program(program["id"])
    evidence = service.collect_development_evidence("observability", "synthetic trace", "rel-1", run["id"])
    prr = service.generate_prr_package("rel-1", "ci")

    assert program["status"] == "CONFIGURED"
    assert run["status"] == "EXECUTED"
    assert evidence["metadata"]["production_evidence"] is False
    assert prr["ga_allowed"] is False
    assert prr["real_payments_enabled"] is False
