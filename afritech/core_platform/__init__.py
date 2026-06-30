"""NovaTech core platform wiring.

This package exposes the core NovaTechSol layers without coupling them to any
product application surface.
"""

from afritech.core_platform.models import (
    AuthorityDecision,
    AuthorityRequest,
    CorePlatformFlowResult,
    Identity,
    PaymentIntent,
    PaymentReceipt,
    SettlementPlan,
    ProgrammingProposal,
    ScriptExplanation,
    TrustReceipt,
)
from afritech.core_platform.services import (
    NovaIDService,
    NovaPayService,
    NovaPowerEngine,
    NovaProgrammingService,
    NovaScriptService,
    NovaTechCorePlatform,
    NovaTrustService,
    SettlementLifecycleEvent,
    SettlementLifecycleHooks,
    SettlementLifecycleState,
    build_core_platform_overview,
)
from afritech.core_platform.settlement import (
    SettlementRouter,
    SettlementResult,
    build_settlement_status,
)
from afritech.core_platform.event_bus import build_event_bus_status
from afritech.core_platform.cbdc import cbdc_status
from afritech.core_platform.consensus import (
    ValidatorConsensusCertificate,
    ValidatorConsensusEngine,
    ValidatorConsensusEnvelope,
    ValidatorConsensusError,
    ValidatorConsensusConflictError,
    ValidatorConsensusVote,
    build_validator_consensus_status,
)
from afritech.core_platform.distributed_verification import (
    DistributedVerificationResult,
    build_trust_seal,
    build_validator_node_health,
    validate_distributed_consensus,
)
from afritech.core_platform.cross_chain_light_client import (
    LightClientState,
    build_cross_chain_bridge,
    build_merkle_proof,
    build_merkle_root,
    verify_cross_chain_bridge,
    verify_merkle_proof,
)
from afritech.core_platform.cryptographic_consensus import (
    CryptographicConsensusCertificate,
    CryptographicConsensusResult,
    CryptographicValidatorVote,
    ValidatorSlashingEngine,
    build_cryptographic_consensus_status,
    build_signed_message,
    detect_double_sign,
    run_cryptographic_consensus,
)
from afritech.core_platform.onchain_light_verifier import build_light_verifier_source
from afritech.core_platform.privacy_qr import (
    build_privacy_qr_artifact,
    build_privacy_qr_bundle,
    build_privacy_qr_payload,
    decode_privacy_qr_payload,
    encode_privacy_qr_payload,
)
from afritech.core_platform.trust_node import build_trust_node_network_status
from afritech.core_platform.persistence import (
    CorePlatformStore,
    InMemoryCorePlatformStore,
    PostgresCorePlatformStore,
)
from afritech.core_platform.payments import (
    PaymentProviderResult,
    PayIDProvider,
    StripeProvider,
)
from afritech.core_platform.stateless_verifier import verify_stateless_privacy_qr
from afritech.core_platform.stack import (
    NovaTechStack,
    StackLayer,
    StackSurface,
    build_novatech_stack,
    build_novatech_stack_readiness,
)
from afritech.core_platform.autonomous_ecosystem import (
    AutonomousEcosystem,
    DigitalTwin,
    GovernanceProtocol,
    ResourceMarket,
    ResourceTrade,
)
from afritech.core_platform.smart_resolver import (
    SmartResolver,
    SmartResolverResult,
    resolve_smart_offline_navigation,
)
from afritech.core_platform.transfers import (
    NovaPayTransferService,
    TransferQuote,
    TransferReceipt,
)
from afritech.core_platform.zk_receipts import (
    build_zk_receipt,
    build_zk_receipt_qr_bundle,
    verify_zk_receipt,
)

__all__ = [
    "AuthorityDecision",
    "AuthorityRequest",
    "CorePlatformFlowResult",
    "Identity",
    "NovaIDService",
    "NovaPayService",
    "NovaPayTransferService",
    "NovaPowerEngine",
    "NovaProgrammingService",
    "NovaScriptService",
    "NovaTechCorePlatform",
    "NovaTrustService",
    "SettlementLifecycleEvent",
    "SettlementLifecycleHooks",
    "SettlementLifecycleState",
    "PaymentIntent",
    "PaymentProviderResult",
    "PaymentReceipt",
    "PayIDProvider",
    "AutonomousEcosystem",
    "DigitalTwin",
    "GovernanceProtocol",
    "ResourceMarket",
    "ResourceTrade",
    "SmartResolver",
    "SmartResolverResult",
    "CorePlatformStore",
    "InMemoryCorePlatformStore",
    "PostgresCorePlatformStore",
    "SettlementPlan",
    "SettlementRouter",
    "SettlementResult",
    "NovaTechStack",
    "StackLayer",
    "StackSurface",
    "TransferQuote",
    "TransferReceipt",
    "ValidatorConsensusCertificate",
    "ValidatorConsensusEngine",
    "ValidatorConsensusEnvelope",
    "ValidatorConsensusError",
    "ValidatorConsensusConflictError",
    "ValidatorConsensusVote",
    "DistributedVerificationResult",
    "LightClientState",
    "CryptographicConsensusCertificate",
    "CryptographicConsensusResult",
    "CryptographicValidatorVote",
    "ValidatorSlashingEngine",
    "build_cross_chain_bridge",
    "build_merkle_proof",
    "build_merkle_root",
    "build_trust_seal",
    "build_cryptographic_consensus_status",
    "build_signed_message",
    "build_validator_node_health",
    "detect_double_sign",
    "run_cryptographic_consensus",
    "verify_cross_chain_bridge",
    "verify_merkle_proof",
    "validate_distributed_consensus",
    "build_settlement_status",
    "build_event_bus_status",
    "build_validator_consensus_status",
    "build_trust_node_network_status",
    "build_light_verifier_source",
    "cbdc_status",
    "ProgrammingProposal",
    "ScriptExplanation",
    "StripeProvider",
    "TrustReceipt",
    "build_privacy_qr_artifact",
    "build_privacy_qr_bundle",
    "build_privacy_qr_payload",
    "decode_privacy_qr_payload",
    "encode_privacy_qr_payload",
    "verify_stateless_privacy_qr",
    "build_novatech_stack",
    "build_novatech_stack_readiness",
    "resolve_smart_offline_navigation",
    "build_zk_receipt",
    "build_zk_receipt_qr_bundle",
    "verify_zk_receipt",
    "build_core_platform_overview",
]
