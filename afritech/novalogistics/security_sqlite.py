"""Durable NovaLogistics authorization assignments and audit evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import sqlite3

from .domain import Identifier
from .persistence import AggregateAlreadyExistsError, AggregateNotFoundError, OptimisticConcurrencyError, TenantScopeError
from .security import AuthorizationDecision, IdentityReference, MembershipStatus, Permission, Role, ServicePrincipal, ServiceStatus, TenantMembership


def _dump_membership(value: TenantMembership) -> str:
    payload={"schema":"novalogistics.membership.v1","id":str(value.id),"tenant_id":str(value.tenant_id),"identity":value.identity.to_dict(),"status":value.status.value,"roles":sorted(r.value for r in value.roles),"direct_permissions":sorted(p.value for p in value.direct_permissions),"version":value.version,"invited_at":value.invited_at.isoformat() if value.invited_at else None,"activated_at":value.activated_at.isoformat() if value.activated_at else None,"suspended_at":value.suspended_at.isoformat() if value.suspended_at else None,"revoked_at":value.revoked_at.isoformat() if value.revoked_at else None,"expires_at":value.expires_at.isoformat() if value.expires_at else None,"audit_actor":value.audit_actor.to_dict() if value.audit_actor else None}
    return json.dumps(payload,sort_keys=True,separators=(",",":"))


def _load_membership(raw: str)->TenantMembership:
    p=json.loads(raw); identity=p["identity"]; actor=p.get("audit_actor")
    return TenantMembership(Identifier(p["id"]),Identifier(p["tenant_id"]),IdentityReference(identity["value"],identity["authority"],identity["contract_version"]),MembershipStatus(p["status"]),frozenset(Role(r) for r in p["roles"]),frozenset(Permission(x) for x in p["direct_permissions"]),int(p["version"]),*[(datetime.fromisoformat(p[n]) if p.get(n) else None) for n in ("invited_at","activated_at","suspended_at","revoked_at","expires_at")],IdentityReference(actor["value"],actor["authority"],actor["contract_version"]) if actor else None)


class SQLiteMembershipRepository:
    def __init__(self, connection:sqlite3.Connection): self.connection=connection
    def add(self,value:TenantMembership)->None:
        now=datetime.now(timezone.utc).isoformat(); raw=_dump_membership(value)
        try: self.connection.execute("INSERT INTO novalogistics_memberships(membership_id,tenant_id,identity_reference,status,roles_json,permissions_json,membership_version,payload_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(str(value.id),str(value.tenant_id),value.identity.value,value.status.value,json.dumps(sorted(r.value for r in value.roles)),json.dumps(sorted(p.value for p in value.direct_permissions)),value.version,raw,now,now))
        except sqlite3.IntegrityError as exc: raise AggregateAlreadyExistsError(str(value.id)) from exc
    def get(self,tenant_id:Identifier,membership_id:Identifier)->TenantMembership:
        row=self.connection.execute("SELECT payload_json FROM novalogistics_memberships WHERE tenant_id=? AND membership_id=?",(str(tenant_id),str(membership_id))).fetchone()
        if row is None: raise AggregateNotFoundError(str(membership_id))
        return _load_membership(row[0])
    def find_identity(self,tenant_id:Identifier,identity:IdentityReference)->TenantMembership:
        row=self.connection.execute("SELECT payload_json FROM novalogistics_memberships WHERE tenant_id=? AND identity_reference=?",(str(tenant_id),identity.value)).fetchone()
        if row is None: raise AggregateNotFoundError(identity.value)
        return _load_membership(row[0])
    def save(self,value:TenantMembership,*,expected_version:int)->None:
        cursor=self.connection.execute("UPDATE novalogistics_memberships SET status=?,roles_json=?,permissions_json=?,membership_version=?,payload_json=?,updated_at=? WHERE tenant_id=? AND membership_id=? AND membership_version=?",(value.status.value,json.dumps(sorted(r.value for r in value.roles)),json.dumps(sorted(p.value for p in value.direct_permissions)),value.version,_dump_membership(value),datetime.now(timezone.utc).isoformat(),str(value.tenant_id),str(value.id),expected_version))
        if cursor.rowcount: return
        row=self.connection.execute("SELECT tenant_id FROM novalogistics_memberships WHERE membership_id=?",(str(value.id),)).fetchone()
        if row is None: raise AggregateNotFoundError(str(value.id))
        if row[0]!=str(value.tenant_id): raise TenantScopeError(str(value.id))
        raise OptimisticConcurrencyError(str(value.id))
    def list(self,tenant_id:Identifier)->tuple[TenantMembership,...]:
        return tuple(_load_membership(r[0]) for r in self.connection.execute("SELECT payload_json FROM novalogistics_memberships WHERE tenant_id=? ORDER BY identity_reference,membership_id",(str(tenant_id),)))


class SQLiteServiceIdentityRepository:
    def __init__(self,connection:sqlite3.Connection): self.connection=connection
    def put(self,value:ServicePrincipal)->None:
        now=datetime.now(timezone.utc).isoformat(); self.connection.execute("INSERT INTO novalogistics_service_identities(service_identity,tenant_id,service_name,status,scopes_json,credential_reference,platform_scope,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",(value.identity.value,str(value.tenant_id) if value.tenant_id else None,value.service_name,value.status.value,json.dumps(sorted(value.scopes)),value.credential_reference,int(value.platform_scope),now,now))
    def get(self,identity:IdentityReference,tenant_id:Identifier|None)->ServicePrincipal:
        row=self.connection.execute("SELECT * FROM novalogistics_service_identities WHERE service_identity=? AND tenant_id IS ?",(identity.value,str(tenant_id) if tenant_id else None)).fetchone()
        if row is None: raise AggregateNotFoundError(identity.value)
        return ServicePrincipal(identity,row["service_name"],frozenset(json.loads(row["scopes_json"])),"persisted-request","persisted-correlation",Identifier(row["tenant_id"]) if row["tenant_id"] else None,bool(row["platform_scope"]),ServiceStatus(row["status"]),row["credential_reference"])


class SQLiteAuthorizationAuditRepository:
    def __init__(self,connection:sqlite3.Connection): self.connection=connection
    def append(self,decision:AuthorizationDecision)->str:
        payload=json.dumps({"allowed":decision.allowed,"code":decision.code.value,"principal_id":decision.principal_id,"tenant_id":decision.tenant_id,"permission":decision.permission,"resource_type":decision.resource_type,"resource_id":decision.resource_id,"reason_code":decision.reason_code,"evaluated_roles":list(decision.evaluated_roles),"correlation_id":decision.correlation_id,"request_id":decision.request_id,"decided_at":decision.decided_at.isoformat()},sort_keys=True,separators=(",",":")); decision_id=sha256(payload.encode()).hexdigest()
        self.connection.execute("INSERT OR IGNORE INTO novalogistics_authorization_audit(decision_id,tenant_id,principal_id,permission,decision_code,resource_type,resource_id,request_id,correlation_id,decided_at,payload_json) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(decision_id,decision.tenant_id,decision.principal_id,decision.permission,decision.code.value,decision.resource_type,decision.resource_id,decision.request_id,decision.correlation_id,decision.decided_at.isoformat(),payload)); return decision_id
