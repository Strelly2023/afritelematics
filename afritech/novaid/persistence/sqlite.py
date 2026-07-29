"""Normalized transactional adapter used for local verification.

The SQL schema mirrors the PostgreSQL migration. SQLite is intentionally only a
local test adapter and is not presented as PostgreSQL operational evidence.
"""
# ruff: noqa: E501 -- normalized DDL is kept legible and grep-friendly.

from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime, timedelta
import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..domain.models import Identity, IdentityStatus, RequestContext, SecurityEvent
from .biometric_sqlite_repository import BiometricSQLiteRepositoryMixin
from .authorization_repository import AuthorizationRepository
from .identity_codec import (
    encode_addresses,
    encode_contact_points,
    encode_identifiers,
    encode_identity_names,
    encode_legal_name,
    encode_metadata,
    identity_from_row,
)


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS novaid_tenants(
 tenant_id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ACTIVE','SUSPENDED','DISABLED')),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
 tenant_type TEXT NOT NULL DEFAULT 'ORGANISATION',tier TEXT NOT NULL DEFAULT 'STANDARD',
 legal_entity TEXT,brand TEXT,settings TEXT NOT NULL DEFAULT '{}',
 security_policy TEXT NOT NULL DEFAULT '{}',metadata TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS novaid_identities(
 identity_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES novaid_tenants(tenant_id), normalized_email TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('PENDING_VERIFICATION','ACTIVE','LOCKED','SUSPENDED','DISABLED','DELETED')),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
 security_version INTEGER NOT NULL DEFAULT 1,
 identity_type TEXT NOT NULL DEFAULT 'PERSON',
 legal_name TEXT,
 preferred_name TEXT,
 alternative_names TEXT NOT NULL DEFAULT '[]',
 contact_points TEXT NOT NULL DEFAULT '[]',
 addresses TEXT NOT NULL DEFAULT '[]',
 identifiers TEXT NOT NULL DEFAULT '[]',
 verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
 assurance_level TEXT NOT NULL DEFAULT 'NID-AL0',
 metadata TEXT NOT NULL DEFAULT '{}',
 UNIQUE(tenant_id, normalized_email));
CREATE INDEX IF NOT EXISTS ix_novaid_identity_tenant ON novaid_identities(tenant_id);
CREATE TABLE IF NOT EXISTS novaid_tenant_memberships(
 membership_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES novaid_tenants(tenant_id),
 identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id), role TEXT NOT NULL, status TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
 CHECK(status IN ('INVITED','ACTIVE','SUSPENDED','REVOKED','EXPIRED')),
 UNIQUE(tenant_id, identity_id));
CREATE TABLE IF NOT EXISTS novaid_permissions(
 permission_id TEXT PRIMARY KEY,tenant_id TEXT,resource TEXT NOT NULL,action TEXT NOT NULL,effect TEXT NOT NULL,
 resource_owner_only INTEGER NOT NULL DEFAULT 0,require_trusted_device INTEGER NOT NULL DEFAULT 0,
 minimum_assurance_level TEXT NOT NULL DEFAULT 'NID-AL0',
 minimum_authentication_strength TEXT NOT NULL DEFAULT 'PASSWORD',created_at TEXT NOT NULL,
 UNIQUE(tenant_id,resource,action,effect));
CREATE TABLE IF NOT EXISTS novaid_roles(
 role_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL REFERENCES novaid_tenants(tenant_id),name TEXT NOT NULL,
 enabled INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,
 version INTEGER NOT NULL DEFAULT 1,UNIQUE(tenant_id,name));
CREATE TABLE IF NOT EXISTS novaid_role_permissions(
 tenant_id TEXT NOT NULL,role_id TEXT NOT NULL REFERENCES novaid_roles(role_id),
 permission_id TEXT NOT NULL REFERENCES novaid_permissions(permission_id),created_at TEXT NOT NULL,
 PRIMARY KEY(tenant_id,role_id,permission_id));
CREATE TABLE IF NOT EXISTS novaid_membership_roles(
 tenant_id TEXT NOT NULL,membership_id TEXT NOT NULL REFERENCES novaid_tenant_memberships(membership_id),
 role_id TEXT NOT NULL REFERENCES novaid_roles(role_id),valid_from TEXT,valid_until TEXT,created_at TEXT NOT NULL,
 PRIMARY KEY(tenant_id,membership_id,role_id));
CREATE TABLE IF NOT EXISTS novaid_authorization_policy_versions(
 tenant_id TEXT NOT NULL,policy_version TEXT NOT NULL,status TEXT NOT NULL,policy_json TEXT NOT NULL,
 created_at TEXT NOT NULL,activated_at TEXT,created_by TEXT NOT NULL,
 PRIMARY KEY(tenant_id,policy_version));
CREATE TABLE IF NOT EXISTS novaid_credentials(
 credential_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id),
 kind TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_password_credentials(
 credential_id TEXT PRIMARY KEY REFERENCES novaid_credentials(credential_id), password_hash TEXT NOT NULL,
 algorithm_version TEXT NOT NULL, expires_at TEXT, compromised_at TEXT);
CREATE TABLE IF NOT EXISTS novaid_otp_challenges(
 challenge_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id),
 purpose TEXT NOT NULL, destination_reference TEXT NOT NULL, secret_hash TEXT NOT NULL UNIQUE,
 created_at TEXT NOT NULL, expires_at TEXT NOT NULL, consumed_at TEXT, attempt_count INTEGER NOT NULL DEFAULT 0,
 maximum_attempts INTEGER NOT NULL, status TEXT NOT NULL, correlation_id TEXT NOT NULL,
 CHECK(expires_at > created_at));
CREATE TABLE IF NOT EXISTS novaid_authentication_sessions(
 session_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id),
 authentication_time TEXT NOT NULL, authentication_strength TEXT NOT NULL, credential_id TEXT,
 device_reference TEXT, client_reference TEXT, risk_score REAL NOT NULL, status TEXT NOT NULL,
 created_at TEXT NOT NULL, last_seen_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT, revocation_reason TEXT,
 version INTEGER NOT NULL DEFAULT 1, membership_id TEXT, authenticated_at TEXT, idle_expires_at TEXT,
 absolute_expires_at TEXT, pending_mfa_expires_at TEXT, step_up_expires_at TEXT, locked_at TEXT,
 expired_at TEXT, compromised_at TEXT, network_reference TEXT, authentication_methods TEXT NOT NULL DEFAULT '[]',
 security_version INTEGER NOT NULL DEFAULT 1, revoked_by TEXT, compromise_reason TEXT,
 CHECK(expires_at > created_at));
CREATE INDEX IF NOT EXISTS ix_novaid_session_tenant_identity ON novaid_authentication_sessions(tenant_id,identity_id,status);
CREATE TABLE IF NOT EXISTS novaid_refresh_token_families(
 family_id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES novaid_authentication_sessions(session_id),
 identity_id TEXT NOT NULL, tenant_id TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
 expires_at TEXT NOT NULL, revoked_at TEXT, version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_refresh_tokens(
 token_id TEXT PRIMARY KEY, family_id TEXT NOT NULL REFERENCES novaid_refresh_token_families(family_id),
 session_id TEXT NOT NULL, identity_id TEXT NOT NULL, tenant_id TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE,
 parent_token_id TEXT, issued_at TEXT NOT NULL, expires_at TEXT NOT NULL, used_at TEXT, revoked_at TEXT,
 replacement_token_id TEXT, status TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_novaid_refresh_family ON novaid_refresh_tokens(family_id,status);
CREATE TABLE IF NOT EXISTS novaid_authentication_attempts(
 attempt_id TEXT PRIMARY KEY, identity_id TEXT, tenant_id TEXT NOT NULL, credential_type TEXT NOT NULL,
 result TEXT NOT NULL, reason_code TEXT NOT NULL, occurred_at TEXT NOT NULL, correlation_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_identity_risk_states(
 identity_id TEXT NOT NULL, tenant_id TEXT NOT NULL, risk_score REAL NOT NULL, status TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(identity_id,tenant_id));
CREATE TABLE IF NOT EXISTS novaid_identity_status_history(
 transition_id TEXT PRIMARY KEY, identity_id TEXT NOT NULL, tenant_id TEXT NOT NULL, previous_status TEXT NOT NULL,
 new_status TEXT NOT NULL, reason_code TEXT NOT NULL, actor_identity_id TEXT NOT NULL, correlation_id TEXT NOT NULL,
 occurred_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_security_events(
 event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, severity TEXT NOT NULL, tenant_id TEXT NOT NULL,
 actor_identity_id TEXT NOT NULL, subject_identity_id TEXT NOT NULL, correlation_id TEXT NOT NULL,
 request_id TEXT NOT NULL, occurred_at TEXT NOT NULL, recorded_at TEXT NOT NULL, outcome TEXT NOT NULL,
 reason_codes TEXT NOT NULL, metadata TEXT NOT NULL, schema_version INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS ix_novaid_event_correlation ON novaid_security_events(correlation_id,event_type,occurred_at);
CREATE TABLE IF NOT EXISTS novaid_idempotency_records(
 tenant_id TEXT NOT NULL, idempotency_key TEXT NOT NULL, payload_hash TEXT NOT NULL,
 response_json TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(tenant_id,idempotency_key));
CREATE TABLE IF NOT EXISTS novaid_authentication_locks(
 tenant_id TEXT NOT NULL, identifier_hash TEXT NOT NULL, failure_count INTEGER NOT NULL,
 window_started_at TEXT NOT NULL, locked_until TEXT, updated_at TEXT NOT NULL,
 PRIMARY KEY(tenant_id,identifier_hash));
CREATE TABLE IF NOT EXISTS novaid_security_outbox(
 outbox_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, event_type TEXT NOT NULL,
 resource_type TEXT NOT NULL, resource_id TEXT NOT NULL, event_version INTEGER NOT NULL,
 payload TEXT NOT NULL, created_at TEXT NOT NULL, published_at TEXT,
 attempt_count INTEGER NOT NULL DEFAULT 0, last_error TEXT, next_attempt_at TEXT,
 status TEXT NOT NULL, available_at TEXT, last_attempt_at TEXT, lease_owner TEXT,
 lease_expires_at TEXT);
CREATE TABLE IF NOT EXISTS novaid_webauthn_registration_challenges(
 challenge_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT NOT NULL,
 purpose TEXT NOT NULL, challenge_hash TEXT NOT NULL, rp_id TEXT NOT NULL, origin TEXT NOT NULL,
 created_at TEXT NOT NULL, expires_at TEXT NOT NULL, consumed_at TEXT, status TEXT NOT NULL,
 attempt_count INTEGER NOT NULL, maximum_attempts INTEGER NOT NULL, correlation_id TEXT NOT NULL,
 request_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_webauthn_authentication_challenges(
 challenge_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT, session_id TEXT,
 purpose TEXT NOT NULL, challenge_hash TEXT NOT NULL, rp_id TEXT NOT NULL, origin TEXT NOT NULL,
 created_at TEXT NOT NULL, expires_at TEXT NOT NULL, consumed_at TEXT, status TEXT NOT NULL,
 attempt_count INTEGER NOT NULL, maximum_attempts INTEGER NOT NULL, correlation_id TEXT NOT NULL,
 request_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_authenticators(
 authenticator_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, aaguid TEXT NOT NULL,
 friendly_name TEXT, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_webauthn_credentials(
 credential_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT NOT NULL,
 membership_id TEXT, authenticator_id TEXT, user_handle BLOB NOT NULL, public_key_cose BLOB NOT NULL,
 public_key_algorithm INTEGER NOT NULL, sign_count INTEGER NOT NULL, aaguid TEXT NOT NULL,
 attestation_format TEXT NOT NULL, attestation_type TEXT NOT NULL, transports TEXT NOT NULL,
 backup_eligible INTEGER NOT NULL, backup_state INTEGER NOT NULL, discoverable INTEGER NOT NULL,
 resident_key INTEGER NOT NULL, user_verification INTEGER NOT NULL, created_at TEXT NOT NULL,
 last_used_at TEXT, last_verified_at TEXT, status TEXT NOT NULL, version INTEGER NOT NULL,
 friendly_name TEXT, device_reference TEXT, provider_reference TEXT);
CREATE TABLE IF NOT EXISTS novaid_authenticator_bindings(
 binding_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT NOT NULL,
 authenticator_id TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_attestation_records(
 attestation_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, credential_id TEXT NOT NULL,
 format TEXT NOT NULL, attestation_type TEXT NOT NULL, trust_path_metadata TEXT NOT NULL,
 verified_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_authenticator_status_history(
 transition_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, credential_id TEXT NOT NULL,
 previous_status TEXT NOT NULL, new_status TEXT NOT NULL, reason_code TEXT NOT NULL,
 occurred_at TEXT NOT NULL, actor_identity_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_recovery_code_batches(
 batch_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,identity_id TEXT NOT NULL,status TEXT NOT NULL,
 created_at TEXT NOT NULL,expires_at TEXT NOT NULL,revoked_at TEXT,version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_recovery_codes(
 recovery_code_id TEXT PRIMARY KEY,batch_id TEXT NOT NULL,tenant_id TEXT NOT NULL,identity_id TEXT NOT NULL,
 code_hash TEXT NOT NULL UNIQUE,status TEXT NOT NULL,created_at TEXT NOT NULL,expires_at TEXT NOT NULL,
 used_at TEXT,revoked_at TEXT,attempt_count INTEGER NOT NULL DEFAULT 0,version INTEGER NOT NULL DEFAULT 1);
CREATE INDEX IF NOT EXISTS ix_novaid_recovery_codes_batch ON novaid_recovery_codes(batch_id,status);
CREATE TABLE IF NOT EXISTS novaid_account_recovery_requests(
 recovery_request_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,identity_id TEXT NOT NULL,status TEXT NOT NULL,
 recovery_method TEXT NOT NULL,requested_at TEXT NOT NULL,expires_at TEXT NOT NULL,approved_at TEXT,
 approved_by TEXT,completed_at TEXT,rejected_at TEXT,cancelled_at TEXT,reason TEXT NOT NULL,
 correlation_id TEXT NOT NULL,request_id TEXT NOT NULL,device_reference TEXT,network_reference TEXT,
 version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_account_recovery_approvals(
 approval_id TEXT PRIMARY KEY,recovery_request_id TEXT NOT NULL,tenant_id TEXT NOT NULL,
 approver_identity_id TEXT NOT NULL,decision TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL,
 expires_at TEXT NOT NULL,UNIQUE(recovery_request_id,approver_identity_id));
CREATE TABLE IF NOT EXISTS novaid_account_recovery_evidence(
 evidence_id TEXT PRIMARY KEY,recovery_request_id TEXT NOT NULL,tenant_id TEXT NOT NULL,
 identity_id TEXT NOT NULL,method TEXT NOT NULL,result TEXT NOT NULL,risk_indicators TEXT NOT NULL,
 actor_identity_id TEXT,correlation_id TEXT NOT NULL,request_id TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_tenant_webauthn_policies(
 tenant_id TEXT PRIMARY KEY,require_webauthn INTEGER NOT NULL,passkeys_enabled INTEGER NOT NULL,
 passwordless_enabled INTEGER NOT NULL,require_phishing_resistant_step_up INTEGER NOT NULL,
 user_verification TEXT NOT NULL,attestation TEXT NOT NULL,maximum_credentials INTEGER NOT NULL,
 recovery_codes_enabled INTEGER NOT NULL,recovery_code_count INTEGER NOT NULL,
 recovery_code_expiry_days INTEGER NOT NULL,recovery_approval_count INTEGER NOT NULL,
 recovery_requires_new_authenticator INTEGER NOT NULL,step_up_seconds INTEGER NOT NULL,
 updated_at TEXT NOT NULL,updated_by TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_tenant_webauthn_policy_history(
 policy_history_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,policy_version INTEGER NOT NULL,
 status TEXT NOT NULL,policy TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL,
 created_by TEXT NOT NULL,UNIQUE(tenant_id,policy_version));
CREATE TABLE IF NOT EXISTS novaid_webauthn_challenge_coordination(
 coordination_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,challenge_id TEXT NOT NULL,purpose TEXT NOT NULL,
 status TEXT NOT NULL,challenge_version INTEGER NOT NULL,created_at TEXT NOT NULL,expires_at TEXT NOT NULL,
 consumed_at TEXT,UNIQUE(tenant_id,challenge_id));
CREATE TABLE IF NOT EXISTS novaid_webauthn_outbox(
 outbox_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,event_type TEXT NOT NULL,resource_id TEXT NOT NULL,
 event_version INTEGER NOT NULL,payload TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,
 available_at TEXT NOT NULL,published_at TEXT,attempt_count INTEGER NOT NULL DEFAULT 0,
 version INTEGER NOT NULL DEFAULT 1,correlation_id TEXT NOT NULL DEFAULT '',
 request_id TEXT NOT NULL DEFAULT '',resource_type TEXT NOT NULL DEFAULT 'WEBAUTHN_CREDENTIAL',
 lease_owner TEXT,lease_expires_at TEXT,next_attempt_at TEXT,last_attempt_at TEXT,
 last_error TEXT,dead_letter_reason TEXT);
CREATE TABLE IF NOT EXISTS novaid_webauthn_event_checkpoints(
 consumer_name TEXT NOT NULL,tenant_id TEXT NOT NULL,event_version INTEGER NOT NULL,
 updated_at TEXT NOT NULL,resource_type TEXT NOT NULL DEFAULT '',resource_reference TEXT NOT NULL DEFAULT '',
 last_event_id TEXT,applied_at TEXT,PRIMARY KEY(consumer_name,tenant_id));
CREATE TABLE IF NOT EXISTS novaid_audit_replay_requests(
 replay_request_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,organization_id TEXT NOT NULL,environment_id TEXT NOT NULL DEFAULT '',
 requested_by TEXT NOT NULL,approved_by TEXT,executed_by TEXT,event_type_filters TEXT NOT NULL DEFAULT '[]',
 aggregate_filters TEXT NOT NULL DEFAULT '{}',subject_filters TEXT NOT NULL DEFAULT '{}',start_time TEXT,end_time TEXT,
 source_checkpoint TEXT,target_checkpoint TEXT,replay_mode TEXT NOT NULL,dry_run INTEGER NOT NULL DEFAULT 0,
 reason TEXT NOT NULL,risk_level TEXT NOT NULL,status TEXT NOT NULL,maximum_events INTEGER NOT NULL DEFAULT 100,
 created_at TEXT NOT NULL,approved_at TEXT,started_at TEXT,completed_at TEXT,cancelled_at TEXT,evidence_id TEXT,
 correlation_id TEXT NOT NULL,request_id TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS novaid_audit_replay_approvals(
 approval_id TEXT PRIMARY KEY,replay_request_id TEXT NOT NULL,tenant_id TEXT NOT NULL,organization_id TEXT NOT NULL,
 approver_id TEXT NOT NULL,decision TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL,
 UNIQUE(replay_request_id,approver_id,decision));
CREATE TABLE IF NOT EXISTS novaid_audit_replay_event_results(
 result_id TEXT PRIMARY KEY,replay_request_id TEXT NOT NULL,tenant_id TEXT NOT NULL,organization_id TEXT NOT NULL,
 event_id TEXT NOT NULL,event_type TEXT NOT NULL,decision TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL,
 UNIQUE(replay_request_id,event_id,decision));

CREATE TABLE IF NOT EXISTS novaid_biometric_consents(
 consent_id TEXT PRIMARY KEY,
 tenant_id TEXT NOT NULL REFERENCES novaid_tenants(tenant_id),
 identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id),
 purpose TEXT NOT NULL,
 policy_version TEXT NOT NULL,
 granted_at TEXT NOT NULL,
 status TEXT NOT NULL,
 expires_at TEXT,
 revoked_at TEXT,
 capture_notice_version TEXT,
 lawful_basis_reference TEXT,
 metadata TEXT NOT NULL DEFAULT '{}',
 CHECK(status IN ('ACTIVE','REVOKED','EXPIRED'))
);

CREATE INDEX IF NOT EXISTS ix_novaid_biometric_consent_identity
 ON novaid_biometric_consents(
  tenant_id,
  identity_id,
  purpose,
  status
 );

CREATE TABLE IF NOT EXISTS novaid_biometric_enrollments(
 enrollment_id TEXT PRIMARY KEY,
 tenant_id TEXT NOT NULL REFERENCES novaid_tenants(tenant_id),
 identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id),
 biometric_type TEXT NOT NULL,
 purpose TEXT NOT NULL,
 consent_id TEXT NOT NULL
  REFERENCES novaid_biometric_consents(consent_id),
 template_reference TEXT NOT NULL,
 provider_reference TEXT NOT NULL,
 algorithm_version TEXT NOT NULL,
 status TEXT NOT NULL,
 capture_device TEXT,
 capture_environment TEXT,
 capture_quality TEXT,
 enrolled_at TEXT,
 expires_at TEXT,
 revoked_at TEXT,
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL,
 version INTEGER NOT NULL,
 metadata TEXT NOT NULL DEFAULT '{}',
 CHECK(version >= 1),
 CHECK(
  biometric_type IN (
   'FACE',
   'FINGERPRINT',
   'IRIS',
   'VOICE'
  )
 ),
 CHECK(
  status IN (
   'PENDING',
   'ACTIVE',
   'SUSPENDED',
   'REVOKED',
   'EXPIRED'
  )
 )
);

CREATE INDEX IF NOT EXISTS ix_novaid_biometric_enrollment_identity
 ON novaid_biometric_enrollments(
  tenant_id,
  identity_id,
  biometric_type,
  status
 );

CREATE INDEX IF NOT EXISTS ix_novaid_biometric_enrollment_consent
 ON novaid_biometric_enrollments(
  tenant_id,
  consent_id
 );

CREATE TABLE IF NOT EXISTS novaid_face_verifications(
 verification_id TEXT PRIMARY KEY,
 tenant_id TEXT NOT NULL REFERENCES novaid_tenants(tenant_id),
 identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id),
 enrollment_id TEXT NOT NULL
  REFERENCES novaid_biometric_enrollments(enrollment_id),
 consent_id TEXT NOT NULL
  REFERENCES novaid_biometric_consents(consent_id),
 purpose TEXT NOT NULL,
 decision TEXT NOT NULL,
 similarity_score REAL NOT NULL,
 match_threshold REAL NOT NULL,
 manual_review_threshold REAL NOT NULL,
 provider_reference TEXT NOT NULL,
 algorithm_version TEXT NOT NULL,
 capture_device TEXT NOT NULL,
 capture_environment TEXT NOT NULL,
 capture_quality TEXT NOT NULL,
 verified_at TEXT NOT NULL,
 version INTEGER NOT NULL DEFAULT 1,
 reason_codes TEXT NOT NULL DEFAULT '[]',
 metadata TEXT NOT NULL DEFAULT '{}',
 CHECK(similarity_score >= 0.0 AND similarity_score <= 1.0),
 CHECK(match_threshold >= 0.0 AND match_threshold <= 1.0),
 CHECK(
  manual_review_threshold >= 0.0
  AND manual_review_threshold <= 1.0
 ),
 CHECK(version >= 1),
 CHECK(
  decision IN (
   'MATCH',
   'NO_MATCH',
   'MANUAL_REVIEW'
  )
 )
);

CREATE INDEX IF NOT EXISTS ix_novaid_face_verification_identity
 ON novaid_face_verifications(
  tenant_id,
  identity_id,
  verified_at
 );

CREATE INDEX IF NOT EXISTS ix_novaid_face_verification_enrollment
 ON novaid_face_verifications(
  tenant_id,
  enrollment_id,
  verified_at
 );

CREATE TABLE IF NOT EXISTS novaid_face_authentications(
 authentication_id TEXT PRIMARY KEY,
 tenant_id TEXT NOT NULL REFERENCES novaid_tenants(tenant_id),
 identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id),
 verification_id TEXT NOT NULL
  REFERENCES novaid_face_verifications(verification_id),
 enrollment_id TEXT NOT NULL
  REFERENCES novaid_biometric_enrollments(enrollment_id),
 purpose TEXT NOT NULL,
 decision TEXT NOT NULL,
 verification_decision TEXT NOT NULL,
 risk_score REAL NOT NULL,
 authentication_strength TEXT NOT NULL,
 current_assurance_level TEXT NOT NULL,
 required_assurance_level TEXT NOT NULL,
 authenticated_at TEXT NOT NULL,
 reason_codes TEXT NOT NULL DEFAULT '[]',
 metadata TEXT NOT NULL DEFAULT '{}',
 CHECK(risk_score >= 0.0 AND risk_score <= 1.0),
 CHECK(
  decision IN (
   'ALLOW',
   'REQUIRE_STEP_UP',
   'REQUIRE_MANUAL_REVIEW',
   'DENY',
   'LOCK_SESSION',
   'LOCK_IDENTITY'
  )
 ),
 CHECK(
  verification_decision IN (
   'MATCH',
   'NO_MATCH',
   'MANUAL_REVIEW'
  )
 )
);

CREATE INDEX IF NOT EXISTS ix_novaid_face_authentication_identity
 ON novaid_face_authentications(
  tenant_id,
  identity_id,
  authenticated_at
 );

CREATE INDEX IF NOT EXISTS ix_novaid_face_authentication_verification
 ON novaid_face_authentications(
  tenant_id,
  verification_id
 );

CREATE TABLE IF NOT EXISTS novaid_liveness_assessments(
 assessment_id TEXT PRIMARY KEY,
 tenant_id TEXT NOT NULL REFERENCES novaid_tenants(tenant_id),
 identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id),
 purpose TEXT NOT NULL,
 decision TEXT NOT NULL,
 attempt_number INTEGER NOT NULL,
 mode TEXT NOT NULL,
 liveness_score REAL NOT NULL,
 presentation_attack_score REAL NOT NULL,
 provider_reference TEXT NOT NULL,
 algorithm_version TEXT NOT NULL,
 capture_device TEXT NOT NULL,
 capture_environment TEXT NOT NULL,
 capture_quality TEXT NOT NULL,
 assessed_at TEXT NOT NULL,
 detected_attack_types TEXT NOT NULL DEFAULT '[]',
 reason_codes TEXT NOT NULL DEFAULT '[]',
 metadata TEXT NOT NULL DEFAULT '{}',
 CHECK(attempt_number >= 1),
 CHECK(liveness_score >= 0.0 AND liveness_score <= 1.0),
 CHECK(
  presentation_attack_score >= 0.0
  AND presentation_attack_score <= 1.0
 ),
 CHECK(mode IN ('PASSIVE','ACTIVE','HYBRID')),
 CHECK(
  decision IN (
   'PASS',
   'RECAPTURE',
   'MANUAL_REVIEW',
   'FAIL',
   'LOCK_SESSION'
  )
 )
);

CREATE INDEX IF NOT EXISTS ix_novaid_liveness_identity
 ON novaid_liveness_assessments(
  tenant_id,
  identity_id,
  assessed_at
 );

CREATE INDEX IF NOT EXISTS ix_novaid_liveness_decision
 ON novaid_liveness_assessments(
  tenant_id,
  decision,
  assessed_at
 );


-- ============================================================
-- NID-P1-004 Step 4F — Governed identity verification
-- ============================================================

CREATE TABLE IF NOT EXISTS
 novaid_identity_verification_evidence (
  workflow_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  identity_id TEXT NOT NULL,
  document_id TEXT NOT NULL,
  document_version INTEGER NOT NULL
   CHECK(document_version >= 1),
  ocr_extraction_id TEXT NOT NULL,
  authenticity_assessment_id TEXT NOT NULL,
  selfie_match_id TEXT NOT NULL,
  evidence_payload TEXT NOT NULL,
  evidence_hash TEXT,
  schema_version INTEGER NOT NULL DEFAULT 1
   CHECK(schema_version >= 1),
  persisted_at TEXT NOT NULL,

  FOREIGN KEY(tenant_id)
   REFERENCES novaid_tenants(tenant_id),

  FOREIGN KEY(identity_id)
   REFERENCES novaid_identities(identity_id),

  UNIQUE(
   tenant_id,
   workflow_id
  )
 );

CREATE INDEX IF NOT EXISTS
 ix_novaid_identity_verification_evidence_identity
 ON novaid_identity_verification_evidence(
  tenant_id,
  identity_id,
  persisted_at
 );

CREATE INDEX IF NOT EXISTS
 ix_novaid_identity_verification_evidence_document
 ON novaid_identity_verification_evidence(
  tenant_id,
  document_id,
  document_version
 );

CREATE INDEX IF NOT EXISTS
 ix_novaid_identity_verification_evidence_components
 ON novaid_identity_verification_evidence(
  tenant_id,
  ocr_extraction_id,
  authenticity_assessment_id,
  selfie_match_id
 );


CREATE TABLE IF NOT EXISTS
 novaid_identity_verifications (
  verification_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  identity_id TEXT NOT NULL,
  workflow_id TEXT NOT NULL,
  document_id TEXT NOT NULL,
  document_version INTEGER NOT NULL
   CHECK(document_version >= 1),
  decision TEXT NOT NULL,
  current_assurance_level TEXT NOT NULL,
  resulting_assurance_level TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  combined_score REAL NOT NULL
   CHECK(
    combined_score >= 0.0
    AND combined_score <= 1.0
   ),
  ocr_score REAL NOT NULL
   CHECK(
    ocr_score >= 0.0
    AND ocr_score <= 1.0
   ),
  authenticity_score REAL NOT NULL
   CHECK(
    authenticity_score >= 0.0
    AND authenticity_score <= 1.0
   ),
  selfie_match_score REAL NOT NULL
   CHECK(
    selfie_match_score >= 0.0
    AND selfie_match_score <= 1.0
   ),
  liveness_score REAL NOT NULL
   CHECK(
    liveness_score >= 0.0
    AND liveness_score <= 1.0
   ),
  reason_codes TEXT NOT NULL,
  verification_payload TEXT NOT NULL,
  verification_hash TEXT,
  verified_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1
   CHECK(version >= 1),

  FOREIGN KEY(tenant_id)
   REFERENCES novaid_tenants(tenant_id),

  FOREIGN KEY(identity_id)
   REFERENCES novaid_identities(identity_id),

  FOREIGN KEY(workflow_id)
   REFERENCES novaid_identity_verification_evidence(
    workflow_id
   ),

  UNIQUE(
   tenant_id,
   verification_id
  ),

  UNIQUE(
   tenant_id,
   workflow_id
  )
 );

CREATE INDEX IF NOT EXISTS
 ix_novaid_identity_verifications_identity
 ON novaid_identity_verifications(
  tenant_id,
  identity_id,
  verified_at
 );

CREATE INDEX IF NOT EXISTS
 ix_novaid_identity_verifications_decision
 ON novaid_identity_verifications(
  tenant_id,
  decision,
  verified_at
 );

CREATE INDEX IF NOT EXISTS
 ix_novaid_identity_verifications_document
 ON novaid_identity_verifications(
  tenant_id,
  document_id,
  document_version
 );

CREATE INDEX IF NOT EXISTS
 ix_novaid_identity_verifications_policy
 ON novaid_identity_verifications(
  tenant_id,
  policy_version,
  verified_at
 );


CREATE TABLE IF NOT EXISTS
 novaid_identity_verification_events (
  event_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  identity_id TEXT NOT NULL,
  verification_id TEXT NOT NULL,
  workflow_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  decision TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  request_id TEXT NOT NULL,
  actor_identity_id TEXT,
  actor_membership_id TEXT,
  policy_version TEXT NOT NULL,
  event_payload TEXT NOT NULL,
  event_hash TEXT,
  occurred_at TEXT NOT NULL,
  persisted_at TEXT NOT NULL,
  schema_version INTEGER NOT NULL DEFAULT 1
   CHECK(schema_version >= 1),

  FOREIGN KEY(tenant_id)
   REFERENCES novaid_tenants(tenant_id),

  FOREIGN KEY(identity_id)
   REFERENCES novaid_identities(identity_id),

  FOREIGN KEY(verification_id)
   REFERENCES novaid_identity_verifications(
    verification_id
   ),

  FOREIGN KEY(workflow_id)
   REFERENCES novaid_identity_verification_evidence(
    workflow_id
   ),

  UNIQUE(
   tenant_id,
   event_id
  )
 );

CREATE INDEX IF NOT EXISTS
 ix_novaid_identity_verification_events_verification
 ON novaid_identity_verification_events(
  tenant_id,
  verification_id,
  occurred_at
 );

CREATE INDEX IF NOT EXISTS
 ix_novaid_identity_verification_events_identity
 ON novaid_identity_verification_events(
  tenant_id,
  identity_id,
  occurred_at
 );

CREATE INDEX IF NOT EXISTS
 ix_novaid_identity_verification_events_workflow
 ON novaid_identity_verification_events(
  tenant_id,
  workflow_id,
  occurred_at
 );

CREATE INDEX IF NOT EXISTS
 ix_novaid_identity_verification_events_correlation
 ON novaid_identity_verification_events(
  tenant_id,
  correlation_id,
  occurred_at
 );

CREATE INDEX IF NOT EXISTS
 ix_novaid_identity_verification_events_type
 ON novaid_identity_verification_events(
  tenant_id,
  event_type,
  occurred_at
 );
"""


class NovaIDUnitOfWork(
    BiometricSQLiteRepositoryMixin,
    AbstractContextManager["NovaIDUnitOfWork"],
):
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.connection = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.identities = self
        self.authentication_locks = self
        self.sessions = self
        self.authorization = AuthorizationRepository(self.connection)

    def __enter__(self) -> "NovaIDUnitOfWork":
        self.connection.execute("BEGIN IMMEDIATE")
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        if self.connection.in_transaction:
            self.connection.execute("ROLLBACK" if exc_type else "COMMIT")
        return False

    @property
    def in_transaction(self) -> bool:
        return self.connection.in_transaction

    def create_tenant(self, tenant_id: str, name: str, now: datetime) -> None:
        self.connection.execute(
            "INSERT INTO novaid_tenants"
            "(tenant_id,name,status,created_at,updated_at,version) VALUES(?,?,?,?,?,1)",
            (tenant_id, name, "ACTIVE", now.isoformat(), now.isoformat()),
        )

    def lock_idempotency_key(self, tenant_id: str, key: str) -> None:
        # BEGIN IMMEDIATE already serializes the local test adapter's writers.
        del tenant_id, key

    def bump_identity_security_version(self, tenant_id: str, identity_id: str) -> None:
        result = self.connection.execute(
            "UPDATE novaid_identities SET security_version=security_version+1,version=version+1 "
            "WHERE identity_id=? AND tenant_id=?",
            (identity_id, tenant_id),
        )
        if result.rowcount != 1:
            raise RuntimeError("CONCURRENCY_CONFLICT")

    def get(self, tenant_id: str, identifier_hash: str):
        return self.connection.execute(
            "SELECT * FROM novaid_authentication_locks WHERE tenant_id=? AND identifier_hash=?",
            (tenant_id, identifier_hash),
        ).fetchone()

    def upsert(
        self,
        tenant_id: str,
        identifier_hash: str,
        failure_count: int,
        window_started_at: str,
        locked_until: str | None,
        updated_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO novaid_authentication_locks VALUES(?,?,?,?,?,?)",
            (tenant_id, identifier_hash, failure_count, window_started_at, locked_until, updated_at),
        )

    def list_password_credentials(self, tenant_id: str, identity_id: str) -> list[sqlite3.Row]:
        return list(
            self.connection.execute(
                "SELECT c.credential_id,c.status,p.password_hash,c.created_at "
                "FROM novaid_credentials c JOIN novaid_password_credentials p "
                "ON p.credential_id=c.credential_id "
                "WHERE c.tenant_id=? AND c.identity_id=? AND c.kind='PASSWORD' "
                "ORDER BY c.created_at DESC",
                (tenant_id, identity_id),
            ).fetchall()
        )

    def supersede_active_password_credentials(self, tenant_id: str, identity_id: str, *, now: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_credentials SET status='SUPERSEDED',updated_at=?,version=version+1 "
            "WHERE tenant_id=? AND identity_id=? AND kind='PASSWORD' AND status='ACTIVE'",
            (now, tenant_id, identity_id),
        )
        return result.rowcount

    def insert_password_credential(
        self,
        credential_id: str,
        tenant_id: str,
        identity_id: str,
        password_hash: str,
        algorithm_version: str,
        *,
        now: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_credentials VALUES(?,?,?,?,?,?,?,?)",
            (credential_id, tenant_id, identity_id, "PASSWORD", "ACTIVE", now, now, 1),
        )
        self.connection.execute(
            "INSERT INTO novaid_password_credentials VALUES(?,?,?,?,?)",
            (credential_id, password_hash, algorithm_version, None, None),
        )

    def create_otp_challenge(
        self,
        challenge_id: str,
        tenant_id: str,
        identity_id: str,
        purpose: str,
        destination_reference: str,
        secret_hash: str,
        created_at: str,
        expires_at: str,
        maximum_attempts: int,
        status: str,
        correlation_id: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_otp_challenges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                challenge_id,
                tenant_id,
                identity_id,
                purpose,
                destination_reference,
                secret_hash,
                created_at,
                expires_at,
                None,
                0,
                maximum_attempts,
                status,
                correlation_id,
            ),
        )

    def get_otp_challenge(self, tenant_id: str, challenge_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM novaid_otp_challenges WHERE tenant_id=? AND challenge_id=?",
            (tenant_id, challenge_id),
        ).fetchone()

    def increment_otp_challenge_attempt(self, challenge_id: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_otp_challenges SET attempt_count=attempt_count+1 WHERE challenge_id=?",
            (challenge_id,),
        )
        return result.rowcount

    def consume_otp_challenge(self, challenge_id: str, *, now: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_otp_challenges SET status='CONSUMED',consumed_at=? "
            "WHERE challenge_id=? AND status='PENDING'",
            (now, challenge_id),
        )
        return result.rowcount

    def get_recovery_authorization_context(
        self, tenant_id: str, identity_id: str, session_id: str
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT s.status,s.authentication_strength,s.step_up_expires_at,m.status membership_status "
            "FROM novaid_authentication_sessions s JOIN novaid_tenant_memberships m "
            "ON m.membership_id=s.membership_id AND m.tenant_id=s.tenant_id "
            "WHERE s.tenant_id=? AND s.identity_id=? AND s.session_id=?",
            (tenant_id, identity_id, session_id),
        ).fetchone()

    def get_recovery_policy(self, tenant_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM novaid_tenant_webauthn_policies WHERE tenant_id=?",
            (tenant_id,),
        ).fetchone()

    def replace_tenant_webauthn_policy(
        self,
        tenant_id: str,
        policy: dict[str, object],
        *,
        updated_by: str,
        reason: str,
        version: int,
        updated_at: str,
    ) -> None:
        self.connection.execute(
            "DELETE FROM novaid_tenant_webauthn_policies WHERE tenant_id=?",
            (tenant_id,),
        )
        self.connection.execute(
            "INSERT INTO novaid_tenant_webauthn_policies(tenant_id,require_webauthn,"
            "passkeys_enabled,passwordless_enabled,require_phishing_resistant_step_up,"
            "user_verification,attestation,maximum_credentials,recovery_codes_enabled,"
            "recovery_code_count,recovery_code_expiry_days,recovery_approval_count,"
            "recovery_requires_new_authenticator,step_up_seconds,updated_at,updated_by,version) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                tenant_id,
                bool(policy["enabled"]),
                bool(policy["passkeys_enabled"]),
                bool(policy["passwordless_enabled"]),
                bool(policy["phishing_resistant_step_up_required"]),
                policy["user_verification"],
                policy["attestation"],
                int(policy["maximum_credentials"]),
                bool(policy["recovery_codes_enabled"]),
                int(policy["recovery_code_count"]),
                int(policy["recovery_code_expiry_days"]),
                int(policy["recovery_approval_count"]),
                bool(policy["recovery_requires_new_authenticator"]),
                int(policy["step_up_seconds"]),
                updated_at,
                updated_by,
                version,
            ),
        )
        self.connection.execute(
            "UPDATE novaid_tenant_webauthn_policy_history SET status='SUPERSEDED' "
            "WHERE tenant_id=? AND status='ACTIVE'",
            (tenant_id,),
        )
        self.connection.execute(
            "INSERT INTO novaid_tenant_webauthn_policy_history(policy_history_id,tenant_id,"
            "policy_version,status,policy,reason,created_at,created_by) VALUES(?,?,?,?,?,?,?,?)",
            (
                str(uuid4()),
                tenant_id,
                version,
                "ACTIVE",
                json.dumps(policy, sort_keys=True, separators=(",", ":")),
                reason,
                updated_at,
                updated_by,
            ),
        )

    def get_actor_recovery_context(
        self, tenant_id: str, actor_identity_id: str, session_id: str
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT m.role,s.authentication_strength,s.step_up_expires_at FROM novaid_tenant_memberships m "
            "JOIN novaid_authentication_sessions s ON s.membership_id=m.membership_id "
            "WHERE m.tenant_id=? AND m.identity_id=? AND m.status='ACTIVE' AND s.session_id=? AND s.status='ACTIVE'",
            (tenant_id, actor_identity_id, session_id),
        ).fetchone()

    def get_active_identity_by_email(self, tenant_id: str, normalized_email: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT identity_id FROM novaid_identities WHERE tenant_id=? AND normalized_email=? AND status='ACTIVE'",
            (tenant_id, normalized_email),
        ).fetchone()

    def get_recent_recovery_request(
        self, tenant_id: str, identity_id: str, *, since: str
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT recovery_request_id FROM novaid_account_recovery_requests WHERE tenant_id=? "
            "AND identity_id=? AND requested_at>? AND status NOT IN "
            "('REJECTED','COMPLETED','CANCELLED','EXPIRED')",
            (tenant_id, identity_id, since),
        ).fetchone()

    def insert_recovery_request(
        self,
        recovery_request_id: str,
        tenant_id: str,
        identity_id: str,
        *,
        status: str,
        recovery_method: str,
        requested_at: str,
        expires_at: str,
        reason: str,
        correlation_id: str,
        request_id: str,
        device_reference: str | None,
        network_reference: str | None,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_account_recovery_requests(recovery_request_id,tenant_id,identity_id,"
            "status,recovery_method,requested_at,expires_at,approved_at,approved_by,completed_at,"
            "rejected_at,cancelled_at,reason,correlation_id,request_id,device_reference,"
            "network_reference,version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                recovery_request_id,
                tenant_id,
                identity_id,
                status,
                recovery_method,
                requested_at,
                expires_at,
                None,
                None,
                None,
                None,
                None,
                reason,
                correlation_id,
                request_id,
                device_reference,
                network_reference,
                1,
            ),
        )

    def get_recovery_request(
        self, tenant_id: str, recovery_request_id: str
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM novaid_account_recovery_requests WHERE tenant_id=? AND recovery_request_id=?",
            (tenant_id, recovery_request_id),
        ).fetchone()

    def mark_recovery_verified(self, recovery_request_id: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET status='VERIFIED',version=version+1 "
            "WHERE recovery_request_id=? AND status='REQUESTED'",
            (recovery_request_id,),
        )
        return result.rowcount

    def insert_recovery_evidence(
        self,
        evidence_id: str,
        recovery_request_id: str,
        tenant_id: str,
        identity_id: str,
        *,
        method: str,
        correlation_id: str,
        request_id: str,
        created_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_account_recovery_evidence(evidence_id,recovery_request_id,"
            "tenant_id,identity_id,method,result,risk_indicators,actor_identity_id,"
            "correlation_id,request_id,created_at) VALUES(?,?,?,?,?,'VERIFIED','[]',NULL,?,?,?)",
            (
                evidence_id,
                recovery_request_id,
                tenant_id,
                identity_id,
                method,
                correlation_id,
                request_id,
                created_at,
            ),
        )

    def get_membership_role_status(self, tenant_id: str, identity_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT role,status FROM novaid_tenant_memberships WHERE tenant_id=? AND identity_id=?",
            (tenant_id, identity_id),
        ).fetchone()

    def insert_recovery_approval(
        self,
        approval_id: str,
        recovery_request_id: str,
        tenant_id: str,
        approver_identity_id: str,
        *,
        decision: str,
        reason: str,
        created_at: str,
        expires_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_account_recovery_approvals(approval_id,recovery_request_id,"
            "tenant_id,approver_identity_id,decision,reason,created_at,expires_at) "
            "VALUES(?,?,?,?,'APPROVED',?,?,?)",
            (
                approval_id,
                recovery_request_id,
                tenant_id,
                approver_identity_id,
                reason,
                created_at,
                expires_at,
            ),
        )

    def bump_recovery_request_version(self, recovery_request_id: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET version=version+1 "
            "WHERE recovery_request_id=?",
            (recovery_request_id,),
        )
        return result.rowcount

    def count_active_recovery_approvals(
        self, tenant_id: str, recovery_request_id: str, *, now: str
    ) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) FROM novaid_account_recovery_approvals WHERE tenant_id=? "
            "AND recovery_request_id=? AND decision='APPROVED' AND expires_at>?",
            (tenant_id, recovery_request_id, now),
        ).fetchone()
        return int(row[0] if row else 0)

    def mark_recovery_approved(
        self, recovery_request_id: str, *, approved_at: str, approved_by: str
    ) -> int:
        result = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET status='APPROVED',approved_at=?,"
            "approved_by=?,version=version+1 WHERE recovery_request_id=? AND status='VERIFIED'",
            (approved_at, approved_by, recovery_request_id),
        )
        return result.rowcount

    def mark_recovery_rejected(
        self, tenant_id: str, recovery_request_id: str, *, rejected_at: str, reason: str
    ) -> int:
        result = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET status='REJECTED',rejected_at=?,"
            "reason=?,version=version+1 WHERE tenant_id=? AND recovery_request_id=? "
            "AND status IN ('REQUESTED','VERIFIED')",
            (rejected_at, reason, tenant_id, recovery_request_id),
        )
        return result.rowcount

    def mark_recovery_cancelled(
        self, tenant_id: str, identity_id: str, recovery_request_id: str, *, cancelled_at: str
    ) -> int:
        result = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET status='CANCELLED',cancelled_at=?,"
            "version=version+1 WHERE tenant_id=? AND identity_id=? AND recovery_request_id=? "
            "AND status IN ('REQUESTED','VERIFIED')",
            (cancelled_at, tenant_id, identity_id, recovery_request_id),
        )
        return result.rowcount

    def expire_recovery_requests(self, tenant_id: str, *, now: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET status='EXPIRED',version=version+1 "
            "WHERE tenant_id=? AND expires_at<=? AND status IN ('REQUESTED','VERIFIED','APPROVED')",
            (tenant_id, now),
        )
        return result.rowcount

    def mark_recovery_completed(self, tenant_id: str, recovery_request_id: str, *, completed_at: str) -> sqlite3.Row | None:
        row = self.connection.execute(
            "SELECT identity_id,status,expires_at FROM novaid_account_recovery_requests "
            "WHERE tenant_id=? AND recovery_request_id=?",
            (tenant_id, recovery_request_id),
        ).fetchone()
        if not row:
            return None
        changed = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET status='COMPLETED',completed_at=?,version=version+1 "
            "WHERE recovery_request_id=? AND status='APPROVED'",
            (completed_at, recovery_request_id),
        )
        if changed.rowcount != 1:
            return None
        return row

    def supersede_recovery_codes(self, tenant_id: str, identity_id: str, *, now: str) -> None:
        self.connection.execute(
            "UPDATE novaid_recovery_code_batches SET status='SUPERSEDED',revoked_at=?,"
            "version=version+1 WHERE tenant_id=? AND identity_id=? AND status='ACTIVE'",
            (now, tenant_id, identity_id),
        )
        self.connection.execute(
            "UPDATE novaid_recovery_codes SET status='SUPERSEDED',revoked_at=?,"
            "version=version+1 WHERE tenant_id=? AND identity_id=? AND status='ACTIVE'",
            (now, tenant_id, identity_id),
        )

    def insert_recovery_code_batch(
        self,
        batch_id: str,
        tenant_id: str,
        identity_id: str,
        *,
        created_at: str,
        expires_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_recovery_code_batches(batch_id,tenant_id,identity_id,status,"
            "created_at,expires_at,revoked_at,version) VALUES(?,?,?,?,?,?,?,1)",
            (batch_id, tenant_id, identity_id, "ACTIVE", created_at, expires_at, None),
        )

    def insert_recovery_code(
        self,
        recovery_code_id: str,
        batch_id: str,
        tenant_id: str,
        identity_id: str,
        code_hash: str,
        *,
        created_at: str,
        expires_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_recovery_codes(recovery_code_id,batch_id,tenant_id,identity_id,code_hash,"
            "status,created_at,expires_at,used_at,revoked_at,attempt_count,version) "
            "VALUES(?,?,?,?,?,'ACTIVE',?,?,NULL,NULL,0,1)",
            (recovery_code_id, batch_id, tenant_id, identity_id, code_hash, created_at, expires_at),
        )

    def get_recovery_code_by_hash(
        self, tenant_id: str, identity_id: str, code_hash: str
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT recovery_code_id,status,expires_at FROM novaid_recovery_codes "
            "WHERE tenant_id=? AND identity_id=? AND code_hash=?",
            (tenant_id, identity_id, code_hash),
        ).fetchone()

    def consume_recovery_code(self, recovery_code_id: str, *, now: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_recovery_codes SET status='USED',used_at=?,version=version+1 "
            "WHERE recovery_code_id=? AND status='ACTIVE'",
            (now, recovery_code_id),
        )
        return result.rowcount

    def revoke_recovery_codes(self, tenant_id: str, identity_id: str, *, now: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_recovery_codes SET status='REVOKED',revoked_at=?,version=version+1 "
            "WHERE tenant_id=? AND identity_id=? AND status='ACTIVE'",
            (now, tenant_id, identity_id),
        )
        return result.rowcount

    def revoke_recovery_code_batches(self, tenant_id: str, identity_id: str, *, now: str) -> None:
        self.connection.execute(
            "UPDATE novaid_recovery_code_batches SET status='REVOKED',revoked_at=?,version=version+1 "
            "WHERE tenant_id=? AND identity_id=? AND status='ACTIVE'",
            (now, tenant_id, identity_id),
        )

    def count_active_recovery_codes(self, tenant_id: str, identity_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) FROM novaid_recovery_codes WHERE tenant_id=? AND identity_id=? "
            "AND status='ACTIVE' AND expires_at>?",
            (tenant_id, identity_id, now),
        ).fetchone()
        return int(row[0] if row is not None else 0)

    def delete(self, tenant_id: str, identifier_hash: str) -> None:
        self.connection.execute(
            "DELETE FROM novaid_authentication_locks WHERE tenant_id=? AND identifier_hash=?",
            (tenant_id, identifier_hash),
        )

    def _session_rows(self, query: str, parameters: tuple[Any, ...]) -> list[sqlite3.Row]:
        return list(self.connection.execute(query, parameters).fetchall())

    def list_sessions_for_identity(self, tenant_id: str, identity_id: str) -> list[sqlite3.Row]:
        return self._session_rows(
            "SELECT session_id,status,authentication_strength,created_at,last_seen_at,expires_at,"
            "authenticated_at,idle_expires_at,absolute_expires_at,pending_mfa_expires_at,"
            "step_up_expires_at,device_reference "
            "FROM novaid_authentication_sessions WHERE tenant_id=? AND identity_id=? "
            "ORDER BY created_at DESC",
            (tenant_id, identity_id),
        )

    def list_for_identity(self, tenant_id: str, identity_id: str) -> list[sqlite3.Row]:
        return [dict(row) for row in self.list_sessions_for_identity(tenant_id, identity_id)]

    def get_session_for_identity(
        self, tenant_id: str, identity_id: str, session_id: str
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT expires_at,status FROM novaid_authentication_sessions "
            "WHERE tenant_id=? AND identity_id=? AND session_id=?",
            (tenant_id, identity_id, session_id),
        ).fetchone()

    def get_active_strength(self, tenant_id: str, identity_id: str, session_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT authentication_strength FROM novaid_authentication_sessions "
            "WHERE tenant_id=? AND identity_id=? AND session_id=? AND status='ACTIVE'",
            (tenant_id, identity_id, session_id),
        ).fetchone()

    def get_for_identity(self, tenant_id: str, identity_id: str, session_id: str) -> sqlite3.Row | None:
        return self.get_session_for_identity(tenant_id, identity_id, session_id)

    def revoke_session(self, tenant_id: str, identity_id: str, session_id: str, reason: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='REVOKED',"
            "revoked_at=?,revocation_reason=? "
            "WHERE tenant_id=? AND identity_id=? AND session_id=?",
            (datetime.utcnow().isoformat(), reason, tenant_id, identity_id, session_id),
        )
        return result.rowcount

    def revoke(self, tenant_id: str, identity_id: str, session_id: str, reason: str) -> int:
        return self.revoke_session(tenant_id, identity_id, session_id, reason)

    def revoke_sessions_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> list[sqlite3.Row]:
        rows = self._session_rows(
            "SELECT session_id,expires_at FROM novaid_authentication_sessions "
            "WHERE tenant_id=? AND identity_id=? AND status NOT IN ('REVOKED','EXPIRED')",
            (tenant_id, identity_id),
        )
        self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='REVOKED',revoked_at=?,"
            "revocation_reason=? WHERE tenant_id=? AND identity_id=? "
            "AND status NOT IN ('REVOKED','EXPIRED')",
            (datetime.utcnow().isoformat(), reason, tenant_id, identity_id),
        )
        return rows

    def revoke_all_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> list[sqlite3.Row]:
        return self.revoke_sessions_for_identity(tenant_id, identity_id, reason)

    def update_session_touch(
        self, tenant_id: str, identity_id: str, session_id: str, *, now: str
    ) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET last_seen_at=?,idle_expires_at=? "
            "WHERE tenant_id=? AND identity_id=? AND session_id=? AND status='ACTIVE'",
            (now, (datetime.fromisoformat(now) + timedelta(minutes=30)).isoformat(), tenant_id, identity_id, session_id),
        )
        return result.rowcount

    def touch(self, tenant_id: str, identity_id: str, session_id: str, *, now: str) -> int:
        return self.update_session_touch(tenant_id, identity_id, session_id, now=now)

    def update_session_step_up(
        self, tenant_id: str, identity_id: str, session_id: str, *, until: str
    ) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='STEP_UP_REQUIRED',"
            "step_up_expires_at=? WHERE tenant_id=? AND identity_id=? AND session_id=? "
            "AND status='ACTIVE'",
            (until, tenant_id, identity_id, session_id),
        )
        return result.rowcount

    def require_step_up(
        self, tenant_id: str, identity_id: str, session_id: str, *, until: str
    ) -> int:
        return self.update_session_step_up(tenant_id, identity_id, session_id, until=until)

    def complete_session_step_up(self, tenant_id: str, identity_id: str, session_id: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='ACTIVE',step_up_expires_at=NULL,"
            "authentication_strength='PASSWORD_OTP' WHERE tenant_id=? AND identity_id=? "
            "AND session_id=? AND status='STEP_UP_REQUIRED'",
            (tenant_id, identity_id, session_id),
        )
        return result.rowcount

    def complete_step_up(self, tenant_id: str, identity_id: str, session_id: str) -> int:
        return self.complete_session_step_up(tenant_id, identity_id, session_id)

    def lock_session(self, tenant_id: str, identity_id: str, session_id: str, *, locked_at: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='LOCKED',locked_at=? "
            "WHERE tenant_id=? AND identity_id=? AND session_id=? "
            "AND status IN ('ACTIVE','STEP_UP_REQUIRED')",
            (locked_at, tenant_id, identity_id, session_id),
        )
        return result.rowcount

    def unlock_session(self, tenant_id: str, identity_id: str, session_id: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='ACTIVE',locked_at=NULL "
            "WHERE tenant_id=? AND identity_id=? AND session_id=? AND status='LOCKED'",
            (tenant_id, identity_id, session_id),
        )
        return result.rowcount

    def lock(self, tenant_id: str, identity_id: str, session_id: str, *, locked_at: str) -> int:
        return self.lock_session(tenant_id, identity_id, session_id, locked_at=locked_at)

    def unlock(self, tenant_id: str, identity_id: str, session_id: str) -> int:
        return self.unlock_session(tenant_id, identity_id, session_id)

    def expire_sessions(self, tenant_id: str, *, now: str) -> int:
        expired = 0
        rules = (
            ("PENDING_MFA", "pending_mfa_expires_at", "PENDING_MFA_EXPIRY"),
            ("ACTIVE", "idle_expires_at", "IDLE_EXPIRY"),
            ("STEP_UP_REQUIRED", "step_up_expires_at", "STEP_UP_EXPIRY"),
        )
        for status, column, reason in rules:
            result = self.connection.execute(
                f"UPDATE novaid_authentication_sessions SET status='EXPIRED',expired_at=?,"
                "revoked_at=?,revocation_reason=? WHERE tenant_id=? AND status=? "
                f"AND {column} IS NOT NULL AND {column}<=?",
                (now, now, reason, tenant_id, status, now),
            )
            expired += result.rowcount
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='EXPIRED',expired_at=?,"
            "revoked_at=?,revocation_reason='ABSOLUTE_EXPIRY' WHERE tenant_id=? "
            "AND status IN ('ACTIVE','PENDING_MFA','STEP_UP_REQUIRED','LOCKED') "
            "AND COALESCE(absolute_expires_at,expires_at)<=?",
            (now, now, tenant_id, now),
        )
        expired += result.rowcount
        return expired

    def expire_stale(self, tenant_id: str, *, now: str) -> int:
        return self.expire_sessions(tenant_id, now=now)

    def mark_session_compromised(
        self, tenant_id: str, identity_id: str, session_id: str, *, now: str
    ) -> sqlite3.Row | None:
        row = self.connection.execute(
            "SELECT expires_at FROM novaid_authentication_sessions "
            "WHERE tenant_id=? AND identity_id=? AND session_id=?",
            (tenant_id, identity_id, session_id),
        ).fetchone()
        if not row:
            return None
        self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='COMPROMISED',"
            "revoked_at=?,compromised_at=?,revocation_reason='SECURITY_CONTAINMENT',"
            "compromise_reason='SECURITY_CONTAINMENT' WHERE tenant_id=? AND identity_id=? "
            "AND session_id=? AND status NOT IN ('COMPROMISED','REVOKED','EXPIRED')",
            (now, now, tenant_id, identity_id, session_id),
        )
        self.connection.execute(
            "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=? "
            "WHERE tenant_id=? AND session_id=? AND status='ACTIVE'",
            (now, tenant_id, session_id),
        )
        return row

    def mark_compromised(
        self, tenant_id: str, identity_id: str, session_id: str, *, now: str
    ) -> sqlite3.Row | None:
        return self.mark_session_compromised(tenant_id, identity_id, session_id, now=now)

    def revoke_refresh_families_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> int:
        del reason
        result = self.connection.execute(
            "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=? "
            "WHERE tenant_id=? AND identity_id=? AND status='ACTIVE'",
            (datetime.utcnow().isoformat(), tenant_id, identity_id),
        )
        return result.rowcount

    def revoke_webauthn_credentials_for_identity(self, tenant_id: str, identity_id: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_webauthn_credentials SET status='SUSPENDED',version=version+1 "
            "WHERE tenant_id=? AND identity_id=? AND status='ACTIVE'",
            (tenant_id, identity_id),
        )
        return result.rowcount

    def list_active_webauthn_credentials(
        self, tenant_id: str, identity_id: str
    ) -> list[sqlite3.Row]:
        return list(
            self.connection.execute(
                "SELECT credential_id,transports FROM novaid_webauthn_credentials "
                "WHERE tenant_id=? AND identity_id=? AND status IN ('ACTIVE','SUSPENDED')",
                (tenant_id, identity_id),
            ).fetchall()
        )

    def get_webauthn_credential(self, tenant_id: str, credential_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM novaid_webauthn_credentials WHERE tenant_id=? AND credential_id=?",
            (tenant_id, credential_id),
        ).fetchone()

    def get_passwordless_session_context(
        self, tenant_id: str, identity_id: str
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT m.membership_id,i.status,i.security_version FROM novaid_tenant_memberships m "
            "JOIN novaid_identities i ON i.identity_id=m.identity_id AND i.tenant_id=m.tenant_id "
            "WHERE m.tenant_id=? AND m.identity_id=? AND m.status='ACTIVE' AND i.status='ACTIVE'",
            (tenant_id, identity_id),
        ).fetchone()

    def get_webauthn_session(
        self, tenant_id: str, session_id: str
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT identity_id,status FROM novaid_authentication_sessions "
            "WHERE tenant_id=? AND session_id=?",
            (tenant_id, session_id),
        ).fetchone()

    def insert_webauthn_challenge(
        self,
        table: str,
        *,
        challenge_id: str,
        tenant_id: str,
        identity_id: str | None,
        session_id: str | None,
        purpose: str,
        challenge_hash: str,
        rp_id: str,
        origin: str,
        created_at: str,
        expires_at: str,
        correlation_id: str,
        request_id: str,
        maximum_attempts: int,
    ) -> None:
        columns = "challenge_id,tenant_id,identity_id,"
        values: tuple[object, ...]
        if table == "novaid_webauthn_authentication_challenges":
            columns += "session_id,"
            values = (challenge_id, tenant_id, identity_id, session_id)
            placeholders = "?,?,?,?"
        else:
            values = (challenge_id, tenant_id, identity_id)
            placeholders = "?,?,?"
        columns += (
            "purpose,challenge_hash,rp_id,origin,created_at,expires_at,consumed_at,status,"
            "attempt_count,maximum_attempts,correlation_id,request_id"
        )
        values += (
            purpose,
            challenge_hash,
            rp_id,
            origin,
            created_at,
            expires_at,
            None,
            "PENDING",
            0,
            maximum_attempts,
            correlation_id,
            request_id,
        )
        self.connection.execute(
            f"INSERT INTO {table}({columns}) VALUES({placeholders},?,?,?,?,?,?,?,?,?,?,?,?)",
            values,
        )

    def get_webauthn_challenge(
        self, table: str, challenge_id: str, tenant_id: str
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            f"SELECT * FROM {table} WHERE challenge_id=? AND tenant_id=?",
            (challenge_id, tenant_id),
        ).fetchone()

    def consume_webauthn_challenge(
        self, table: str, challenge_id: str, tenant_id: str, *, now: str
    ) -> int:
        result = self.connection.execute(
            f"UPDATE {table} SET status='CONSUMED',consumed_at=? "
            "WHERE challenge_id=? AND tenant_id=? AND status='PENDING'",
            (now, challenge_id, tenant_id),
        )
        return result.rowcount

    def insert_webauthn_authenticator(
        self,
        authenticator_id: str,
        tenant_id: str,
        aaguid: str,
        friendly_name: str | None,
        *,
        status: str,
        created_at: str,
        updated_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_authenticators VALUES(?,?,?,?,?,?,?,1)",
            (
                authenticator_id,
                tenant_id,
                aaguid,
                friendly_name,
                status,
                created_at,
                updated_at,
            ),
        )

    def insert_webauthn_credential(
        self,
        *,
        credential_id: str,
        tenant_id: str,
        identity_id: str,
        membership_id: str,
        authenticator_id: str,
        user_handle: bytes,
        public_key_cose: bytes,
        public_key_algorithm: int,
        sign_count: int,
        aaguid: str,
        attestation_format: str,
        attestation_type: str,
        transports: str,
        backup_eligible: bool,
        backup_state: bool,
        discoverable: bool,
        resident_key: bool,
        user_verification: bool,
        created_at: str,
        status: str,
        version: int,
        friendly_name: str | None,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_webauthn_credentials(credential_id,tenant_id,identity_id,"
            "membership_id,authenticator_id,user_handle,public_key_cose,public_key_algorithm,"
            "sign_count,aaguid,attestation_format,attestation_type,transports,backup_eligible,"
            "backup_state,discoverable,resident_key,user_verification,created_at,status,version,"
            "friendly_name) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                credential_id,
                tenant_id,
                identity_id,
                membership_id,
                authenticator_id,
                user_handle,
                public_key_cose,
                public_key_algorithm,
                sign_count,
                aaguid,
                attestation_format,
                attestation_type,
                transports,
                backup_eligible,
                backup_state,
                discoverable,
                resident_key,
                user_verification,
                created_at,
                status,
                version,
                friendly_name,
            ),
        )

    def mark_webauthn_credential_compromised(self, tenant_id: str, credential_id: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_webauthn_credentials SET status='COMPROMISED',version=version+1 "
            "WHERE tenant_id=? AND credential_id=? AND status='ACTIVE'",
            (tenant_id, credential_id),
        )
        return result.rowcount

    def update_webauthn_credential_sign_count(
        self,
        tenant_id: str,
        credential_id: str,
        *,
        new_sign_count: int,
        last_used_at: str,
        last_verified_at: str,
        backup_state: bool,
        expected_sign_count: int,
    ) -> int:
        result = self.connection.execute(
            "UPDATE novaid_webauthn_credentials SET sign_count=?,last_used_at=?,"
            "last_verified_at=?,backup_state=?,version=version+1 WHERE tenant_id=? "
            "AND credential_id=? AND status='ACTIVE' AND sign_count=?",
            (
                new_sign_count,
                last_used_at,
                last_verified_at,
                backup_state,
                tenant_id,
                credential_id,
                expected_sign_count,
            ),
        )
        return result.rowcount

    def update_webauthn_credential_status(
        self,
        tenant_id: str,
        identity_id: str,
        credential_id: str,
        *,
        target: str,
    ) -> int:
        result = self.connection.execute(
            "UPDATE novaid_webauthn_credentials SET status=?,version=version+1 "
            "WHERE tenant_id=? AND identity_id=? AND credential_id=?",
            (target, tenant_id, identity_id, credential_id),
        )
        return result.rowcount

    def complete_webauthn_step_up(self, tenant_id: str, session_id: str, *, now: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='ACTIVE',"
            "authentication_strength='PHISHING_RESISTANT',authenticated_at=?,"
            "step_up_expires_at=?,authentication_methods='[\"WEBAUTHN\"]' "
            "WHERE tenant_id=? AND session_id=? AND status='STEP_UP_REQUIRED'",
            (now, (datetime.fromisoformat(now) + timedelta(minutes=5)).isoformat(), tenant_id, session_id),
        )
        return result.rowcount

    def insert_webauthn_status_history(
        self,
        history_id: str,
        tenant_id: str,
        credential_id: str,
        previous_status: str,
        target_status: str,
        reason: str,
        created_at: str,
        actor_identity_id: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_authenticator_status_history VALUES(?,?,?,?,?,?,?,?)",
            (
                history_id,
                tenant_id,
                credential_id,
                previous_status,
                target_status,
                reason,
                created_at,
                actor_identity_id,
            ),
        )

    def add_identity(self, identity: Identity) -> None:
        self.connection.execute(
            "INSERT INTO novaid_identities("
            "identity_id,tenant_id,normalized_email,status,created_at,"
            "updated_at,version,security_version,identity_type,legal_name,"
            "preferred_name,alternative_names,contact_points,addresses,"
            "identifiers,verification_status,assurance_level,metadata"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                identity.identity_id,
                identity.tenant_id,
                identity.normalized_email.lower(),
                identity.status.value,
                identity.created_at.isoformat(),
                identity.updated_at.isoformat(),
                identity.version,
                1,
                identity.identity_type.value,
                encode_legal_name(identity.legal_name),
                identity.preferred_name,
                encode_identity_names(identity.alternative_names),
                encode_contact_points(identity.contact_points),
                encode_addresses(identity.addresses),
                encode_identifiers(identity.identifiers),
                identity.verification_status.value,
                identity.assurance_level.value,
                encode_metadata(identity.metadata),
            ),
        )

    def get_by_email(self, tenant_id: str, normalized_email: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT identity_id FROM novaid_identities "
            "WHERE tenant_id=? AND normalized_email=? AND status='ACTIVE'",
            (tenant_id, normalized_email.lower()),
        ).fetchone()

    def get_tenant_status(self, tenant_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT status FROM novaid_tenants WHERE tenant_id=?",
            (tenant_id,),
        ).fetchone()

    def get_idempotency_record(self, tenant_id: str, key: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT payload_hash,response_json FROM novaid_idempotency_records "
            "WHERE tenant_id=? AND idempotency_key=?",
            (tenant_id, key),
        ).fetchone()

    def insert_idempotency_record(
        self, tenant_id: str, key: str, payload_hash: str, response_json: str, *, now: str
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_idempotency_records VALUES(?,?,?,?,?)",
            (tenant_id, key, payload_hash, response_json, now),
        )

    def create_registration_membership(
        self, membership_id: str, tenant_id: str, identity_id: str, *, now: str
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_tenant_memberships"
            "(membership_id,tenant_id,identity_id,role,status,created_at,updated_at,version) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (membership_id, tenant_id, identity_id, "MEMBER", "ACTIVE", now, now, 1),
        )

    def get_identity_for_tenant(self, tenant_id: str, identity_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM novaid_identities WHERE identity_id=? AND tenant_id=?",
            (identity_id, tenant_id),
        ).fetchone()

    def activate_identity(self, tenant_id: str, identity_id: str, *, now: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_identities SET status='ACTIVE',updated_at=?,version=version+1 "
            "WHERE identity_id=? AND tenant_id=?",
            (now, identity_id, tenant_id),
        )
        return result.rowcount

    def create_registration_challenge(
        self,
        challenge_id: str,
        tenant_id: str,
        identity_id: str,
        purpose: str,
        destination_reference: str,
        secret_hash: str,
        created_at: str,
        expires_at: str,
        maximum_attempts: int,
        correlation_id: str,
    ) -> None:
        self.create_otp_challenge(
            challenge_id,
            tenant_id,
            identity_id,
            purpose,
            destination_reference,
            secret_hash,
            created_at,
            expires_at,
            maximum_attempts,
            "PENDING",
            correlation_id,
        )

    def create_authentication_session(
        self,
        session_id: str,
        tenant_id: str,
        identity_id: str,
        authentication_time: str,
        authentication_strength: str,
        credential_id: str,
        risk_score: float,
        membership_id: str,
        *,
        created_at: str,
        expires_at: str,
        pending_mfa_expires_at: str,
        authentication_methods: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_authentication_sessions(session_id,tenant_id,identity_id,"
            "authentication_time,authentication_strength,credential_id,device_reference,"
            "client_reference,risk_score,status,created_at,last_seen_at,expires_at,revoked_at,"
            "revocation_reason,version,membership_id,authenticated_at,idle_expires_at,"
            "absolute_expires_at,pending_mfa_expires_at,step_up_expires_at,locked_at,expired_at,"
            "compromised_at,network_reference,authentication_methods,security_version,revoked_by,"
            "compromise_reason) VALUES(?,?,?,?,?,?,?,?,?,'PENDING_MFA',?,?,?,?,?,1,?,NULL,?,?,?,NULL,NULL,NULL,NULL,NULL,?,1,NULL,NULL)",
            (
                session_id,
                tenant_id,
                identity_id,
                authentication_time,
                authentication_strength,
                credential_id,
                None,
                None,
                risk_score,
                created_at,
                created_at,
                expires_at,
                None,
                None,
                membership_id,
                created_at,
                expires_at,
                pending_mfa_expires_at,
                authentication_methods,
            ),
        )

    def create_login_challenge(
        self,
        challenge_id: str,
        tenant_id: str,
        identity_id: str,
        session_id: str,
        secret_hash: str,
        created_at: str,
        expires_at: str,
        correlation_id: str,
    ) -> None:
        self.create_otp_challenge(
            challenge_id,
            tenant_id,
            identity_id,
            "LOGIN",
            session_id,
            secret_hash,
            created_at,
            expires_at,
            5,
            "PENDING",
            correlation_id,
        )

    def get_pending_session(self, tenant_id: str, session_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT identity_id,status,expires_at FROM novaid_authentication_sessions "
            "WHERE tenant_id=? AND session_id=?",
            (tenant_id, session_id),
        ).fetchone()

    def get_recent_login_challenge(
        self, tenant_id: str, identity_id: str, session_id: str
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT challenge_id,created_at FROM novaid_otp_challenges "
            "WHERE tenant_id=? AND identity_id=? AND purpose='LOGIN' "
            "AND destination_reference=? AND status='PENDING' "
            "ORDER BY created_at DESC LIMIT 1",
            (tenant_id, identity_id, session_id),
        ).fetchone()

    def get_login_identity(self, tenant_id: str, normalized_email: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT i.identity_id,i.status,m.membership_id,c.credential_id,p.password_hash "
            "FROM novaid_identities i JOIN novaid_tenant_memberships m ON m.identity_id=i.identity_id AND m.tenant_id=i.tenant_id "
            "JOIN novaid_credentials c ON c.identity_id=i.identity_id AND c.tenant_id=i.tenant_id "
            "JOIN novaid_password_credentials p ON p.credential_id=c.credential_id "
            "WHERE i.tenant_id=? AND i.normalized_email=? AND m.status='ACTIVE' AND c.status='ACTIVE'",
            (tenant_id, normalized_email.lower()),
        ).fetchone()

    def update_otp_status(self, challenge_id: str, status: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_otp_challenges SET status=? WHERE challenge_id=?",
            (status, challenge_id),
        )
        return result.rowcount

    def supersede_challenge(self, challenge_id: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_otp_challenges SET status='SUPERSEDED' WHERE challenge_id=?",
            (challenge_id,),
        )
        return result.rowcount

    def get_mfa_challenge_session(
        self, tenant_id: str, challenge_id: str, session_id: str
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT c.*,s.identity_id,s.status session_status FROM novaid_otp_challenges c "
            "JOIN novaid_authentication_sessions s ON CAST(s.session_id AS TEXT)=c.destination_reference "
            "WHERE c.challenge_id=? AND c.tenant_id=? AND s.session_id=?",
            (challenge_id, tenant_id, session_id),
        ).fetchone()

    def activate_session_and_refresh(
        self,
        session_id: str,
        *,
        now: str,
        authentication_methods: str,
        authentication_strength: str = "PASSWORD_OTP",
    ) -> int:
        idle_expires_at = (
            datetime.fromisoformat(now) + timedelta(minutes=30)
        ).isoformat()

        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='ACTIVE',"
            "authentication_strength=?,authenticated_at=?,"
            "last_seen_at=?,idle_expires_at=?,authentication_methods=?,"
            "pending_mfa_expires_at=NULL WHERE session_id=? "
            "AND status='PENDING_MFA'",
            (
                authentication_strength,
                now,
                now,
                idle_expires_at,
                authentication_methods,
                session_id,
            ),
        )
        return result.rowcount

    def create_refresh_family(
        self,
        family_id: str,
        session_id: str,
        identity_id: str,
        tenant_id: str,
        *,
        created_at: str,
        expires_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_refresh_token_families VALUES(?,?,?,?,?,?,?,?,?)",
            (family_id, session_id, identity_id, tenant_id, "ACTIVE", created_at, expires_at, None, 1),
        )

    def create_refresh_token(
        self,
        token_id: str,
        family_id: str,
        session_id: str,
        identity_id: str,
        tenant_id: str,
        token_hash: str,
        parent_token_id: str | None,
        *,
        issued_at: str,
        expires_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_refresh_tokens VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                token_id,
                family_id,
                session_id,
                identity_id,
                tenant_id,
                token_hash,
                parent_token_id,
                issued_at,
                expires_at,
                None,
                None,
                None,
                "ACTIVE",
            ),
        )

    def get_refresh_context(self, tenant_id: str, token_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT t.*,f.status family_status,s.status session_status,"
            "s.idle_expires_at,s.absolute_expires_at,s.expires_at session_expires_at "
            "FROM novaid_refresh_tokens t "
            "JOIN novaid_refresh_token_families f ON f.family_id=t.family_id "
            "JOIN novaid_authentication_sessions s ON s.session_id=t.session_id "
            "WHERE t.token_id=? AND t.tenant_id=?",
            (token_id, tenant_id),
        ).fetchone()

    def mark_refresh_replayed(self, token_id: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_refresh_tokens SET status='REPLAYED' WHERE token_id=?",
            (token_id,),
        )
        return result.rowcount

    def revoke_refresh_family(self, family_id: str, *, now: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=? WHERE family_id=?",
            (now, family_id),
        )
        return result.rowcount

    def revoke_refresh_session(self, session_id: str, *, now: str, reason: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='REVOKED',revoked_at=?,revocation_reason=? "
            "WHERE session_id=?",
            (now, reason, session_id),
        )
        return result.rowcount

    def expire_refresh_session(
        self, tenant_id: str, session_id: str, *, now: str, reason: str
    ) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='EXPIRED',expired_at=?,"
            "revoked_at=?,revocation_reason=? WHERE tenant_id=? AND session_id=? AND status='ACTIVE'",
            (now, now, reason, tenant_id, session_id),
        )
        return result.rowcount

    def mark_refresh_used(self, token_id: str, successor_id: str, *, now: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_refresh_tokens SET status='USED',used_at=?,replacement_token_id=? "
            "WHERE token_id=? AND status='ACTIVE'",
            (now, successor_id, token_id),
        )
        return result.rowcount

    def list_password_credentials(self, tenant_id: str, identity_id: str) -> list[sqlite3.Row]:
        return list(
            self.connection.execute(
                "SELECT c.credential_id,c.status,p.password_hash,c.created_at "
                "FROM novaid_credentials c JOIN novaid_password_credentials p "
                "ON p.credential_id=c.credential_id "
                "WHERE c.tenant_id=? AND c.identity_id=? AND c.kind='PASSWORD' "
                "ORDER BY c.created_at DESC",
                (tenant_id, identity_id),
            ).fetchall()
        )

    def supersede_active_password_credentials(self, tenant_id: str, identity_id: str, *, now: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_credentials SET status='SUPERSEDED',updated_at=?,version=version+1 "
            "WHERE tenant_id=? AND identity_id=? AND kind='PASSWORD' AND status='ACTIVE'",
            (now, tenant_id, identity_id),
        )
        return result.rowcount

    def insert_password_credential(
        self,
        credential_id: str,
        tenant_id: str,
        identity_id: str,
        password_hash: str,
        algorithm_version: str,
        *,
        now: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_credentials VALUES(?,?,?,?,?,?,?,?)",
            (credential_id, tenant_id, identity_id, "PASSWORD", "ACTIVE", now, now, 1),
        )
        self.connection.execute(
            "INSERT INTO novaid_password_credentials VALUES(?,?,?,?,?)",
            (credential_id, password_hash, algorithm_version, None, None),
        )

    def create_otp_challenge(
        self,
        challenge_id: str,
        tenant_id: str,
        identity_id: str,
        purpose: str,
        destination_reference: str,
        secret_hash: str,
        created_at: str,
        expires_at: str,
        maximum_attempts: int,
        status: str,
        correlation_id: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_otp_challenges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                challenge_id,
                tenant_id,
                identity_id,
                purpose,
                destination_reference,
                secret_hash,
                created_at,
                expires_at,
                None,
                0,
                maximum_attempts,
                status,
                correlation_id,
            ),
        )

    def get_otp_challenge(self, tenant_id: str, challenge_id: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM novaid_otp_challenges WHERE tenant_id=? AND challenge_id=?",
            (tenant_id, challenge_id),
        ).fetchone()

    def increment_otp_challenge_attempt(self, challenge_id: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_otp_challenges SET attempt_count=attempt_count+1 WHERE challenge_id=?",
            (challenge_id,),
        )
        return result.rowcount

    def consume_otp_challenge(self, challenge_id: str, *, now: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_otp_challenges SET status='CONSUMED',consumed_at=? "
            "WHERE challenge_id=? AND status='PENDING'",
            (now, challenge_id),
        )
        return result.rowcount

    def get_identity(self, context: RequestContext, identity_id: str) -> Identity:
        row = self.connection.execute(
            "SELECT * FROM novaid_identities WHERE identity_id=? AND tenant_id=?",
            (identity_id, context.tenant_id),
        ).fetchone()

        if row is None:
            raise LookupError("TENANT_ACCESS_DENIED")

        return identity_from_row(row)

    def update_identity(
        self, context: RequestContext, identity: Identity, expected_version: int
    ) -> None:
        result = self.connection.execute(
            "UPDATE novaid_identities SET status=?,updated_at=?,version=? WHERE identity_id=? AND tenant_id=? AND version=?",
            (
                identity.status,
                identity.updated_at.isoformat(),
                identity.version,
                identity.identity_id,
                context.tenant_id,
                expected_version,
            ),
        )
        if result.rowcount != 1:
            raise RuntimeError("CONCURRENCY_CONFLICT")

    def add_event(self, event: SecurityEvent) -> None:
        forbidden = {
            "password",
            "otp",
            "access_token",
            "refresh_token",
            "private_key",
            "recovery_secret",
        }
        if forbidden & {key.lower() for key in event.metadata}:
            raise ValueError("SECRET_IN_SECURITY_EVENT")
        self.connection.execute(
            "INSERT INTO novaid_security_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                event.event_id,
                event.event_type,
                event.severity,
                event.tenant_id,
                event.actor_identity_id,
                event.subject_identity_id,
                event.correlation_id,
                event.request_id,
                event.occurred_at.isoformat(),
                event.recorded_at.isoformat(),
                event.outcome,
                json.dumps(event.reason_codes),
                json.dumps(event.metadata),
                event.schema_version,
            ),
        )

    def record_security_event(self, event: SecurityEvent) -> None:
        self.add_event(event)

    def count(self, table: str) -> int:
        allowed = {
            row[0]
            for row in self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if table not in allowed:
            raise ValueError("invalid_table")
        return int(self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
