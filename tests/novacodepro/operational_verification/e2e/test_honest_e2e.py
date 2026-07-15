from afritech.novacodepro.operational_verification.service import OperationalVerificationService


def test_e2e_keeps_ga_and_payments_disabled_after_repository_automation() -> None:
    service = OperationalVerificationService()
    program = service.create_program({"release_id": "rel-e2e"})
    run = service.execute_program(program["id"])
    service.collect_development_evidence("accessibility", "portal routes", "rel-e2e", run["id"])
    prr = service.generate_prr_package("rel-e2e")
    executive = service.request_executive_approval({"release_id": "rel-e2e", "prr_id": prr["prr_id"]}, "usr-requester")
    ga = service.evaluate_ga()
    payments = service.evaluate_payments()

    assert executive["status"] == "APPROVAL_PENDING"
    assert prr["recommendation"] == "READY_FOR_PRR_APPROVAL"
    assert ga["ga_allowed"] is False
    assert payments["real_payments_enabled"] is False
