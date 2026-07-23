# AfriTech Full Architecture Graph

Status: GENERATED FULL ARCHITECTURE GRAPH

Classification: REPO-BACKED ARCHITECTURE INVENTORY AND RUNTIME GRAPH

Purpose: render a current-state architecture graph from the repository,
the FastAPI startup closure, and the runtime boundary validator output.

Generated: `deterministic-repo-snapshot`

## Runtime Summary

- Startup module: `afritech.api.app`
- Startup-safe closure size: `790`
- Django-bound modules declared in repo: `255`
- Runtime-boundary violations: `0`
- Direct startup imports from `afritech.api.app`: `107`

## Runtime Architecture Graph

```mermaid
flowchart LR
    Client["Clients / Operators / Partners"] --> Edge["Caddy / HTTP Edge\ndeploy/production"]
    Dashboard["React Dashboard\ndashboard/src"] --> Edge
    Edge --> App["FastAPI Runtime\nafritech/api/app.py"]

    subgraph FastAPI["Startup-Safe FastAPI Surface (790 modules)"]
        App --> Api["API Routers\nauth, trace, system, public verify"]
        App --> Workspace["AfriPro Workspace API"]
        App --> Governance["Ops Governance API"]
        App --> Trust["Partner / Trust Network APIs"]
    end

    subgraph Pipeline["Deterministic Execution Pipeline"]
        App --> Adapt["Edge Adapter"]
        Adapt --> Normalize["Normalization"]
        Normalize --> Queue["Partitioned Queue"]
        Queue --> Worker["Worker Pool"]
    end

    subgraph State["Stateful Domain Surfaces (255 Django-bound modules declared)"]
        Worker --> Domain["AfriRide Backend\nafriride_system/backend"]
        Domain --> Django["Django State Layer\nafriride_system/django_app"]
    end

    subgraph Proof["Proof / Replay / Verification"]
        Worker --> Trace["Trace / Replay / Evidence / Receipt"]
        Trace --> Public["Public Verification"]
        Trace --> Registry["Partner Registry / Trust Network"]
    end

    subgraph GovernancePlane["Governance & Enforcement"]
        Contract["Boundary Contract\nAFRITECH_FASTAPI_DJANGO_BOUNDARY_CONTRACT"] --> Validator["Runtime Boundary Validator"]
        Checklist["Safe Import Checklist"] --> Validator
        Validator --> Review["Generated Scan Report"]
    end

    App -. startup imports .-> Imports["Direct startup imports from app.py (107)"]
```

## Repository Architecture Inventory

```mermaid
flowchart TD
    Root["AfriTech Repository"] --> Core["afritech/"]
    Root --> Ride["afriride_system/"]
    Root --> Ui["dashboard/"]
    Root --> Deploy["deploy/production/"]

    Core --> Api["api (116 files)"]
    Core --> Edge["edge (11 files)"]
    Core --> Execution["execution (16 files)"]
    Core --> Security["security (18 files)"]
    Core --> Monitoring["monitoring (2 files)"]
    Core --> Proof["proof (25 files)"]
    Core --> Replay["replay (11 files)"]
    Core --> Governance["governance (18 files)"]
    Core --> Semantic["semantic_engine (26 files)"]
    Core --> Runtime["runtime (79 files)"]

    Ride --> Backend["backend (30 files)"]
    Ride --> Django["django_app (99 files)"]
    Ui --> Dashboard["src (6 files)"]
    Deploy --> Production["production (15 files)"]
```

## Repo Area Counts

- `api`: `116` files
- `edge`: `11` files
- `execution`: `16` files
- `security`: `18` files
- `monitoring`: `2` files
- `proof`: `25` files
- `replay`: `11` files
- `governance`: `18` files
- `semantic_engine`: `26` files
- `runtime`: `79` files
- `afriride_backend`: `30` files
- `afriride_django`: `99` files
- `dashboard_ui`: `6` files
- `deploy_production`: `15` files

## Startup Inventory

### Api (125)

- `afritech.api.afriprogramming_control_api`
- `afritech.api.afriride_mobile_release_api`
- `afritech.api.afriride_next_gen_mobile_api`
- `afritech.api.afriride_operational_api`
- `afritech.api.afroprog_workspace_api`
- `afritech.api.ai_auto_generator_api`
- `afritech.api.api_catalog_api`
- `afritech.api.api_platform_admin_api`
- `afritech.api.app`
- `afritech.api.architecture_proof_api`
- `afritech.api.auth`
- `afritech.api.auth.jwt_device_auth`
- `afritech.api.auth.legacy_auth`
- `afritech.api.auth.novacodepro_session_store`
- `afritech.api.contracts`
- `afritech.api.contracts.rules`
- `afritech.api.contracts.schema_registry_api`
- `afritech.api.contracts.schema_registry_middleware`
- `afritech.api.contracts.validator`
- `afritech.api.core_platform_api`
- `afritech.api.dashboard_gateway_api`
- `afritech.api.data_governance_api`
- `afritech.api.delivery_platform_api`
- `afritech.api.documentation_compliance_api`
- `afritech.api.executable_runtime_api`
- `afritech.api.feature_registry_api`
- `afritech.api.ingestion`
- `afritech.api.ingestion.event_ingestion`
- `afritech.api.integration_platform_api`
- `afritech.api.mobile_intelligence_api`
- `afritech.api.novacodepro_ncp003_api`
- `afritech.api.novacodepro_ncp004_api`
- `afritech.api.novacodepro_ncp005_api`
- `afritech.api.novacodepro_ncp006a_api`
- `afritech.api.novacodepro_ncp006b_api`
- `afritech.api.novacodepro_ncp007_api`
- `afritech.api.novacodepro_ncp008_api`
- `afritech.api.novacodepro_operational_verification_api`
- `afritech.api.novacodepro_platform_api`
- `afritech.api.novacodepro_product_factory_api`
- `afritech.api.novacodepro_workflow_fabric_api`
- `afritech.api.novacodepro_workspace_api`
- `afritech.api.novaid_api`
- `afritech.api.novaid_audit_replay_api`
- `afritech.api.novapay_ecosystem_api`
- `afritech.api.novapay_runtime_api`
- `afritech.api.novaportal_suite_api`
- `afritech.api.novaride_operations_api`
- `afritech.api.novaride_runtime_api`
- `afritech.api.novascript_api`
- `afritech.api.novatech_intranet_api`
- `afritech.api.ops_governance_api`
- `afritech.api.partner_certification_api`
- `afritech.api.partner_governance_api`
- `afritech.api.partner_registry_api`
- `afritech.api.partner_verification_api`
- `afritech.api.phase0_api`
- `afritech.api.phase10_api`
- `afritech.api.phase11_api`
- `afritech.api.phase12_api`
- `afritech.api.phase13_api`
- `afritech.api.phase1_api`
- `afritech.api.phase2_api`
- `afritech.api.phase3_api`
- `afritech.api.phase4_api`
- `afritech.api.phase5_api`
- `afritech.api.phase6_api`
- `afritech.api.phase7_api`
- `afritech.api.phase8_api`
- `afritech.api.phase9_api`
- `afritech.api.platform_runtime_api`
- `afritech.api.public_gateway_api`
- `afritech.api.public_verification_api`
- `afritech.api.realtime`
- `afritech.api.realtime.dashboard_bus`
- `afritech.api.realtime.ride_bus`
- `afritech.api.realtime.ws_server`
- `afritech.api.runtime_activation_api`
- `afritech.api.runtime_infrastructure_api`
- `afritech.api.runtime_operations_api`
- `afritech.api.runtime_verification_api`
- `afritech.api.runtime_worker_api`
- `afritech.api.solution_engineering_api`
- `afritech.api.system_status`
- `afritech.api.trace_api`
- `afritech.api.trust_network_api`
- `afritech.api_catalog`
- `afritech.api_catalog.approval`
- `afritech.api_catalog.authority`
- `afritech.api_catalog.compatibility`
- `afritech.api_catalog.domains`
- `afritech.api_catalog.enforcement`
- `afritech.api_catalog.lifecycle`
- `afritech.api_catalog.metrics`
- `afritech.api_catalog.provenance`
- `afritech.api_catalog.publication`
- `afritech.api_catalog.registry`
- `afritech.api_catalog.runtime_validation`
- `afritech.api_catalog.scorecard`
- `afritech.api_catalog.sdk`
- `afritech.api_catalog.signing`
- `afritech.api_platform`
- `afritech.api_platform.audit`
- `afritech.api_platform.authentication`
- `afritech.api_platform.authorization`
- `afritech.api_platform.compatibility`
- `afritech.api_platform.contracts`
- `afritech.api_platform.deprecation`
- `afritech.api_platform.endpoint_registry`
- `afritech.api_platform.errors`
- `afritech.api_platform.evidence`
- `afritech.api_platform.execution_pipeline`
- `afritech.api_platform.health`
- `afritech.api_platform.idempotency`
- `afritech.api_platform.openapi_registry`
- `afritech.api_platform.policy`
- `afritech.api_platform.rate_limiting`
- `afritech.api_platform.request_context`
- `afritech.api_platform.router_factory`
- `afritech.api_platform.telemetry`
- `afritech.api_platform.tenancy`
- `afritech.api_platform.validation`
- `afritech.api_platform.versioning`
- `afritech.api_platform.webhook_runtime`
- `afritech.api_platform.websocket_runtime`

### Edge (11)

- `afritech.edge`
- `afritech.edge.adapter`
- `afritech.edge.adapter.runtime_adapter`
- `afritech.edge.adapter.validation`
- `afritech.edge.ingestion`
- `afritech.edge.ingestion.queue_ingestor`
- `afritech.edge.ingestion.reality_ingestor`
- `afritech.edge.normalization`
- `afritech.edge.normalization.normalizer`
- `afritech.edge.normalization.reality_events`
- `afritech.edge.normalization.validation`

### Execution (7)

- `afritech.execution.partition`
- `afritech.execution.partition.router`
- `afritech.execution.queue`
- `afritech.execution.queue.partitioned_queue`
- `afritech.execution.worker`
- `afritech.execution.worker.types`
- `afritech.execution.worker.worker_pool`

### Monitoring (2)

- `afritech.monitoring.alerts`
- `afritech.monitoring.realtime_anomaly_alerting`

### Other (625)

- `afritech`
- `afritech.afripay`
- `afritech.afripay.api`
- `afritech.afripay.audit_sandbox`
- `afritech.afripay.billing`
- `afritech.afripay.certification_fraud`
- `afritech.afripay.compliance`
- `afritech.afripay.config`
- `afritech.afripay.dao_economy`
- `afritech.afripay.events`
- `afritech.afripay.exceptions`
- `afritech.afripay.external_packages`
- `afritech.afripay.fx`
- `afritech.afripay.global_treasury_ai`
- `afritech.afripay.guards`
- `afritech.afripay.intelligence`
- `afritech.afripay.ledger`
- `afritech.afripay.models`
- `afritech.afripay.money`
- `afritech.afripay.observability`
- `afritech.afripay.orchestration`
- `afritech.afripay.proofs`
- `afritech.afripay.protocol`
- `afritech.afripay.providers`
- `afritech.afripay.public_validation`
- `afritech.afripay.reconciliation`
- `afritech.afripay.routing`
- `afritech.afripay.treasury`
- `afritech.afripay.treasury_ai`
- `afritech.afriprogramming`
- `afritech.afriprogramming.assurance`
- `afritech.afriprogramming.assurance.assurance_engine`
- `afritech.afriprogramming.assurance.cert_signer`
- `afritech.afriprogramming.assurance.certification`
- `afritech.afriprogramming.assurance.continuous_engine`
- `afritech.afriprogramming.assurance.crypto_hardening`
- `afritech.afriprogramming.assurance.distributed_network`
- `afritech.afriprogramming.assurance.event_streaming`
- `afritech.afriprogramming.assurance.pki`
- `afritech.afriprogramming.assurance.policy_registry`
- `afritech.afriprogramming.assurance.replay_registry`
- `afritech.afriprogramming.assurance.reports`
- `afritech.afriprogramming.assurance.retention`
- `afritech.afriprogramming.assurance.risk_engine`
- `afritech.afriprogramming.assurance.risk_prediction`
- `afritech.afriprogramming.assurance.signed_audit`
- `afritech.afriprogramming.assurance.trust_engine`
- `afritech.afriprogramming.assurance.trust_exchange`
- `afritech.afriprogramming.assurance.trust_fabric`
- `afritech.afriprogramming.assurance.trust_trends`
- `afritech.afriprogramming.assurance.workflows`
- `afritech.afriprogramming.assurance.zero_trust`
- `afritech.afriprogramming.constants`
- `afritech.afriprogramming.control_plane`
- `afritech.afriprogramming.integration`
- `afritech.afriprogramming.models`
- `afritech.afriprogramming.persistence`
- `afritech.afriprogramming.phase1`
- `afritech.afriprogramming.phase10`
- `afritech.afriprogramming.phase11`
- `afritech.afriprogramming.phase12`
- `afritech.afriprogramming.phase13`
- `afritech.afriprogramming.phase2`
- `afritech.afriprogramming.phase3`
- `afritech.afriprogramming.phase4`
- `afritech.afriprogramming.phase5`
- `afritech.afriprogramming.phase6`
- `afritech.afriprogramming.phase7`
- `afritech.afriprogramming.phase8`
- `afritech.afriprogramming.phase9`
- `afritech.afriprogramming.phase_common`
- `afritech.afriprogramming.proposals`
- `afritech.afriprogramming.rbac`
- `afritech.afriprogramming.roles`
- `afritech.afriprogramming.schemas`
- `afritech.afriprogramming.services`
- `afritech.afriprogramming.tooling_manifest`
- `afritech.afriprogramming.tooling_surfaces`
- `afritech.afriprogramming.v9`
- `afritech.afriprogramming.v9.crypto_governance`
- `afritech.afriprogramming.v9.scheduler`
- `afritech.afriprogramming.v9.schema`
- `afritech.afriprogramming.v9.tracing`
- `afritech.afriprogramming.v9.trust_consensus`
- `afritech.afriride_mobile_release`
- `afritech.afroprog_workspace`
- `afritech.afroprog_workspace.models`
- `afritech.afroprog_workspace.service`
- `afritech.afroprog_workspace.workspace`
- `afritech.architecture.afritech_dashboard`
- `afritech.architecture.afritech_dashboard.services`
- `afritech.architecture.afritech_dashboard.views`
- `afritech.architecture.anchor_indexer`
- `afritech.architecture.blockchain_anchor`
- `afritech.architecture.config_loader`
- `afritech.architecture.domain_fabric`
- `afritech.architecture.full_architecture_graph`
- `afritech.architecture.integrity_proof`
- `afritech.architecture.novaride_app_store`
- `afritech.architecture.novaride_architecture`
- `afritech.architecture.novaride_next_generation`
- `afritech.architecture.novaride_protocol_marketplace`
- `afritech.architecture.novaride_super_app`
- `afritech.audit.merkle`
- `afritech.chain`
- `afritech.chain.anchor_publisher`
- `afritech.chain.contracts`
- `afritech.chain.contracts.architecture_anchor_abi`
- `afritech.chain.contracts.architecture_anchor_v2_abi`
- `afritech.chain.contracts.contract_client`
- `afritech.chain.contracts.deployment_config`
- `afritech.chain.sepolia_client`
- `afritech.chain.types`
- `afritech.ci`
- `afritech.ci.runtime_boundary_validator`
- `afritech.compliance.continuous_assurance`
- `afritech.contracts.guards_interface`
- `afritech.core`
- `afritech.core.engine`
- `afritech.core.matching_engine`
- `afritech.core.runtime`
- `afritech.core.runtime.receipts`
- `afritech.core.runtime.system_enforcement.execution_guard`
- `afritech.core.runtime.worker`
- `afritech.core.runtime.worker.worker`
- `afritech.core_platform`
- `afritech.core_platform.adaptive_sla`
- `afritech.core_platform.anchoring`
- `afritech.core_platform.audit_export`
- `afritech.core_platform.auditor_dashboard`
- `afritech.core_platform.autonomous_control`
- `afritech.core_platform.autonomous_ecosystem`
- `afritech.core_platform.canonical`
- `afritech.core_platform.cbdc`
- `afritech.core_platform.compliance_report`
- `afritech.core_platform.consensus`
- `afritech.core_platform.cross_chain_light_client`
- `afritech.core_platform.cryptographic_consensus`
- `afritech.core_platform.distributed_verification`
- `afritech.core_platform.event_bus`
- `afritech.core_platform.export_bundle`
- `afritech.core_platform.geo_routing`
- `afritech.core_platform.hash_domains`
- `afritech.core_platform.live_transaction`
- `afritech.core_platform.migration_system`
- `afritech.core_platform.mobile_verifier`
- `afritech.core_platform.models`
- `afritech.core_platform.novapay_runtime`
- `afritech.core_platform.onchain_light_verifier`
- `afritech.core_platform.orm`
- `afritech.core_platform.payments`
- `afritech.core_platform.payments.contracts`
- `afritech.core_platform.payments.mobile_money`
- `afritech.core_platform.payments.providers`
- `afritech.core_platform.persistence`
- `afritech.core_platform.privacy_qr`
- `afritech.core_platform.proof_receipts`
- `afritech.core_platform.qr`
- `afritech.core_platform.qr_proof`
- `afritech.core_platform.services`
- `afritech.core_platform.settlement`
- `afritech.core_platform.signing`
- `afritech.core_platform.smart_contract_verification`
- `afritech.core_platform.smart_resolver`
- `afritech.core_platform.stack`
- `afritech.core_platform.stateless_verifier`
- `afritech.core_platform.threshold_bls`
- `afritech.core_platform.transfers`
- `afritech.core_platform.trust_node`
- `afritech.core_platform.zk_receipts`
- `afritech.crypto.anchor_publication`
- `afritech.crypto.external_anchor`
- `afritech.crypto.merkle`
- `afritech.crypto.multi_party_verification`
- `afritech.crypto.public_chain_anchor`
- `afritech.crypto.signature`
- `afritech.data_governance`
- `afritech.data_governance.contracts`
- `afritech.data_governance.enterprise`
- `afritech.data_governance.guards`
- `afritech.data_governance.lifecycle`
- `afritech.data_governance.metadata_repository`
- `afritech.data_governance.ownership`
- `afritech.data_governance.registry`
- `afritech.delivery_platform`
- `afritech.delivery_platform.build_orchestrator`
- `afritech.delivery_platform.contracts`
- `afritech.delivery_platform.deployment_planner`
- `afritech.delivery_platform.errors`
- `afritech.delivery_platform.optimisation`
- `afritech.delivery_platform.orchestrator`
- `afritech.delivery_platform.registry`
- `afritech.delivery_platform.verification`
- `afritech.dispatch`
- `afritech.dispatch.matching`
- `afritech.dispatch.presence`
- `afritech.dispatch.service`
- `afritech.distributed.consensus`
- `afritech.distributed.consensus.quorum`
- `afritech.distributed.node`
- `afritech.distributed.trust`
- `afritech.distributed.trust.reputation_store`
- `afritech.distributed.trust.scoring`
- `afritech.distributed.trust.slashing`
- `afritech.distributed.trust.trust_engine`
- `afritech.docs`
- `afritech.docs.document_system`
- `afritech.ecosystem_evolution`
- `afritech.epoch`
- `afritech.epoch.compiled.semantic_epoch`
- `afritech.epoch.epoch_snapshot`
- `afritech.extensions.afriprog`
- `afritech.extensions.afriprog.ai_engine`
- `afritech.extensions.afriprog.ai_engine.coder`
- `afritech.extensions.afriprog.ai_engine.design_generator`
- `afritech.extensions.afriprog.ai_engine.design_output_validator`
- `afritech.extensions.afriprog.ai_engine.objective_engine`
- `afritech.extensions.afriprog.ai_engine.planner`
- `afritech.extensions.afriprog.ai_engine.reviewer`
- `afritech.extensions.afriprog.ai_engine.task_generator`
- `afritech.extensions.afriprog.ai_engine.test_writer`
- `afritech.extensions.afriprog.code_executor`
- `afritech.extensions.afriprog.code_executor.ast_editor`
- `afritech.extensions.afriprog.code_executor.diff_model`
- `afritech.extensions.afriprog.code_executor.executor_preview`
- `afritech.extensions.afriprog.code_executor.patch_generator`
- `afritech.extensions.afriprog.code_executor.patch_model`
- `afritech.extensions.afriprog.code_executor.sandbox`
- `afritech.extensions.afriprog.command_center`
- `afritech.extensions.afriprog.command_center.execution_engine`
- `afritech.extensions.afriprog.command_center.task_dispatcher`
- `afritech.extensions.afriprog.command_center.worktree_manager`
- `afritech.extensions.afriprog.constitutional_guard.authority_guard`
- `afritech.extensions.afriprog.constitutional_guard.claim_guard`
- `afritech.extensions.afriprog.constitutional_guard.guard_orchestrator`
- `afritech.extensions.afriprog.constitutional_guard.replay_guard`
- `afritech.extensions.afriprog.constitutional_guard.surface_guard`
- `afritech.extensions.afriprog.contracts`
- `afritech.extensions.afriprog.contracts.engineering_receipt`
- `afritech.extensions.afriprog.contracts.engineering_task`
- `afritech.extensions.afriprog.contracts.evidence_record`
- `afritech.extensions.afriprog.copilot_assist`
- `afritech.extensions.afriprog.copilot_assist.context_collector`
- `afritech.extensions.afriprog.copilot_assist.explanation_builder`
- `afritech.extensions.afriprog.copilot_assist.proposal_intelligence`
- `afritech.extensions.afriprog.copilot_assist.safety_classifier`
- `afritech.extensions.afriprog.copilot_assist.suggestion_engine`
- `afritech.extensions.afriprog.copilot_assist.suggestion_model`
- `afritech.extensions.afriprog.copilot_assist.validation_gate`
- `afritech.extensions.afriprog.design_generator`
- `afritech.extensions.afriprog.design_generator.architecture`
- `afritech.extensions.afriprog.design_generator.architecture.architecture_generator`
- `afritech.extensions.afriprog.design_generator.architecture.dependency_mapper`
- `afritech.extensions.afriprog.design_generator.architecture.module_generator`
- `afritech.extensions.afriprog.design_generator.contracts`
- `afritech.extensions.afriprog.design_generator.contracts.api_contract_generator`
- `afritech.extensions.afriprog.design_generator.contracts.database_contract_generator`
- `afritech.extensions.afriprog.design_generator.contracts.event_contract_generator`
- `afritech.extensions.afriprog.design_generator.design_orchestrator`
- `afritech.extensions.afriprog.design_generator.design_reviewer`
- `afritech.extensions.afriprog.design_generator.evidence`
- `afritech.extensions.afriprog.design_generator.evidence.design_evidence_generator`
- `afritech.extensions.afriprog.design_generator.planning`
- `afritech.extensions.afriprog.design_generator.planning.implementation_plan_generator`
- `afritech.extensions.afriprog.design_generator.planning.milestone_generator`
- `afritech.extensions.afriprog.design_generator.requirements`
- `afritech.extensions.afriprog.design_generator.requirements.domain_analyzer`
- `afritech.extensions.afriprog.design_generator.requirements.requirements_extractor`
- `afritech.extensions.afriprog.evidence`
- `afritech.extensions.afriprog.evidence.evidence_generator`
- `afritech.extensions.afriprog.evidence.evidence_model`
- `afritech.extensions.afriprog.execution`
- `afritech.extensions.afriprog.execution.loop_engine`
- `afritech.extensions.afriprog.git_agent`
- `afritech.extensions.afriprog.git_agent.git_client`
- `afritech.extensions.afriprog.git_agent.pr_generator`
- `afritech.extensions.afriprog.monitoring`
- `afritech.extensions.afriprog.monitoring.lifecycle_monitor`
- `afritech.extensions.afriprog.orchestrator`
- `afritech.extensions.afriprog.repository_intelligence`
- `afritech.extensions.afriprog.repository_intelligence.contract_locator`
- `afritech.extensions.afriprog.repository_intelligence.orchestrator_preview`
- `afritech.extensions.afriprog.repository_intelligence.repo_loader`
- `afritech.extensions.afriprog.repository_intelligence.report_builder`
- `afritech.extensions.afriprog.repository_intelligence.structure_mapper`
- `afritech.extensions.afriprog.repository_intelligence.surface_locator`
- `afritech.extensions.afriprog.repository_intelligence.test_mapper`
- `afritech.extensions.afriprog.task_planner`
- `afritech.extensions.afriprog.task_planner.failure_parser`
- `afritech.extensions.afriprog.task_planner.planner`
- `afritech.extensions.afriprog.task_planner.task_model`
- `afritech.extensions.afriprog.task_planner.task_types`
- `afritech.extensions.afriprog.validator_runner`
- `afritech.extensions.afriprog.validator_runner.command_result`
- `afritech.features`
- `afritech.fintech`
- `afritech.fintech.mock_provider`
- `afritech.fintech.payment_provider`
- `afritech.fintech.webhook_security`
- `afritech.fintech.webhooks`
- `afritech.global_verification`
- `afritech.governance`
- `afritech.governance.adr_anchor`
- `afritech.guards`
- `afritech.guards.edge_input_guard`
- `afritech.guards.engine`
- `afritech.identity`
- `afritech.identity.mobility_participant`
- `afritech.integration_platform`
- `afritech.integration_platform.audit`
- `afritech.integration_platform.cache`
- `afritech.integration_platform.circuit_breaker`
- `afritech.integration_platform.contracts`
- `afritech.integration_platform.credentials`
- `afritech.integration_platform.errors`
- `afritech.integration_platform.event_client`
- `afritech.integration_platform.evidence`
- `afritech.integration_platform.health`
- `afritech.integration_platform.http_client`
- `afritech.integration_platform.idempotency`
- `afritech.integration_platform.polling`
- `afritech.integration_platform.provider_registry`
- `afritech.integration_platform.retry`
- `afritech.integration_platform.synchronization`
- `afritech.integration_platform.telemetry`
- `afritech.integration_platform.transform`
- `afritech.integration_platform.webhook_client`
- `afritech.integration_platform.websocket_client`
- `afritech.intelligence`
- `afritech.intelligence.mobile_projection`
- `afritech.middleware`
- `afritech.middleware.circuit_breaker`
- `afritech.middleware.distributed_governance`
- `afritech.middleware.governance_middleware`
- `afritech.middleware.multi_region_redis`
- `afritech.middleware.rate_limiter`
- `afritech.middleware.redis_circuit_breaker`
- `afritech.middleware.redis_rate_limiter`
- `afritech.middleware.request_logging`
- `afritech.mobility`
- `afritech.mobility.cross_border_federation`
- `afritech.mobility.federation`
- `afritech.mobility.federation_invariants`
- `afritech.mobility.field_evidence`
- `afritech.mobility.fleet_governance`
- `afritech.mobility.fleet_governance_invariants`
- `afritech.mobility.institutional_networks`
- `afritech.mobility.intelligence_layer`
- `afritech.mobility.legal_compliance_layer`
- `afritech.mobility.logistics_custody_chain`
- `afritech.mobility.logistics_custody_invariants`
- `afritech.mobility.market`
- `afritech.mobility.market_invariants`
- `afritech.mobility.pilot_deployment_architecture`
- `afritech.mobility.public_evidence_api`
- `afritech.mobility.real_time_execution_engine`
- `afritech.mobility.realtime_hub`
- `afritech.mobility.reconciliation`
- `afritech.mobility.regulator_certification_layer`
- `afritech.mobility.self_auditing_network`
- `afritech.mobility.settlement_boundary`
- `afritech.mobility.settlement_invariants`
- `afritech.mobility.trust_dispatch`
- `afritech.mobility.trust_dispatch_invariants`
- `afritech.mobility.trust_network`
- `afritech.mobility.trust_network_invariants`
- `afritech.novacodepro`
- `afritech.novacodepro.ai_auto_generator`
- `afritech.novacodepro.auth_accounts`
- `afritech.novacodepro.completion_standard`
- `afritech.novacodepro.edos`
- `afritech.novacodepro.enterprise_framework`
- `afritech.novacodepro.enterprise_os`
- `afritech.novacodepro.eros`
- `afritech.novacodepro.ncp003`
- `afritech.novacodepro.ncp004`
- `afritech.novacodepro.ncp005`
- `afritech.novacodepro.ncp006a`
- `afritech.novacodepro.ncp006b`
- `afritech.novacodepro.ncp007`
- `afritech.novacodepro.ncp008`
- `afritech.novacodepro.operating_fabric`
- `afritech.novacodepro.operational_verification`
- `afritech.novacodepro.operational_verification.enums`
- `afritech.novacodepro.operational_verification.errors`
- `afritech.novacodepro.operational_verification.events`
- `afritech.novacodepro.operational_verification.evidence`
- `afritech.novacodepro.operational_verification.hashing`
- `afritech.novacodepro.operational_verification.models`
- `afritech.novacodepro.operational_verification.policy`
- `afritech.novacodepro.operational_verification.repository`
- `afritech.novacodepro.operational_verification.service`
- `afritech.novacodepro.operational_verification.status`
- `afritech.novacodepro.platform`
- `afritech.novacodepro.product_factory`
- `afritech.novacodepro.product_factory_enterprise`
- `afritech.novacodepro.production_readiness`
- `afritech.novacodepro.solution_engineering`
- `afritech.novacodepro.ux_operating_system`
- `afritech.novacodepro.workflow_fabric`
- `afritech.novacodepro.workspace`
- `afritech.novaid`
- `afritech.novaid.ai`
- `afritech.novaid.api`
- `afritech.novaid.application`
- `afritech.novaid.application.authentication`
- `afritech.novaid.application.lockout`
- `afritech.novaid.application.passwords`
- `afritech.novaid.application.recovery`
- `afritech.novaid.application.sessions`
- `afritech.novaid.application.webauthn`
- `afritech.novaid.audit_replay`
- `afritech.novaid.config`
- `afritech.novaid.core`
- `afritech.novaid.domain`
- `afritech.novaid.domain.models`
- `afritech.novaid.domain.webauthn`
- `afritech.novaid.observability`
- `afritech.novaid.outbox`
- `afritech.novaid.persistence`
- `afritech.novaid.persistence.migrations`
- `afritech.novaid.persistence.pool`
- `afritech.novaid.persistence.postgres`
- `afritech.novaid.persistence.sqlite`
- `afritech.novaid.repository`
- `afritech.novaid.revocation`
- `afritech.novaid.revocation_delivery`
- `afritech.novaid.runtime`
- `afritech.novaid.security`
- `afritech.novaid.service`
- `afritech.novaid.standards`
- `afritech.novaid.surfaces`
- `afritech.novaid.tokens`
- `afritech.novaid.trust`
- `afritech.novaid.webauthn_coordination`
- `afritech.novaid.webauthn_delivery`
- `afritech.novapay`
- `afritech.novapay.ecosystem_contract`
- `afritech.novapay.migration`
- `afritech.novapay.portal_suite`
- `afritech.novapay.repository`
- `afritech.novapay.schema`
- `afritech.novapay.service`
- `afritech.novapay.surfaces`
- `afritech.novaride_runtime`
- `afritech.novaride_runtime.common`
- `afritech.novaride_runtime.common.clocks`
- `afritech.novaride_runtime.common.errors`
- `afritech.novaride_runtime.common.geography`
- `afritech.novaride_runtime.common.idempotency`
- `afritech.novaride_runtime.common.identifiers`
- `afritech.novaride_runtime.common.money`
- `afritech.novaride_runtime.config`
- `afritech.novaride_runtime.events`
- `afritech.novaride_runtime.events.envelope`
- `afritech.novaride_runtime.events.hashing`
- `afritech.novaride_runtime.events.registry`
- `afritech.novaride_runtime.events.replay`
- `afritech.novaride_runtime.events.replay_planner`
- `afritech.novaride_runtime.events.replay_verifier`
- `afritech.novaride_runtime.events.schema_registry`
- `afritech.novaride_runtime.models`
- `afritech.novaride_runtime.operations`
- `afritech.novaride_runtime.operations_workspace`
- `afritech.novaride_runtime.persistence`
- `afritech.novaride_runtime.persistence.memory`
- `afritech.novaride_runtime.readiness`
- `afritech.novaride_runtime.replay`
- `afritech.novaride_runtime.replay.dependencies`
- `afritech.novaride_runtime.replay.hashing`
- `afritech.novaride_runtime.replay.lifecycle`
- `afritech.novaride_runtime.replay.memory_repository`
- `afritech.novaride_runtime.replay.models`
- `afritech.novaride_runtime.replay.postgres_repository`
- `afritech.novaride_runtime.replay.repository`
- `afritech.novaride_runtime.replay.service`
- `afritech.novaride_runtime.resilience`
- `afritech.novaride_runtime.security`
- `afritech.novaride_runtime.services`
- `afritech.novaride_runtime.slo`
- `afritech.novaride_runtime.sync_security`
- `afritech.novascript`
- `afritech.novascript.schemas`
- `afritech.novascript.service`
- `afritech.novascript.v2`
- `afritech.novascript.v2.adoption`
- `afritech.novascript.v2.certificates`
- `afritech.novascript.v2.compliance`
- `afritech.novascript.v2.economy`
- `afritech.novascript.v2.engine`
- `afritech.novascript.v2.explainability`
- `afritech.novascript.v2.federation`
- `afritech.novascript.v2.graph`
- `afritech.novascript.v2.intelligence`
- `afritech.novascript.v2.knowledge`
- `afritech.novascript.v2.memory`
- `afritech.novascript.v2.monitoring`
- `afritech.novascript.v2.parser`
- `afritech.novascript.v2.persistence`
- `afritech.novascript.v2.policy`
- `afritech.novascript.v2.prompts`
- `afritech.novascript.v2.providers`
- `afritech.novascript.v2.receipts`
- `afritech.novascript.v2.remediation`
- `afritech.novascript.v2.tools`
- `afritech.novascript.v2.workflow`
- `afritech.observability`
- `afritech.observability.opentelemetry`
- `afritech.ops_dashboard`
- `afritech.partner_certification`
- `afritech.partner_governance`
- `afritech.platform_contracts`
- `afritech.platform_contracts.federation`
- `afritech.platform_contracts.registry`
- `afritech.platform_contracts.runtime`
- `afritech.platform_contracts.schema_registry`
- `afritech.platform_operations`
- `afritech.platform_operations.feature_flags`
- `afritech.platform_operations.policy`
- `afritech.platform_operations.registry`
- `afritech.platform_operations.reliability`
- `afritech.platform_operations.rollout`
- `afritech.platform_operations.workflow`
- `afritech.platform_runtime`
- `afritech.platform_runtime.activation`
- `afritech.platform_runtime.adapters`
- `afritech.platform_runtime.adapters.base`
- `afritech.platform_runtime.adapters.docker_compose`
- `afritech.platform_runtime.adapters.kubernetes`
- `afritech.platform_runtime.adapters.nats`
- `afritech.platform_runtime.adapters.object_storage`
- `afritech.platform_runtime.adapters.postgres`
- `afritech.platform_runtime.adapters.redis`
- `afritech.platform_runtime.adapters.secrets`
- `afritech.platform_runtime.adapters.systemd`
- `afritech.platform_runtime.adapters.workers`
- `afritech.platform_runtime.command_executor`
- `afritech.platform_runtime.compatibility`
- `afritech.platform_runtime.config`
- `afritech.platform_runtime.contracts`
- `afritech.platform_runtime.deployment_verifier`
- `afritech.platform_runtime.errors`
- `afritech.platform_runtime.executable_runtime`
- `afritech.platform_runtime.infrastructure`
- `afritech.platform_runtime.models`
- `afritech.platform_runtime.operational`
- `afritech.platform_runtime.operational.activation_certificate`
- `afritech.platform_runtime.operational.evidence_store`
- `afritech.platform_runtime.operational.orchestrator`
- `afritech.platform_runtime.operational.probes`
- `afritech.platform_runtime.operational.readiness`
- `afritech.platform_runtime.operational.recovery`
- `afritech.platform_runtime.operational.restart_recovery`
- `afritech.platform_runtime.operational.rollback`
- `afritech.platform_runtime.operational.verification`
- `afritech.platform_runtime.persistence`
- `afritech.platform_runtime.persistence.migrations`
- `afritech.platform_runtime.persistence.models`
- `afritech.platform_runtime.persistence.repository`
- `afritech.platform_runtime.product_loader`
- `afritech.platform_runtime.protected_configuration`
- `afritech.platform_runtime.provisioning`
- `afritech.platform_runtime.query_executor`
- `afritech.platform_runtime.registry`
- `afritech.platform_runtime.route_registry`
- `afritech.platform_runtime.runtime_evidence`
- `afritech.platform_runtime.secret_resolver`
- `afritech.platform_runtime.worker_registry`
- `afritech.platform_runtime.worker_supervisor`
- `afritech.registry.loader`
- `afritech.registry.snapshot`
- `afritech.runtime`
- `afritech.runtime.admission`
- `afritech.runtime.admission.controller`
- `afritech.runtime.audit.ledger`
- `afritech.runtime.kernel.execute`
- `afritech.runtime.runtime_engine`
- `afritech.runtime_monitoring`
- `afritech.runtime_monitoring.anomaly_classifier`
- `afritech.runtime_monitoring.anomaly_context_builder`
- `afritech.runtime_monitoring.anomaly_detector`
- `afritech.runtime_monitoring.anomaly_to_proposal`
- `afritech.runtime_monitoring.monitor`
- `afritech.runtime_monitoring.monitoring_validators`
- `afritech.sdk`
- `afritech.sdk.external_verifier`
- `afritech.sdk.novascript`
- `afritech.sdk.novatrust`
- `afritech.sdk.partner_registry`
- `afritech.sdk.partner_verification`
- `afritech.sdk.public_verifier`
- `afritech.sdk.semantic_admission`
- `afritech.sdk.trust_network`
- `afritech.semantic_engine.evaluator.evaluator`
- `afritech.semantic_engine.inspection`
- `afritech.semantic_engine.ir.hasher`
- `afritech.semantic_engine.ir.schema`
- `afritech.semantic_engine.optimizer.normalizer`
- `afritech.semantic_engine.parser.ir_builder`
- `afritech.semantic_engine.proof.proof_builder`
- `afritech.semantic_engine.satisfiability.solver`
- `afritech.services`
- `afritech.services.africonnecttl`
- `afritech.services.africonnecttl.contracts`
- `afritech.services.africonnecttl.execution`
- `afritech.services.africonnecttl.models`
- `afritech.services.africonnecttl.reducers`
- `afritech.services.africonnecttl.registry`
- `afritech.shared.types`
- `afritech.simulation`
- `afritech.simulation.pilot_dataset`
- `afritech.simulation.validation_receipt`
- `afritech.storage`
- `afritech.storage.event_log`
- `afritech.storage.event_schema`
- `afritech.tools.feature_registry_verifier`
- `afritech.trust_badges`
- `afritech.trust_federation`
- `afritech.workers.mobile_push_worker`
- `afritech.zk`
- `afritech.zk.groth16_prover`
- `afritech.zk.groth16_verifier`
- `afritech.zk.interface`
- `afritech.zk.mock_snark`
- `afritech.zk.registry`

### Security (16)

- `afritech.security`
- `afritech.security.adversarial_engine`
- `afritech.security.ai_anomaly_engine`
- `afritech.security.anomaly`
- `afritech.security.anomaly_ml`
- `afritech.security.architecture_signing`
- `afritech.security.device_identity`
- `afritech.security.ed25519`
- `afritech.security.event_authenticator`
- `afritech.security.integrity_trace`
- `afritech.security.ip_control`
- `afritech.security.key_manager`
- `afritech.security.mutation_guard`
- `afritech.security.rate_limit`
- `afritech.security.signing`
- `afritech.security.trust_registry`

### Trust And Registry (4)

- `afritech.partner_registry`
- `afritech.partner_verification`
- `afritech.standards_dependency`
- `afritech.trust_network`

## Direct Startup Imports

- `afritech.api.afriprogramming_control_api`
- `afritech.api.afriride_mobile_release_api`
- `afritech.api.afriride_next_gen_mobile_api`
- `afritech.api.afriride_operational_api`
- `afritech.api.afroprog_workspace_api`
- `afritech.api.ai_auto_generator_api`
- `afritech.api.api_catalog_api`
- `afritech.api.api_platform_admin_api`
- `afritech.api.architecture_proof_api`
- `afritech.api.auth.jwt_device_auth`
- `afritech.api.contracts.schema_registry_api`
- `afritech.api.contracts.schema_registry_middleware`
- `afritech.api.core_platform_api`
- `afritech.api.dashboard_gateway_api`
- `afritech.api.data_governance_api`
- `afritech.api.delivery_platform_api`
- `afritech.api.documentation_compliance_api`
- `afritech.api.executable_runtime_api`
- `afritech.api.feature_registry_api`
- `afritech.api.ingestion.event_ingestion`
- `afritech.api.integration_platform_api`
- `afritech.api.mobile_intelligence_api`
- `afritech.api.novacodepro_ncp007_api`
- `afritech.api.novacodepro_ncp008_api`
- `afritech.api.novacodepro_operational_verification_api`
- `afritech.api.novacodepro_platform_api`
- `afritech.api.novacodepro_product_factory_api`
- `afritech.api.novacodepro_workflow_fabric_api`
- `afritech.api.novacodepro_workspace_api`
- `afritech.api.novaid_api`
- `afritech.api.novaid_audit_replay_api`
- `afritech.api.novapay_ecosystem_api`
- `afritech.api.novapay_runtime_api`
- `afritech.api.novaportal_suite_api`
- `afritech.api.novaride_operations_api`
- `afritech.api.novaride_runtime_api`
- `afritech.api.novascript_api`
- `afritech.api.novatech_intranet_api`
- `afritech.api.ops_governance_api`
- `afritech.api.partner_certification_api`
- `afritech.api.partner_governance_api`
- `afritech.api.partner_registry_api`
- `afritech.api.partner_verification_api`
- `afritech.api.phase0_api`
- `afritech.api.phase10_api`
- `afritech.api.phase11_api`
- `afritech.api.phase12_api`
- `afritech.api.phase13_api`
- `afritech.api.phase1_api`
- `afritech.api.phase2_api`
- `afritech.api.phase3_api`
- `afritech.api.phase4_api`
- `afritech.api.phase5_api`
- `afritech.api.phase6_api`
- `afritech.api.phase7_api`
- `afritech.api.phase8_api`
- `afritech.api.phase9_api`
- `afritech.api.platform_runtime_api`
- `afritech.api.public_gateway_api`
- `afritech.api.public_verification_api`
- `afritech.api.realtime.dashboard_bus`
- `afritech.api.realtime.ride_bus`
- `afritech.api.runtime_activation_api`
- `afritech.api.runtime_infrastructure_api`
- `afritech.api.runtime_operations_api`
- `afritech.api.runtime_verification_api`
- `afritech.api.runtime_worker_api`
- `afritech.api.solution_engineering_api`
- `afritech.api.system_status`
- `afritech.api.trace_api`
- `afritech.api.trust_network_api`
- `afritech.api_platform`
- `afritech.architecture.anchor_indexer`
- `afritech.core_platform.adaptive_sla`
- `afritech.core_platform.autonomous_control`
- `afritech.edge.adapter.runtime_adapter`
- `afritech.edge.adapter.validation`
- `afritech.edge.ingestion.queue_ingestor`
- `afritech.edge.normalization.normalizer`
- `afritech.edge.normalization.validation`
- `afritech.execution.partition.router`
- `afritech.execution.queue.partitioned_queue`
- `afritech.execution.worker.worker_pool`
- `afritech.middleware.distributed_governance`
- `afritech.middleware.multi_region_redis`
- `afritech.middleware.request_logging`
- `afritech.novacodepro.platform`
- `afritech.novaid.runtime`
- `afritech.novaride_runtime.replay.dependencies`
- `afritech.observability.opentelemetry`
- `afritech.partner_certification`
- `afritech.partner_governance`
- `afritech.partner_registry`
- `afritech.partner_verification`
- `afritech.platform_runtime`
- `afritech.platform_runtime.activation`
- `afritech.platform_runtime.adapters.base`
- `afritech.platform_runtime.deployment_verifier`
- `afritech.platform_runtime.executable_runtime`
- `afritech.platform_runtime.operational`
- `afritech.platform_runtime.persistence.repository`
- `afritech.platform_runtime.provisioning`
- `afritech.platform_runtime.route_registry`
- `afritech.platform_runtime.runtime_evidence`
- `afritech.platform_runtime.worker_supervisor`
- `afritech.standards_dependency`
- `afritech.trust_network`

## Interpretation

- The runtime graph is based on the current production-style FastAPI entrypoint.
- The inventory graph is repo-wide and broader than the active startup path.
- Django-bound surfaces are allowed in the repo but must remain outside FastAPI import-time coupling.
- Regenerate this file after major routing, deployment, or domain-boundary changes.

