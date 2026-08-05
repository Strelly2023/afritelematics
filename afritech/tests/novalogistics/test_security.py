from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone

import pytest

from afritech.novalogistics import Identifier
from afritech.novalogistics.persistence import AggregateAlreadyExistsError, OptimisticConcurrencyError
from afritech.novalogistics.security import *
from afritech.novalogistics.security_sqlite import SQLiteAuthorizationAuditRepository, SQLiteMembershipRepository, SQLiteServiceIdentityRepository
from afritech.novalogistics.sqlite import MigrationRunner, connect

NOW=datetime(2026,8,6,tzinfo=timezone.utc); TENANT=Identifier("tenant-a"); OTHER=Identifier("tenant-b"); ACTOR=IdentityReference("novaid:admin")

def membership(status=MembershipStatus.ACTIVE,roles=frozenset({Role.CUSTOMER})):
    return TenantMembership(Identifier("m-1"),TENANT,IdentityReference("novaid:user-1"),status,roles,version=1,activated_at=NOW,audit_actor=ACTOR)
def human(role=Role.CUSTOMER,tenant=TENANT):
    perms=ROLE_PERMISSIONS[role]
    return HumanPrincipal(IdentityReference("novaid:user-1"),tenant,Identifier("m-1"),"session-ref",NOW,frozenset({role}),perms,"req","corr")
def request(permission=Permission.CUSTOMER_READ,tenant=TENANT,**kwargs): return AuthorizationRequest(permission,tenant,"customer",**kwargs)

def test_identity_reference_normalization_validation_and_serialization():
    assert IdentityReference("  novaid:user ").value=="novaid:user"
    assert IdentityReference("novaid:user").to_dict()["contract_version"]=="novaid.identity-reference.v1"
    with pytest.raises(SecurityError): IdentityReference("bad identity")

def test_principals_are_immutable_and_contain_no_token_field():
    principal=human()
    with pytest.raises(FrozenInstanceError): principal.request_id="x"
    assert "token" not in repr(principal).lower()
    assert AnonymousPrincipal("r","c").principal_id=="anonymous"

def test_all_roles_have_explicit_non_wildcard_permissions():
    assert set(ROLE_PERMISSIONS)==set(Role)
    assert all(permissions and all("*" not in p.value for p in permissions) for permissions in ROLE_PERMISSIONS.values())
    assert Permission.PLATFORM_MANAGE not in ROLE_PERMISSIONS[Role.TENANT_ADMINISTRATOR]
    assert all(p.value.endswith(".read") for p in ROLE_PERMISSIONS[Role.AUDITOR])

def test_membership_lifecycle_and_role_assignment_rules():
    invited=TenantMembership(Identifier("m"),TENANT,IdentityReference("novaid:u"),invited_at=NOW)
    active=invited.transition(MembershipStatus.ACTIVE,at=NOW,actor=ACTOR)
    suspended=active.transition(MembershipStatus.SUSPENDED,at=NOW,actor=ACTOR)
    assert suspended.transition(MembershipStatus.ACTIVE,at=NOW,actor=ACTOR).status is MembershipStatus.ACTIVE
    revoked=suspended.transition(MembershipStatus.REVOKED,at=NOW,actor=ACTOR)
    with pytest.raises(MembershipInactiveError): revoked.transition(MembershipStatus.ACTIVE,at=NOW,actor=ACTOR)
    with pytest.raises(RoleAssignmentError): active.assign_role(Role.PLATFORM_ADMINISTRATOR)
    assert active.assign_role(Role.DISPATCHER).assign_role(Role.DISPATCHER).roles==frozenset({Role.DISPATCHER})

@pytest.mark.parametrize("status",[MembershipStatus.INVITED,MembershipStatus.SUSPENDED,MembershipStatus.REVOKED,MembershipStatus.EXPIRED])
def test_inactive_membership_denied(status):
    decision=AuthorizationService().decide(human(),membership(status),request(),at=NOW)
    assert (decision.allowed,decision.code)==(False,DecisionCode.MEMBERSHIP_INACTIVE)

def test_authorization_permission_tenant_platform_and_missing_membership():
    service=AuthorizationService(); principal=human()
    assert service.decide(principal,membership(),request(),at=NOW).allowed
    assert service.decide(principal,membership(),request(Permission.PLATFORM_MANAGE),at=NOW).code is DecisionCode.PERMISSION_MISSING
    assert service.decide(principal,membership(),request(tenant=OTHER),at=NOW).code is DecisionCode.TENANT_MISMATCH
    assert service.decide(principal,None,request(),at=NOW).code is DecisionCode.MEMBERSHIP_NOT_FOUND
    assert service.decide(principal,membership(),request(platform_action=True),at=NOW).code is DecisionCode.PLATFORM_SCOPE_REQUIRED

def test_customer_and_driver_resource_ownership():
    service=AuthorizationService(); customer=human(); driver=human(Role.DRIVER)
    assert service.decide(customer,membership(),request(owner_id=customer.principal_id),at=NOW).allowed
    assert service.decide(customer,membership(),request(owner_id="other"),at=NOW).code is DecisionCode.RESOURCE_OWNERSHIP_REQUIRED
    delivery=request(Permission.DELIVERY_EXECUTE,assigned_principal_id=driver.principal_id)
    assert service.decide(driver,membership(roles=frozenset({Role.DRIVER})),delivery,at=NOW).allowed
    assert service.decide(driver,membership(roles=frozenset({Role.DRIVER})),request(Permission.DELIVERY_EXECUTE,assigned_principal_id="other"),at=NOW).code is DecisionCode.RESOURCE_OWNERSHIP_REQUIRED

@pytest.mark.parametrize(("role","permission"),[(Role.DISPATCHER,Permission.SHIPMENT_DISPATCH),(Role.FLEET_MANAGER,Permission.VEHICLE_MANAGE),(Role.WAREHOUSE_OPERATOR,Permission.INVENTORY_ADJUST),(Role.FINANCE_USER,Permission.DRIVER_MANAGE),(Role.COMPLIANCE_USER,Permission.SETTLEMENT_MANAGE)])
def test_representative_positive_and_negative_role_boundaries(role,permission):
    decision=AuthorizationService().decide(human(role),membership(roles=frozenset({role})),request(permission),at=NOW)
    assert decision.allowed==(permission in ROLE_PERMISSIONS[role])

def test_anonymous_and_service_scope_authorization():
    service=AuthorizationService(); anonymous=AnonymousPrincipal("r","c")
    assert service.decide(anonymous,None,request(),at=NOW).code is DecisionCode.UNAUTHENTICATED
    principal=ServicePrincipal(IdentityReference("novaid:service"),"tracking",frozenset({"novalogistics.tracking.ingest"}),"r","c",TENANT)
    allowed=request(Permission.SERVICE_INVOKE,service_scope="novalogistics.tracking.ingest")
    denied=request(Permission.SERVICE_INVOKE,service_scope="novalogistics.payments.sync")
    assert service.decide(principal,None,allowed,at=NOW).allowed
    assert service.decide(principal,None,denied,at=NOW).code is DecisionCode.SERVICE_SCOPE_MISSING

def test_tenant_resolution_rejects_spoofing_and_conflicts():
    resolver=TenantResolver(); principal=human()
    assert resolver.resolve(principal,token_tenant=TENANT,header_tenant=TENANT).tenant_id==TENANT
    with pytest.raises(TenantMismatchError): resolver.resolve(principal,token_tenant=TENANT,header_tenant=OTHER)

def test_novaid_adapter_active_inactive_missing_unavailable_and_timeout():
    identity=IdentityReference("novaid:user-1"); summary=IdentityStatusSummary(identity,True,"aal2",NOW)
    assert DeterministicNovaIDAdapter({identity.value:summary}).status(identity)==summary
    with pytest.raises(IdentityStatusInvalidError): DeterministicNovaIDAdapter().status(identity)
    with pytest.raises(IdentityStatusInvalidError): DeterministicNovaIDAdapter({identity.value:IdentityStatusSummary(identity,False,"aal1",NOW)}).status(identity)
    with pytest.raises(IdentityProviderUnavailableError): DeterministicNovaIDAdapter(unavailable=True).status(identity)
    with pytest.raises(IdentityProviderUnavailableError): DeterministicNovaIDAdapter({identity.value:summary}).status(identity,timeout_seconds=0)

def test_membership_persistence_uniqueness_isolation_and_concurrency():
    connection=connect(); repo=SQLiteMembershipRepository(connection); value=membership(); repo.add(value)
    assert repo.get(TENANT,value.id)==value
    with pytest.raises(AggregateAlreadyExistsError): repo.add(value)
    changed=value.assign_role(Role.DISPATCHER); repo.save(changed,expected_version=1)
    with pytest.raises(OptimisticConcurrencyError): repo.save(replace(changed,version=3),expected_version=1)
    assert repo.list(OTHER)==()

def test_service_identity_and_audit_persistence():
    connection=connect(); service=ServicePrincipal(IdentityReference("novaid:svc"),"webhook",frozenset({"novalogistics.webhooks.publish"}),"r","c",TENANT,credential_reference="credential-ref")
    SQLiteServiceIdentityRepository(connection).put(service)
    assert SQLiteServiceIdentityRepository(connection).get(service.identity,TENANT).credential_reference=="credential-ref"
    decision=AuthorizationService().decide(human(),membership(),request(),at=NOW)
    repo=SQLiteAuthorizationAuditRepository(connection); assert repo.append(decision)==repo.append(decision)

def test_authorization_migration_is_repeat_safe_and_indexed():
    connection=connect(); runner=MigrationRunner(connection)
    assert "0002_novalogistics_authorization" in runner.applied(); assert runner.migrate()==()
    indexes={row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    assert {"idx_nl_membership_tenant_status","idx_nl_service_tenant_status","idx_nl_auth_audit_tenant_time"}<=indexes

def test_novaid_public_exports_remain_compatible():
    from afritech.novaid.domain import AuthorizationDecision as NovaIDAuthorizationDecision, TenantMembership as NovaIDTenantMembership
    assert NovaIDAuthorizationDecision is not None and NovaIDTenantMembership is not None
