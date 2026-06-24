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
    build_core_platform_overview,
)
from afritech.core_platform.settlement import (
    SettlementRouter,
    SettlementResult,
    build_settlement_status,
)
from afritech.core_platform.event_bus import build_event_bus_status
from afritech.core_platform.cbdc import cbdc_status
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

__all__ = [
    "AuthorityDecision",
    "AuthorityRequest",
    "CorePlatformFlowResult",
    "Identity",
    "NovaIDService",
    "NovaPayService",
    "NovaPowerEngine",
    "NovaProgrammingService",
    "NovaScriptService",
    "NovaTechCorePlatform",
    "NovaTrustService",
    "PaymentIntent",
    "PaymentProviderResult",
    "PaymentReceipt",
    "PayIDProvider",
    "CorePlatformStore",
    "InMemoryCorePlatformStore",
    "PostgresCorePlatformStore",
    "SettlementPlan",
    "SettlementRouter",
    "SettlementResult",
    "build_settlement_status",
    "build_event_bus_status",
    "build_trust_node_network_status",
    "cbdc_status",
    "ProgrammingProposal",
    "ScriptExplanation",
    "StripeProvider",
    "TrustReceipt",
    "build_core_platform_overview",
]
