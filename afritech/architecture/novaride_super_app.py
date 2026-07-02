"""NovaRide Super App and NovaID contract surfaces."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


NOVARIDE_SUPER_APP_VERSION = "2026.07.0"
NOVAID_VERSION = "2026.07.0"
NOVAID_GEN_SOVEREIGN_VERSION = "2026.07.0"
NOVAID_DIGITAL_NATION_VERSION = "2026.07.0"
NOVARIDE_DIGITAL_CONSTITUTION_VERSION = "2026.07.0"
NOVARIDE_REGULATORY_ALIGNMENT_VERSION = "2026.07.0"
NOVARIDE_GLOBAL_EXPANSION_VERSION = "2026.07.0"

NOVAID_CAPABILITIES: tuple[dict[str, Any], ...] = (
    {
        "key": "identity",
        "name": "Universal identity",
        "capability": "Cross-app account identity with DID-ready identifiers.",
    },
    {
        "key": "authentication",
        "name": "Secure authentication",
        "capability": "Login with NovaID for NovaRide and partner applications.",
    },
    {
        "key": "reputation",
        "name": "Reputation",
        "capability": "Trust score, ride history, delivery activity, and verification state.",
    },
    {
        "key": "wallet_linkage",
        "name": "Wallet linkage",
        "capability": "NovaPay wallet binding for financial identity and settlements.",
    },
    {
        "key": "device_identity",
        "name": "Device identity",
        "capability": "Device binding, session risk checks, and replay-aware security.",
    },
    {
        "key": "governance",
        "name": "Governance rights",
        "capability": "DAO voting, proposal participation, and token-weighted access.",
    },
)

NOVARIDE_SUPER_APP_MODULES: tuple[dict[str, Any], ...] = (
    {
        "key": "mobility",
        "name": "Mobility",
        "route": "/super-app/mobility",
        "capabilities": ("book_ride", "schedule_ride", "driver_verification", "ride_receipts"),
        "authority": "NovaRide Core",
    },
    {
        "key": "delivery",
        "name": "Delivery",
        "route": "/super-app/delivery",
        "capabilities": ("parcel_delivery", "proof_tracking", "courier_identity", "delivery_receipts"),
        "authority": "NovaRide Core",
    },
    {
        "key": "wallet",
        "name": "Wallet / NovaPay",
        "route": "/super-app/wallet",
        "capabilities": ("multi_currency_wallet", "send_money", "merchant_payment", "token_balance"),
        "authority": "NovaPay",
    },
    {
        "key": "finance",
        "name": "Finance",
        "route": "/super-app/finance",
        "capabilities": ("loans", "treasury_access", "staking", "settlement_history"),
        "authority": "NovaPay",
    },
    {
        "key": "app_store",
        "name": "App Store",
        "route": "/super-app/app-store",
        "capabilities": ("install_app", "launch_partner_app", "developer_revenue", "permission_review"),
        "authority": "NovaPower",
    },
    {
        "key": "identity",
        "name": "Identity / NovaID",
        "route": "/super-app/identity",
        "capabilities": ("login_with_novaid", "privacy_controls", "wallet_linkage", "device_security"),
        "authority": "NovaID",
    },
    {
        "key": "ai_assistant",
        "name": "AI Assistant / NovaAI",
        "route": "/super-app/assistant",
        "capabilities": ("ride_recommendations", "spending_insights", "app_suggestions", "governance_prompts"),
        "authority": "advisory_only",
    },
)

NOVAID_GEN_SOVEREIGN_LAYERS: tuple[dict[str, Any], ...] = (
    {
        "key": "sovereign_identity",
        "name": "NovaID SSI",
        "role": "Self-sovereign identity, DID documents, and verifiable credentials.",
        "authority": "NovaID",
    },
    {
        "key": "crypto_finance",
        "name": "NovaToken / Crypto Layer",
        "role": "NVT, stablecoin support, CBDC adapters, and on-chain treasury plans.",
        "authority": "NovaPay_policy_gated",
    },
    {
        "key": "governance",
        "name": "NovaDAO",
        "role": "Token, reputation, and activity-weighted proposal governance.",
        "authority": "DAO_policy_gated",
    },
    {
        "key": "verification",
        "name": "NovaTrust",
        "role": "Credential, payment, replay, and on-chain audit verification.",
        "authority": "NovaTrust",
    },
    {
        "key": "decision_intelligence",
        "name": "NovaAI",
        "role": "Proposal analysis, manipulation detection, and outcome simulation.",
        "authority": "advisory_only",
    },
    {
        "key": "federation",
        "name": "Open Protocol Ecosystem",
        "role": "Federated identity, payments, trust, app, bank, and government integrations.",
        "authority": "federation_policy_gated",
    },
)

NOVAID_GEN_SOVEREIGN_FEDERATION_APIS: tuple[dict[str, str], ...] = (
    {
        "path": "/v1/federation/identity",
        "purpose": "Verify DID, credential, and identity assertions across trusted peers.",
    },
    {
        "path": "/v1/federation/payments",
        "purpose": "Route fiat, stablecoin, token, CBDC, and settlement proofs through NovaPay.",
    },
    {
        "path": "/v1/federation/trust",
        "purpose": "Exchange NovaTrust verification packets, receipts, and replay anchors.",
    },
)

NOVAID_DIGITAL_NATION_LAYERS: tuple[dict[str, str], ...] = (
    {
        "key": "digital_citizenship",
        "name": "NovaID Digital Citizenship",
        "role": "Platform citizenship, wallet linkage, reputation, activity, and governance eligibility.",
        "authority": "NovaID_policy_gated",
    },
    {
        "key": "novapassport",
        "name": "NovaPassport",
        "role": "Cross-platform access, service eligibility, trusted credential storage, and mobility access.",
        "authority": "NovaTrust_credential_gated",
    },
    {
        "key": "token_economy",
        "name": "NovaToken Economy",
        "role": "Rewards, contribution incentives, staking, treasury participation, and governance weight.",
        "authority": "NovaDAO_policy_gated",
    },
    {
        "key": "financial_system",
        "name": "NovaPay Financial System",
        "role": "Wallets, payments, settlement proofs, and economic identity.",
        "authority": "NovaPay_compliance_gated",
    },
    {
        "key": "global_protocol",
        "name": "Global Protocol Layer",
        "role": "Federation with apps, financial networks, and credential issuers.",
        "authority": "federation_policy_gated",
    },
)

NOVA_CITIZENSHIP_TIERS: tuple[dict[str, str], ...] = (
    {"tier": "Basic", "access": "Identity + wallet"},
    {"tier": "Verified", "access": "Full platform access"},
    {"tier": "Trusted", "access": "Governance power"},
    {"tier": "Elite", "access": "Ecosystem influence"},
)

NOVARIDE_CONSTITUTIONAL_ARTICLES: tuple[dict[str, Any], ...] = (
    {
        "article": "I",
        "title": "Sovereign Identity",
        "principle": "All participants possess a NovaID representing citizenship, access, economy, and governance.",
        "rules": (
            "identity_shall_be_self_sovereign",
            "identity_shall_be_cryptographically_verifiable",
            "identity_ownership_shall_remain_with_user",
            "credentials_shall_be_portable_and_interoperable",
        ),
    },
    {
        "article": "II",
        "title": "Digital Citizenship",
        "principle": "A NovaCitizen is any NovaID holder with verified participation in the ecosystem.",
        "rights": ("service_access", "governance_participation", "economic_participation", "data_ownership"),
        "responsibilities": (
            "maintain_identity_integrity",
            "respect_protocol_rules",
            "participate_in_fair_governance",
            "avoid_fraudulent_behavior",
        ),
    },
    {
        "article": "III",
        "title": "Rights of Users",
        "principle": "Every NovaCitizen receives identity, finance, governance, transparency, and record rights.",
        "guaranteed_rights": (
            "right_to_identity_ownership",
            "right_to_financial_participation",
            "right_to_governance_participation",
            "right_to_transparent_operations",
            "right_to_verifiable_records",
        ),
        "prohibited_actions": (
            "fraudulent_identity_creation",
            "unauthorized_financial_manipulation",
            "trust_layer_tampering",
            "governance_manipulation",
        ),
    },
)

NOVARIDE_REGULATORY_DOMAINS: tuple[dict[str, str], ...] = (
    {
        "domain": "Identity",
        "novaride_layer": "NovaID",
        "real_world_equivalent": "National ID / eID",
        "control": "KYC, AML, eKYC, DID, selective disclosure",
    },
    {
        "domain": "Finance",
        "novaride_layer": "NovaPay",
        "real_world_equivalent": "Banking / payments law",
        "control": "auditability, anti-fraud controls, monitoring, traceable settlement",
    },
    {
        "domain": "Token",
        "novaride_layer": "NovaToken",
        "real_world_equivalent": "Securities / digital assets",
        "control": "jurisdictional classification and transfer restrictions",
    },
    {
        "domain": "Governance",
        "novaride_layer": "DAO",
        "real_world_equivalent": "Corporate + cooperative governance",
        "control": "transparent voting, legal wrapper readiness, enforceable contract mapping",
    },
    {
        "domain": "Trust",
        "novaride_layer": "NovaTrust",
        "real_world_equivalent": "Audit / compliance systems",
        "control": "replay evidence, cryptographic proof, audit readiness",
    },
)

NOVARIDE_EXPANSION_PHASES: tuple[dict[str, Any], ...] = (
    {
        "phase": "0",
        "name": "Foundation",
        "status": "done",
        "markets": ("Global core platform",),
        "note": "NovaID, NovaPay, NovaTrust, and DAO.",
    },
    {
        "phase": "1",
        "name": "Regulatory ready markets",
        "status": "target",
        "markets": ("Australia", "UK", "Singapore", "UAE"),
        "note": "Clear fintech regulations and stable legal systems.",
    },
    {
        "phase": "2",
        "name": "High growth markets",
        "status": "target",
        "markets": ("Kenya", "Rwanda", "Nigeria", "India"),
        "note": "Mobile-first economies with strong mobility and payments demand.",
    },
    {
        "phase": "3",
        "name": "Complex regulations",
        "status": "target",
        "markets": ("EU", "USA"),
        "note": "Strict compliance and licensing requirements.",
    },
)


class NovaID:
    """Deterministic NovaID profile builder for contract surfaces."""

    def create_identity(self, user: Mapping[str, Any]) -> dict[str, Any]:
        user_id = str(user.get("id") or user.get("user_id") or "84729")
        wallet = str(user.get("wallet") or "novapay_wallet_demo")
        return {
            "id": f"NOVA-{user_id}",
            "did": f"did:nova:{user_id}",
            "wallet": wallet,
            "trust_score": int(user.get("trust_score", 92)),
            "reputation": list(user.get("reputation", ("verified_rider", "wallet_linked"))),
            "privacy": {
                "selective_disclosure": True,
                "onchain_proofs": "proof_hashes_only",
                "cross_app_sharing": "user_controlled",
            },
        }

    def authenticate(self, credentials: Mapping[str, Any]) -> dict[str, Any]:
        subject = str(credentials.get("subject") or credentials.get("user_id") or "anonymous")
        return {
            "status": "policy_gated",
            "subject": subject,
            "method": str(credentials.get("method", "login_with_novaid")),
            "requires": ("credential_verification", "device_binding", "replay_evidence"),
            "authority_boundary": "NovaID_authentication_is_backend_authoritative",
        }


def novaid_identity_contract() -> dict[str, Any]:
    """Return the governed NovaID global identity contract."""

    return {
        "platform": "NovaRide",
        "version": NOVAID_VERSION,
        "classification": "global_identity_layer_contract",
        "status": "standard_ready",
        "positioning": "Login with NovaID",
        "authority_boundary": "NovaID_owns_identity_authentication_reputation_device_and_governance_identity",
        "identity_model": {
            "identifier": "NOVA-{user_id}",
            "did_method": "did:nova",
            "wallet_linkage": "NovaPay",
            "trust_score": "NovaTrust",
            "governance_rights": "DAO",
            "device_identity": "replay_bound_device_claims",
        },
        "capabilities": deepcopy(list(NOVAID_CAPABILITIES)),
        "verification": {
            "cryptographic_verification": True,
            "onchain_proofs": True,
            "cross_app_identity": True,
            "privacy_control": True,
            "replay_auditing": True,
        },
        "sample_profile": NovaID().create_identity(
            {
                "id": "84729",
                "wallet": "novapay_wallet_84729",
                "trust_score": 92,
                "reputation": ("120_rides", "15_deliveries", "wallet_verified"),
            }
        ),
        "login_button": {
            "label": "Login with NovaID",
            "contract": "novaride.identity.login.v1",
            "policy_gates": ("credential_verification", "device_binding", "privacy_consent", "replay_receipt"),
        },
        "use_cases": (
            "login_across_apps",
            "driver_verification",
            "payments_identity",
            "governance_voting",
            "reputation_scoring",
        ),
        "metrics": {
            "identity_profiles": 2500000,
            "wallet_link_rate": "92%",
            "verified_devices": 1800000,
            "cross_app_sessions": 7200,
        },
    }


def novaride_super_app_contract() -> dict[str, Any]:
    """Return the NovaRide Super App shell contract."""

    return {
        "platform": "NovaRide",
        "version": NOVARIDE_SUPER_APP_VERSION,
        "classification": "global_super_app_operating_system_contract",
        "status": "contract_ready",
        "purpose": "Global digital operating system for mobility, finance, identity, apps, and governance.",
        "authority_boundary": "super_app_is_interface_only_backend_services_keep_authority",
        "shell": {
            "entry": "NovaRide Super App",
            "experience_flow": (
                "open_dashboard",
                "choose_service",
                "use_app",
                "pay_with_novapay",
                "earn_nvt",
                "build_novaid_reputation",
            ),
            "components": ("Header", "NovaIDProfile", "Wallet", "AppStore", "Services", "AIAssistant"),
        },
        "modules": deepcopy(list(NOVARIDE_SUPER_APP_MODULES)),
        "profile": {
            "novaid": "NOVA-84729",
            "wallet_balance_usd": 850,
            "token_balance": "2,400 NVT",
            "trust_score": "92%",
            "activity": {"rides": 120, "deliveries": 15},
        },
        "wallet": {
            "base_currency": "USD",
            "balances": {
                "USD": "500.00",
                "KES": "20000.00",
                "USDC": "200.00",
                "NVT": "1500.00",
            },
            "authority": "NovaPay",
        },
        "governance": {
            "can_vote": True,
            "active_proposals": 42,
            "staking": "NVT_supported",
            "authority": "DAO_policy_gated",
        },
        "ai_assistant": {
            "authority_boundary": "NovaAI_recommendations_are_advisory_only",
            "recommendations": (
                "Take a ride now: high demand nearby",
                "Earn extra today as driver",
                "Vote on proposal #42",
                "Review wallet reserve before cross-border transfer",
            ),
        },
        "ecosystem_loop": (
            "users",
            "super_app_activity",
            "payments_and_tokens",
            "treasury",
            "dao_governance",
            "platform_evolution",
            "developer_build",
            "ecosystem_growth",
        ),
        "metrics": {
            "users": "2.5M",
            "apps": 7200,
            "transactions_per_day": "$5M",
            "token_circulation": "growing",
        },
    }


def novaid_gen_sovereign_contract() -> dict[str, Any]:
    """Return the NovaID Gen-Sovereign infrastructure contract."""

    return {
        "platform": "NovaRide",
        "version": NOVAID_GEN_SOVEREIGN_VERSION,
        "classification": "novaid_gen_sovereign_infrastructure_contract",
        "status": "architecture_contract_ready",
        "positioning": "Sovereign digital identity and global crypto-financial infrastructure",
        "authority_boundary": (
            "gen_sovereign_is_architecture_and_policy_gated_infrastructure_not_live_state_authority"
        ),
        "core_layers": deepcopy(list(NOVAID_GEN_SOVEREIGN_LAYERS)),
        "identity": {
            "model": "self_sovereign_identity",
            "did_method": "did:nova",
            "credential_standard": "verifiable_credentials",
            "sample_did_document": {
                "id": "did:nova:847392",
                "publicKey": "0xABC...",
                "credentials": ("KYC_verified", "Driver_licensed"),
            },
            "auth_flow": (
                "user_signs_with_private_key",
                "network_verifies_signature",
                "policy_checks_credentials",
                "access_granted_with_replay_receipt",
            ),
            "privacy_controls": (
                "selective_disclosure",
                "user_controlled_sharing",
                "proof_hashes_only_onchain",
                "revocable_cross_platform_sessions",
            ),
        },
        "government_integration": {
            "status": "credential_adapter_contract",
            "model": (
                "government_issues_credential",
                "issuer_signature_verified",
                "linked_to_novaid",
                "usable_through_policy_gated_federation",
            ),
            "credential_types": (
                "national_id_verification",
                "driver_license",
                "tax_identity",
                "public_transport_access",
            ),
            "authority_boundary": "governments_remain_credential_issuers_novaid_verifies_and_binds_claims",
        },
        "crypto_finance": {
            "components": (
                "NovaToken_NVT",
                "stablecoins",
                "optional_CBDC_adapters",
                "onchain_treasury_contracts",
            ),
            "payment_stack": (
                "wallet",
                "crypto_or_fiat",
                "novapay",
                "settlement",
                "onchain_verification",
            ),
            "token_contract_reference": {
                "name": "NovaToken",
                "symbol": "NVT",
                "capabilities": ("transfer", "stake", "governance_weight", "reward_distribution"),
                "authority_boundary": "smart_contracts_require_audit_deployment_and_governance_approval",
            },
            "metrics": {
                "token_circulation": "50M NVT",
                "daily_transactions": "$20M",
                "treasury": "$10M",
            },
        },
        "federation": {
            "model": (
                "NovaRide_to_apps",
                "NovaRide_to_banks",
                "NovaRide_to_governments",
                "NovaRide_to_protocols",
            ),
            "apis": deepcopy(list(NOVAID_GEN_SOVEREIGN_FEDERATION_APIS)),
            "authority_boundary": "federation_admits_peers_by_policy_and_trust_roots_only",
        },
        "ai_governance": {
            "model": "tokens_reputation_activity_weighted",
            "formula": {
                "tokens": 0.5,
                "reputation": 0.3,
                "activity": 0.2,
            },
            "ai_roles": (
                "suggest_proposals",
                "predict_outcomes",
                "detect_manipulation",
                "optimize_decisions",
            ),
            "sample_analysis": {
                "proposal": "Expand to Kigali",
                "roi": "24%",
                "risk": "LOW",
                "recommendation": "APPROVE",
            },
            "authority_boundary": "NovaAI_recommends_only_DAO_and_policy_execute",
        },
        "security": {
            "hard_guarantees": (
                "user_controlled_private_keys",
                "cryptographic_authentication",
                "zero_trust_architecture",
                "replay_verification",
                "onchain_audit",
            ),
            "minimum_controls": (
                "key_rotation",
                "credential_revocation",
                "issuer_registry",
                "sanctions_and_compliance_policy_hooks",
                "independent_audit_before_live_financial_clearing",
            ),
        },
        "dashboard": {
            "identity": {
                "novaids": "10M+",
                "verified": "95%",
                "active": "growing",
            },
            "economy": {
                "token_circulation": "50M NVT",
                "daily_transactions": "$20M",
                "treasury": "$10M",
            },
            "governance": {
                "proposals": 120,
                "participation": "70%",
                "ai_assisted_decisions": True,
            },
        },
        "capabilities": (
            "sovereign_identity",
            "global_crypto_finance",
            "dao_governance",
            "ai_assisted_decisions",
            "cross_platform_federation",
            "token_economy",
            "open_protocol",
            "super_app",
        ),
    }


def novaid_digital_nation_contract() -> dict[str, Any]:
    """Return the NovaID Gen-Sovereign++ digital nation contract."""

    return {
        "platform": "NovaRide",
        "version": NOVAID_DIGITAL_NATION_VERSION,
        "classification": "novaid_gen_sovereign_plus_plus_digital_nation_contract",
        "status": "architecture_contract_ready",
        "positioning": "Digital Citizenship + NovaID Passport System",
        "authority_boundary": (
            "digital_nation_is_platform_citizenship_not_legal_nationality_or_immigration_authority"
        ),
        "what_this_is": (
            "platform_level_citizenship",
            "digital_identity_system",
            "economic_ecosystem",
            "governance_participation_layer",
        ),
        "what_this_is_not": (
            "government_issued_citizenship",
            "legal_passport",
            "immigration_authority",
            "state_sovereignty_claim",
        ),
        "core_layers": deepcopy(list(NOVAID_DIGITAL_NATION_LAYERS)),
        "citizenship": {
            "name": "NovaCitizens",
            "purpose": "Digital citizens with identity, wallet, reputation, activity, and governance rights.",
            "features": (
                "digital_identity",
                "wallet_linkage",
                "reputation",
                "activity_history",
                "governance_rights",
            ),
            "profile": {
                "nova_id": "did:nova:00087423",
                "citizenship_status": "verified",
                "wallet": "0xABC123",
                "trust_score": 94,
                "reputation": "high",
                "roles": ("rider", "developer"),
                "governance_power": 2450,
            },
            "tiers": deepcopy(list(NOVA_CITIZENSHIP_TIERS)),
        },
        "passport": {
            "name": "NovaPassport",
            "purpose": "Digital global access passport for NovaRide and federated platform services.",
            "authority_boundary": "novapassport_is_platform_access_not_a_legal_travel_document",
            "sample": {
                "passport_id": "NVP-992384",
                "holder": "did:nova:00087423",
                "credentials": ("KYC_verified", "licensed_driver", "trusted_user"),
                "validity": "global",
                "signature": "cryptographic_proof",
            },
            "capabilities": (
                "cross_platform_access",
                "cross_border_identity_verification",
                "service_eligibility",
                "trusted_credential_storage",
                "platform_level_mobility_rights",
            ),
            "use_cases": (
                "access_apps_globally",
                "verify_drivers_instantly",
                "enable_financial_services",
                "participate_in_governance",
            ),
        },
        "ssi": {
            "model": "self_sovereign_identity",
            "ownership": "user_controlled_keys",
            "storage": "offchain_onchain_hybrid",
            "credential_issuance": "authorities_sign_verifiable_credentials",
            "auth_flow": (
                "user_signs_challenge",
                "public_key_verifies_signature",
                "policy_checks_credentials",
                "access_granted_with_replay_receipt",
            ),
            "zero_central_control": (
                "no_single_authority_owns_identities",
                "issuers_verify_claims",
                "users_control_disclosure",
            ),
        },
        "economy": {
            "principle": "identity_equals_economic_power",
            "participation_loop": (
                "use_platform",
                "earn_tokens",
                "build_reputation",
                "vote",
                "influence_system",
                "earn_more",
            ),
            "dashboard": {
                "token_supply": "100M NVT",
                "daily_transactions": "$25M",
                "treasury": "$15M",
            },
        },
        "governance": {
            "model": "NovaDAO_governs_ecosystem_citizens_vote_with_NovaID",
            "formula": {
                "tokens": 0.5,
                "trust_score": 0.3,
                "activity": 0.2,
            },
            "proposal_types": (
                "economic_policy",
                "app_store_rules",
                "treasury_allocation",
                "platform_upgrades",
            ),
            "dashboard": {
                "active_voters": "2.5M",
                "participation": "72%",
                "ai_assisted_decisions": True,
            },
        },
        "ai_governance": {
            "roles": (
                "analyze_proposals",
                "predict_outcomes",
                "detect_manipulation",
                "recommend_decisions",
            ),
            "sample_analysis": {
                "proposal": "Increase driver incentives",
                "impact": "Positive",
                "cost": "Moderate",
                "recommendation": "APPROVE",
            },
            "authority_boundary": "NovaAI_recommends_only_citizens_and_DAO_execute",
        },
        "federation": {
            "model": (
                "NovaRide_to_external_platforms",
                "NovaRide_to_credential_issuers",
                "NovaRide_to_financial_networks",
            ),
            "architecture": (
                "cross_app_identity",
                "cross_platform_payments",
                "federated_credential_verification",
            ),
            "authority_boundary": "federation_requires_peer_policy_trust_roots_and_compliance_review",
        },
        "security": {
            "guarantees": (
                "cryptographic_identity",
                "private_key_ownership",
                "replay_logs",
                "onchain_proofs",
                "ai_anomaly_detection",
            ),
            "minimum_controls": (
                "credential_revocation",
                "key_recovery_policy",
                "issuer_registry",
                "passport_status_checks",
                "independent_security_review_before_live_federation",
            ),
        },
        "dashboard": {
            "identity": {
                "novacitizens": "12M",
                "verified": "95%",
                "trusted": "60%",
            },
            "economy": {
                "token_supply": "100M NVT",
                "daily_transactions": "$25M",
                "treasury": "$15M",
            },
            "governance": {
                "active_voters": "2.5M",
                "participation": "72%",
                "ai_assisted_decisions": True,
            },
        },
        "capabilities": (
            "digital_citizenship",
            "passport_system",
            "global_identity_layer",
            "token_economy",
            "dao_governance",
            "ai_assisted_decisions",
            "cross_platform_federation",
            "financial_infrastructure",
        ),
    }


def novaride_digital_constitution_contract() -> dict[str, Any]:
    """Return the NovaRide Digital Constitution governance contract."""

    return {
        "platform": "NovaRide",
        "version": NOVARIDE_DIGITAL_CONSTITUTION_VERSION,
        "classification": "novaride_digital_constitution_governance_contract",
        "status": "architecture_contract_ready",
        "positioning": "Digital Constitution + Legal Governance Framework",
        "authority_boundary": (
            "digital_constitution_is_platform_governance_not_statutory_law_or_regulator_substitute"
        ),
        "core_statement": (
            "NovaRide shall operate as a governed digital system in which identity is sovereign, "
            "authority is bounded, rules are enforceable, actions are auditable, and governance is participatory."
        ),
        "constitutional_principle": {
            "identity": "NovaID",
            "rules": "programmable_contracts",
            "governance": "NovaDAO",
            "authority": "NovaPower",
            "truth": "NovaTrust_replay_audit",
        },
        "articles": deepcopy(list(NOVARIDE_CONSTITUTIONAL_ARTICLES)),
        "authority_structure": {
            "fundamental_rule": "execution_authority_shall_remain_with_NovaPower_and_authorized_subsystems_only",
            "authorities": (
                {"authority": "NovaPower", "role": "Execution authority"},
                {"authority": "NovaRide Core", "role": "Operational truth"},
                {"authority": "NovaPay", "role": "Financial authority"},
                {"authority": "NovaTrust", "role": "Verification authority"},
                {"authority": "DAO", "role": "Governance authority"},
            ),
        },
        "governance": {
            "legislative_layer": "NovaDAO",
            "powers": (
                "change_protocol_rules",
                "define_economic_policies",
                "approve_treasury_allocations",
                "govern_ecosystem_evolution",
            ),
            "voting_model": ("token_holdings", "trust_score", "participation_level"),
            "ai_role": {
                "shall_provide": ("recommendations", "predictive_analysis", "fraud_detection"),
                "shall_not": ("directly_vote", "override_governance", "execute_authority"),
            },
        },
        "economic_constitution": {
            "principles": (
                "economy_shall_be_token_driven",
                "value_creation_shall_be_rewarded",
                "treasury_shall_be_governed_transparently",
                "financial_actions_shall_be_auditable",
            ),
            "treasury_rules": (
                "funds_shall_be_verifiable",
                "allocations_shall_require_governance_approval",
                "transactions_shall_be_replayable",
            ),
        },
        "trust_verification_law": {
            "truth_model": (
                "replay_shall_be_source_of_operational_truth",
                "novatrust_shall_validate_all_critical_actions",
                "cryptographic_proof_shall_be_required_for_verification",
            ),
            "legal_equivalent": "replay_is_digital_audit_record",
        },
        "contract_law": {
            "rule": "all_system_behavior_shall_be_governed_by_contracts",
            "types": ("api_contracts", "smart_contracts", "governance_rules", "identity_credentials"),
            "enforcement": (
                "contracts_shall_be_versioned",
                "contracts_shall_be_test_validated",
                "violations_shall_be_rejected_automatically",
            ),
        },
        "ai_governance_law": {
            "required_behavior": (
                "explain_decisions",
                "provide_confidence_scores",
                "identify_data_sources",
                "record_audit_logs",
            ),
            "restrictions": (
                "execute_payments",
                "modify_trust_evidence",
                "override_authority_systems",
                "make_irreversible_decisions",
            ),
        },
        "federation_law": {
            "purpose": "Define contract-gated interaction with external systems.",
            "rules": (
                "external_systems_shall_integrate_via_contracts",
                "identity_shall_remain_novaid_based",
                "trust_verification_shall_be_required",
                "cross_platform_operations_shall_be_auditable",
            ),
        },
        "dispute_resolution": {
            "mechanisms": (
                "automated_validation",
                "ai_analysis",
                "dao_arbitration",
            ),
            "example_flow": (
                "transaction_dispute",
                "replay_verification",
                "ai_review",
                "dao_vote",
                "decision_enforced",
            ),
        },
        "security_constitution": {
            "principles": (
                "zero_trust_architecture_shall_be_enforced",
                "all_actions_shall_be_authenticated",
                "all_sensitive_actions_shall_be_logged",
                "all_operations_shall_be_cryptographically_verifiable",
            ),
        },
        "compliance_enforcement": {
            "rule": "violations_are_architecture_defects_and_system_violations",
            "layers": (
                "validator_engine",
                "ci_compliance_system",
                "governance_ai",
                "dao_enforcement",
            ),
        },
        "amendment_process": (
            "proposal_submitted",
            "ai_impact_analysis",
            "public_review",
            "dao_vote",
            "enactment_via_contract_update",
        ),
        "guarantees": {
            "identity_sovereignty": True,
            "governance_participation": True,
            "financial_transparency": True,
            "security_enforcement": True,
            "contract_integrity": True,
            "ai_safety": True,
            "trust_verification": True,
        },
    }


def novaride_regulatory_alignment_contract() -> dict[str, Any]:
    """Return the NovaRide real-world regulatory alignment contract."""

    return {
        "platform": "NovaRide",
        "version": NOVARIDE_REGULATORY_ALIGNMENT_VERSION,
        "classification": "novaride_regulatory_alignment_contract",
        "status": "architecture_contract_ready",
        "positioning": "Regulatory-Aligned Digital Infrastructure Layer",
        "authority_boundary": (
            "regulatory_alignment_is_control_mapping_not_legal_advice_certification_or_regulatory_approval"
        ),
        "core_principle": (
            "NovaRide shall operate within applicable legal frameworks while preserving "
            "its constitutional invariants and autonomy."
        ),
        "alignment_model": deepcopy(list(NOVARIDE_REGULATORY_DOMAINS)),
        "identity_compliance": {
            "aligns_with": ("KYC", "AML", "eKYC", "W3C_DID", "government_document_verification"),
            "requirements": (
                "verified_identity_credentials",
                "government_issued_document_integration",
                "selective_disclosure_for_privacy_laws",
                "high_risk_actions_require_identity_verification",
            ),
            "rule": "identity_verification_required_for_high_risk_financial_or_governance_actions",
        },
        "payments_regulation": {
            "aligns_with": (
                "payment_services_regulations",
                "banking_compliance",
                "anti_fraud_controls",
                "transaction_monitoring",
            ),
            "requirements": (
                "transactions_shall_be_auditable",
                "suspicious_activity_shall_be_flagged",
                "cross_border_payments_shall_be_compliant",
                "settlement_systems_shall_be_traceable",
            ),
            "treasury_rule": "treasury_operations_shall_comply_with_financial_risk_and_audit_standards",
        },
        "token_regulation": {
            "aligns_with": ("digital_asset_laws", "stablecoin_regulations", "securities_classification"),
            "classification_model": (
                {"type": "utility_token", "treatment": "platform_usage"},
                {"type": "governance_token", "treatment": "DAO_participation"},
                {"type": "payment_token", "treatment": "financial_rules_apply"},
            ),
            "rule": "novatoken_shall_comply_with_applicable_digital_asset_regulations_per_jurisdiction",
        },
        "privacy_law": {
            "aligns_with": ("GDPR", "Privacy_Act_AU", "global_data_protection_standards"),
            "principles": (
                "data_shall_be_user_controlled",
                "consent_shall_be_explicit",
                "sensitive_data_shall_be_protected",
                "data_portability_shall_be_supported",
            ),
            "implementation": (
                "zero_knowledge_proofs_where_needed",
                "offchain_sensitive_storage",
                "permission_based_data_sharing",
            ),
        },
        "governance_legalization": {
            "recognition_model": "digital_cooperative_or_governance_body",
            "rules": (
                "dao_decisions_shall_map_to_enforceable_contracts",
                "governance_shall_be_transparent",
                "voting_shall_be_auditable",
            ),
            "optional_structures": ("registered_DAO_entity", "foundation", "association"),
        },
        "cross_border_framework": {
            "rule": "novaride_shall_implement_jurisdiction_aware_compliance_layers",
            "flow": ("user_location", "region_detected", "applicable_rules_enforced", "system_adapts"),
            "regions": (
                {"region": "EU", "active_rule": "GDPR enforced"},
                {"region": "US", "active_rule": "financial reporting"},
                {"region": "Africa", "active_rule": "mobile money integration"},
            ),
        },
        "identity_recognition_path": {
            "target": "recognized_digital_identity_layer",
            "steps": (
                "partner_with_governments",
                "integrate_existing_id_systems",
                "provide_verification_apis",
                "meet_interoperability_standards",
            ),
            "federation": ("NovaID_to_government_ID", "NovaID_to_banks", "NovaID_to_platforms"),
        },
        "liability_model": {
            "rule": "liability_attributed_by_layer_of_control_and_authority",
            "responsibilities": (
                {"component": "NovaRide Protocol", "responsibility": "Infrastructure"},
                {"component": "App developers", "responsibility": "Application behavior"},
                {"component": "Users", "responsibility": "Actions"},
                {"component": "DAO", "responsibility": "Governance decisions"},
            ),
        },
        "ai_regulation_compliance": {
            "aligns_with": ("AI_safety_regulations", "algorithm_transparency", "explainability_requirements"),
            "rules": (
                "ai_decisions_shall_be_explainable",
                "ai_shall_not_execute_high_risk_actions_autonomously",
                "human_or_governance_review_shall_exist",
            ),
        },
        "compliance_engine": {
            "model": "jurisdiction_aware_policy_enforcement",
            "flow": (
                "load_regulations_for_region",
                "evaluate_action_against_rules",
                "block_non_compliant_action",
                "approve_compliant_action_with_replay_evidence",
            ),
            "existing_capabilities": ("architecture_validator", "governance_ai", "digital_twin"),
        },
        "dashboard": {
            "regulatory_status": {
                "identity": "mapped",
                "finance": "mapped",
                "crypto": "mapped",
                "privacy": "mapped",
            },
            "jurisdictions": {
                "EU": "GDPR active",
                "US": "financial rules active",
                "Africa": "mobile money integration",
            },
            "risk_monitor": {
                "fraud_risk": "LOW",
                "compliance_risk": "LOW",
                "audit_readiness": "HIGH",
            },
        },
        "properties": {
            "legal_compliance": "control_mapped",
            "identity_recognition": "integration_ready",
            "financial_regulation_alignment": "policy_gated",
            "cross_border_operation": "jurisdiction_aware",
            "governance_legality": "legal_wrapper_ready",
            "ai_safety_compliance": "human_or_governance_review_required",
        },
    }


def novaride_global_expansion_contract() -> dict[str, Any]:
    """Return the NovaRide global regulatory expansion strategy contract."""

    return {
        "platform": "NovaRide",
        "version": NOVARIDE_GLOBAL_EXPANSION_VERSION,
        "classification": "novaride_global_regulatory_expansion_strategy_contract",
        "status": "strategy_contract_ready",
        "positioning": "Global Regulatory Expansion Strategy",
        "authority_boundary": (
            "expansion_strategy_is_rollout_planning_not_country_launch_authorization_or_legal_approval"
        ),
        "objective": "globally_compliant_identity_mobility_fintech_protocol",
        "core_principle": "Global standard architecture plus local regulatory adaptation equals scalable deployment.",
        "expansion_model": (
            "Global Core Platform",
            "Regional Compliance Layer",
            "Country-Specific Adaptation",
            "Local Market Deployment",
        ),
        "phases": deepcopy(list(NOVARIDE_EXPANSION_PHASES)),
        "country_entry_playbook": {
            "regulatory_mapping": (
                "identify_financial_regulators",
                "identify_identity_requirements",
                "identify_transport_rules",
                "identify_data_protection_laws",
            ),
            "legal_structure": (
                "local_entity",
                "compliance_officer",
                "partner_contracts",
            ),
            "partnership_model": (
                "integrate_with_local_banks",
                "integrate_with_psps_and_mobile_money",
                "integrate_with_gov_id_or_kyc_providers",
                "integrate_with_fleet_operators",
            ),
            "integration_strategy": "replace_nothing_integrate_with_existing_systems",
        },
        "novaid_deployment": {
            "basic_id": ("email_and_phone", "platform_access"),
            "verified_id": ("KYC", "document_verification"),
            "trusted_id": ("government_credential_integration",),
            "government_integration_path": (
                "start_with_KYC_providers",
                "integrate_gov_APIs",
                "become_trusted_identity_layer",
            ),
        },
        "novapay_deployment": {
            "partner_based": ("Stripe", "Adyen", "mobile_money", "banks"),
            "licensed_later": (
                "payment_institution_license",
                "e_money_license",
                "crypto_compliance",
            ),
            "multi_currency_rollout": ("fiat_only", "stablecoins", "full_on_chain_treasury"),
        },
        "token_strategy": {
            "rule": "token_must_not_be_treated_as_a_security_without_jurisdiction_review",
            "launch_model": (
                {"region": "strict_regulation", "strategy": "utility_only"},
                {"region": "flexible_regulation", "strategy": "full_token_model"},
                {"region": "DeFi_friendly", "strategy": "on_chain_economy"},
            ),
        },
        "dao_structure": {
            "model": ("on_chain_DAO", "legal_wrapper_foundation_or_association", "local_operations_entity"),
            "why_it_matters": (
                "legal_enforceability",
                "liability_protection",
                "regulatory_clarity",
            ),
        },
        "cross_border_architecture": {
            "compliance_engine": (
                "detect_user_location",
                "load_rules_for_region",
                "enforce_rules",
            ),
            "region_examples": (
                {"region": "EU", "feature": "GDPR mode"},
                {"region": "US", "feature": "reporting mode"},
                {"region": "Africa", "feature": "mobile money"},
            ),
        },
        "ai_alignment": {
            "requirements": (
                "explainability",
                "transparency",
                "audit_logs",
                "no_autonomous_financial_execution",
            ),
            "implementation": "all_ai_decisions_logged_auditable_explainable",
        },
        "go_to_market": {
            "entry_model": (
                "launch_pilot_city",
                "partner_with_local_operators",
                "acquire_early_users",
                "expand_region",
            ),
            "growth_strategy": (
                "incentives_token_plus_fiat",
                "driver_onboarding",
                "developer_ecosystem",
                "app_store_expansion",
            ),
        },
        "risk_management": {
            "top_risks": (
                {"risk": "Regulatory rejection", "mitigation": "Partner model"},
                {"risk": "Financial compliance", "mitigation": "Licensed partners"},
                {"risk": "Data privacy", "mitigation": "Regional storage"},
                {"risk": "Token scrutiny", "mitigation": "Staged rollout"},
            ),
        },
        "dashboard": {
            "expansion_status": {
                "Australia": "Live",
                "Kenya": "Live",
                "India": "Pilot",
                "EU": "Preparation",
            },
            "compliance_status": {
                "identity": "OK",
                "finance": "OK",
                "privacy": "OK",
                "token": "Restricted",
            },
            "financial": {
                "transactions_per_day": "$1.5M",
                "revenue": "Growing",
                "cost": "Controlled",
            },
        },
        "execution_blueprint": {
            "hub_model": (
                {"hub": "Melbourne", "role": "regulatory_base_and_funding_hq"},
                {"hub": "Burundi", "role": "controlled_low_cost_pilot"},
                {"hub": "DRC", "role": "scale_opportunity_market"},
                {"hub": "East Africa", "role": "expansion_corridor_kenya_rwanda_uganda"},
            ),
            "phase_sequence": (
                {"phase": "1", "market": "Melbourne", "objective": "compliance_and_pilot"},
                {"phase": "2", "market": "Burundi", "objective": "controlled_launch"},
                {"phase": "3", "market": "DRC", "objective": "scaled_deployment"},
                {"phase": "4", "market": "East Africa", "objective": "regional_expansion"},
            ),
            "melbourne_pilot": {
                "legal_setup": ("Pty Ltd", "global_hq"),
                "compliance_checklist": (
                    "KYC_provider",
                    "Privacy_Act",
                    "payment_partner",
                    "licensed_drivers_or_fleets",
                ),
                "target": ("airport_transfers", "courier_logistics"),
                "pilot_flow": (
                    "launch_small_fleet",
                    "onboard_10_to_20_drivers",
                    "invite_200_to_500_users",
                    "test_ride_payment_loop",
                    "collect_data",
                    "iterate",
                ),
                "success_metrics": (
                    "1000_plus_rides_per_month",
                    "payment_reliability_above_99_percent",
                    "user_retention_above_30_percent",
                ),
            },
            "burundi_launch": {
                "structure": ("local_partner_or_entity", "ops_manager"),
                "compliance": ("basic_KYC", "mobile_money", "partner_first"),
                "services": ("ride_hailing", "delivery", "mobile_money_payments"),
                "pilot_size": ("10_to_30_drivers", "200_to_1000_users"),
            },
            "drc_launch": {
                "structure": ("partner_led", "local_operator_execution"),
                "compliance": ("progressive_KYC", "mobile_money_first", "partnership_adaptation"),
                "priorities": ("motorbike_taxis", "delivery_and_logistics", "business_transport"),
                "scale_plan": (
                    "pilot_city",
                    "city_expansion",
                    "regional_hubs",
                    "national_coverage",
                ),
            },
            "east_africa_expansion": {
                "markets": ("Kenya", "Rwanda", "Uganda"),
                "kenya": ("M_Pesa_integration", "fintech_plus_delivery_plus_rides"),
                "rwanda": ("government_friendly", "NovaID_plus_governance_pilots"),
            },
            "legal_entity_template": {
                "step_1": "register_local_company_or_partner",
                "step_2": ("identity_KYC", "payment_partner", "privacy_laws", "local_licensing"),
                "step_3": ("driver_agreements", "partner_agreements", "API_SDK_terms"),
            },
            "novaid_rollout": (
                "phone_based_login",
                "verified_KYC",
                "trust_and_reputation",
                "passport_level_system",
            ),
            "novapay_rollout": (
                "payment_partners",
                "internal_wallet",
                "multi_currency",
                "token_layer_later",
            ),
            "team_structure": {
                "founder": "Australia",
                "tech_team": "remote",
                "ops_manager": "each_country",
                "compliance_advisor": "per_region",
            },
            "ninety_day_plan": (
                "register_AU_entity",
                "build_production_ready_app",
                "secure_payment_partner",
                "launch_Melbourne_pilot",
                "begin_Burundi_setup",
                "launch_Burundi_pilot",
                "prepare_DRC_entry",
            ),
        },
    }
