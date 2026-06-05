"""Domain execution contracts for AfriTPPS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.afritpps.execution_engine import (
    AfriTPPSOperationIntent,
    AfriTPPSExecutionOutcome,
    execute_operation,
)


class AfriTPPSContractError(ValueError):
    """Raised when a domain operation violates its execution contract."""


@dataclass(frozen=True)
class DomainOperationContract:
    operation: str
    required_fields: tuple[str, ...]
    expected_outcome: str


@dataclass(frozen=True)
class DomainExecutionContract:
    domain: str
    identity: str
    operations: tuple[DomainOperationContract, ...]
    execution_allowed: bool = True
    blocked_reason: str = ""

    def operation_contract(self, operation: str) -> DomainOperationContract:
        for contract in self.operations:
            if contract.operation == operation:
                return contract
        raise AfriTPPSContractError(f"{self.domain}.{operation} is not registered")


DOMAIN_CONTRACTS: dict[str, DomainExecutionContract] = {
    "AfriRide": DomainExecutionContract(
        domain="AfriRide",
        identity="Mobility Execution System",
        operations=(
            DomainOperationContract(
                operation="RideRequested",
                required_fields=("rider_id", "pickup", "dropoff"),
                expected_outcome="ride request recorded",
            ),
            DomainOperationContract(
                operation="DriverAssigned",
                required_fields=("ride_id", "driver_id"),
                expected_outcome="driver assignment recorded",
            ),
            DomainOperationContract(
                operation="TripStarted",
                required_fields=("ride_id", "driver_id"),
                expected_outcome="trip start recorded",
            ),
            DomainOperationContract(
                operation="TripCompleted",
                required_fields=("ride_id", "driver_id"),
                expected_outcome="trip completion recorded",
            ),
        ),
    ),
    "AfriConnect": DomainExecutionContract(
        domain="AfriConnect",
        identity="Supply Chain Execution System",
        operations=(
            DomainOperationContract(
                operation="ShipmentCreated",
                required_fields=("shipment_id", "origin", "destination"),
                expected_outcome="shipment creation recorded",
            ),
            DomainOperationContract(
                operation="ShipmentDispatched",
                required_fields=("shipment_id", "driver_id"),
                expected_outcome="shipment dispatch recorded",
            ),
            DomainOperationContract(
                operation="ShipmentDelivered",
                required_fields=("shipment_id", "delivery_location", "received_by"),
                expected_outcome="shipment delivery recorded",
            ),
            DomainOperationContract(
                operation="WarehouseStored",
                required_fields=("shipment_id", "warehouse_id"),
                expected_outcome="warehouse storage recorded",
            ),
        ),
    ),
    "AfriPay": DomainExecutionContract(
        domain="AfriPay",
        identity="Conceptual Financial Surface",
        execution_allowed=False,
        blocked_reason="AfriPay is DESIGNED_BLOCKED; raw transaction evidence only.",
        operations=(
            DomainOperationContract(
                operation="RawTransactionEvidence",
                required_fields=(
                    "transaction_id",
                    "payer",
                    "payee",
                    "amount",
                    "currency",
                    "method",
                    "outcome",
                ),
                expected_outcome="raw transaction evidence recorded",
            ),
        ),
    ),
    "AfriHealth": DomainExecutionContract(
        domain="AfriHealth",
        identity="Healthcare Execution System",
        operations=(
            DomainOperationContract(
                operation="ConsultationPerformed",
                required_fields=("patient_id", "provider_id"),
                expected_outcome="consultation recorded",
            ),
            DomainOperationContract(
                operation="DiagnosisRecorded",
                required_fields=("patient_id", "provider_id", "diagnosis"),
                expected_outcome="diagnosis recorded",
            ),
            DomainOperationContract(
                operation="PrescriptionIssued",
                required_fields=("patient_id", "doctor_id", "medication"),
                expected_outcome="prescription recorded",
            ),
            DomainOperationContract(
                operation="TreatmentCompleted",
                required_fields=("patient_id", "provider_id"),
                expected_outcome="treatment completion recorded",
            ),
            DomainOperationContract(
                operation="HealthCheckTriggered",
                required_fields=("driver_id", "reason"),
                expected_outcome="health check trigger recorded",
            ),
        ),
    ),
    "AfriLearning": DomainExecutionContract(
        domain="AfriLearning",
        identity="Education Execution System",
        operations=(
            DomainOperationContract(
                operation="CourseEnrolled",
                required_fields=("student_id", "course_id"),
                expected_outcome="course enrollment recorded",
            ),
            DomainOperationContract(
                operation="ModuleCompleted",
                required_fields=("student_id", "module_id"),
                expected_outcome="module completion recorded",
            ),
            DomainOperationContract(
                operation="AssessmentPassed",
                required_fields=("student_id", "assessment_id", "score"),
                expected_outcome="assessment pass recorded",
            ),
            DomainOperationContract(
                operation="CertificateIssued",
                required_fields=("student_id", "certificate_id"),
                expected_outcome="certificate issuance recorded",
            ),
        ),
    ),
    "AfriTalent": DomainExecutionContract(
        domain="AfriTalent",
        identity="Employment Execution System",
        operations=(
            DomainOperationContract(
                operation="JobPosted",
                required_fields=("job_id", "employer_id"),
                expected_outcome="job post recorded",
            ),
            DomainOperationContract(
                operation="CandidateMatched",
                required_fields=("job_id", "candidate_id"),
                expected_outcome="candidate match recorded",
            ),
            DomainOperationContract(
                operation="WorkCompleted",
                required_fields=("worker_id", "work_id"),
                expected_outcome="work completion recorded",
            ),
            DomainOperationContract(
                operation="PerformanceVerified",
                required_fields=("worker_id", "verifier_id"),
                expected_outcome="performance verification recorded",
            ),
        ),
    ),
    "AfriMarket": DomainExecutionContract(
        domain="AfriMarket",
        identity="Commerce Execution System",
        operations=(
            DomainOperationContract(
                operation="ProductListed",
                required_fields=("product_id", "seller_id"),
                expected_outcome="product listing recorded",
            ),
            DomainOperationContract(
                operation="OrderPlaced",
                required_fields=("order_id", "buyer_id"),
                expected_outcome="order placement recorded",
            ),
            DomainOperationContract(
                operation="OrderFulfilled",
                required_fields=("order_id", "seller_id"),
                expected_outcome="order fulfillment recorded",
            ),
            DomainOperationContract(
                operation="OrderDelivered",
                required_fields=("order_id", "recipient_id"),
                expected_outcome="order delivery recorded",
            ),
        ),
    ),
    "AfriHome": DomainExecutionContract(
        domain="AfriHome",
        identity="Housing Execution System",
        operations=(
            DomainOperationContract(
                operation="PropertyListed",
                required_fields=("property_id", "owner_id"),
                expected_outcome="property listing recorded",
            ),
            DomainOperationContract(
                operation="RentalAgreementCreated",
                required_fields=("agreement_id", "property_id", "tenant_id"),
                expected_outcome="rental agreement recorded",
            ),
            DomainOperationContract(
                operation="OccupancyStarted",
                required_fields=("agreement_id", "tenant_id"),
                expected_outcome="occupancy start recorded",
            ),
            DomainOperationContract(
                operation="OccupancyEnded",
                required_fields=("agreement_id", "tenant_id"),
                expected_outcome="occupancy end recorded",
            ),
        ),
    ),
    "AfriID": DomainExecutionContract(
        domain="AfriID",
        identity="Trust and Identity Layer",
        operations=(
            DomainOperationContract(
                operation="IdentityCreated",
                required_fields=("identity_id", "subject_id"),
                expected_outcome="identity creation recorded",
            ),
            DomainOperationContract(
                operation="CredentialIssued",
                required_fields=("credential_id", "subject_id", "issuer_id"),
                expected_outcome="credential issuance recorded",
            ),
            DomainOperationContract(
                operation="CredentialVerified",
                required_fields=("credential_id", "verifier_id"),
                expected_outcome="credential verification recorded",
            ),
        ),
    ),
    "AfriCloud": DomainExecutionContract(
        domain="AfriCloud",
        identity="Infrastructure Execution System",
        operations=(
            DomainOperationContract(
                operation="InstanceStarted",
                required_fields=("instance_id", "region"),
                expected_outcome="instance start recorded",
            ),
            DomainOperationContract(
                operation="ServiceDeployed",
                required_fields=("service_id", "version"),
                expected_outcome="service deployment recorded",
            ),
            DomainOperationContract(
                operation="SystemScaled",
                required_fields=("service_id", "scale_target"),
                expected_outcome="system scale recorded",
            ),
            DomainOperationContract(
                operation="FailureDetected",
                required_fields=("service_id", "failure_type"),
                expected_outcome="failure detection recorded",
            ),
        ),
    ),
}


def get_domain_contract(domain: str) -> DomainExecutionContract:
    try:
        return DOMAIN_CONTRACTS[domain]
    except KeyError as exc:
        raise AfriTPPSContractError(f"unknown AfriTPPS domain: {domain}") from exc


def execute_domain_operation(
    *,
    operation_id: str,
    domain: str,
    operation: str,
    actor_id: str,
    subject_id: str,
    payload: dict[str, Any],
    signature: dict[str, Any],
    witnesses: tuple[dict[str, Any], ...] = (),
    require_client_signature: bool = False,
) -> AfriTPPSExecutionOutcome:
    contract = get_domain_contract(domain)
    if not contract.execution_allowed:
        raise AfriTPPSContractError(contract.blocked_reason)

    operation_contract = contract.operation_contract(operation)
    _validate_required_fields(operation_contract, payload)
    return execute_operation(
        AfriTPPSOperationIntent(
            operation_id=operation_id,
            domain=domain,
            actor_id=actor_id,
            subject_id=subject_id,
            action=operation,
            expected_outcome=operation_contract.expected_outcome,
            payload=payload,
            signature=signature,
            witnesses=witnesses,
        ),
        require_client_signature=require_client_signature,
    )


def _validate_required_fields(
    operation_contract: DomainOperationContract,
    payload: dict[str, Any],
) -> None:
    missing = [
        field
        for field in operation_contract.required_fields
        if field not in payload or payload[field] in (None, "")
    ]
    if missing:
        raise AfriTPPSContractError(
            f"{operation_contract.operation} missing required fields: "
            + ", ".join(missing)
        )
