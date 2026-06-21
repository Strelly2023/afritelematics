from __future__ import annotations

from hashlib import sha256
from typing import Any


class NovaTrustCertificateAuthority:
    def __init__(self) -> None:
        self._chains: dict[str, dict[str, Any]] = {}
        self._certificates: dict[str, dict[str, Any]] = {}
        self._root = {
            "certificate_id": "novatrust-root-v1",
            "subject": "NovaTrust Root",
            "issuer": "NovaTrust Root",
            "scope": "engineering_trust_verification",
            "public_key_hash": sha256(b"novatrust-root-v1").hexdigest(),
        }
        self._root["signature"] = _sign_certificate(self._root, issuer_key=self._root["public_key_hash"])
        self._certificates[self._root["certificate_id"]] = self._root

    def issue_chain(
        self,
        *,
        organization_id: str,
        project_id: str,
        receipt: dict[str, Any],
        federation: dict[str, Any],
    ) -> dict[str, Any]:
        org_cert = _certificate(
            certificate_id=f"novatrust-org-{organization_id}",
            subject=organization_id,
            issuer=self._root["certificate_id"],
            scope="organization_trust_authority",
        )
        receipt_cert = _certificate(
            certificate_id=f"novatrust-receipt-{receipt.get('receipt_id', 'unknown')}",
            subject=str(receipt.get("receipt_id", "")),
            issuer=org_cert["certificate_id"],
            scope="governance_receipt",
            evidence_hash=sha256(str(sorted(receipt.items())).encode("utf-8")).hexdigest(),
        )
        chain = {
            "chain_id": "chain-" + sha256(
                f"{organization_id}:{project_id}:{receipt.get('receipt_id')}:{federation.get('federation_id')}".encode(
                    "utf-8"
                )
            ).hexdigest()[:12],
            "organization_id": organization_id,
            "project_id": project_id,
            "root_certificate": self._root,
            "organization_certificate": org_cert,
            "receipt_certificate": receipt_cert,
            "federation_consensus": {
                "federation_id": federation.get("federation_id"),
                "verified": bool(federation.get("verified")),
                "payload_hash": federation.get("payload_hash"),
            },
        }
        chain["chain_hash"] = sha256(str(sorted(_flatten_chain(chain).items())).encode("utf-8")).hexdigest()
        self._chains[chain["chain_id"]] = chain
        for certificate in (self._root, org_cert, receipt_cert):
            self._certificates[certificate["certificate_id"]] = certificate
        return chain

    def find_certificate(self, certificate_id: str) -> dict[str, Any] | None:
        return self._certificates.get(certificate_id)

    def find_chain_by_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        subject = str(receipt_id)
        for chain in self._chains.values():
            if chain.get("receipt_certificate", {}).get("subject") == subject:
                return chain
        return None

    def verify_chain(
        self,
        *,
        receipt: dict[str, Any],
        chain: dict[str, Any],
        receipt_verification: dict[str, Any],
    ) -> dict[str, Any]:
        root_ok = chain.get("root_certificate", {}).get("certificate_id") == self._root["certificate_id"]
        org_ok = chain.get("organization_certificate", {}).get("issuer") == self._root["certificate_id"]
        receipt_ok = chain.get("receipt_certificate", {}).get("subject") == receipt.get("receipt_id")
        root_signature_ok = _verify_certificate(chain.get("root_certificate", {}), issuer_key=self._root["public_key_hash"])
        org_signature_ok = _verify_certificate(
            chain.get("organization_certificate", {}),
            issuer_key=sha256(f"{chain.get('root_certificate', {}).get('certificate_id')}:public".encode()).hexdigest(),
        )
        receipt_signature_ok = _verify_certificate(
            chain.get("receipt_certificate", {}),
            issuer_key=sha256(f"{chain.get('organization_certificate', {}).get('certificate_id')}:public".encode()).hexdigest(),
        )
        federation_ok = bool(chain.get("federation_consensus", {}).get("verified"))
        signature_ok = bool(receipt_verification.get("verified"))
        return {
            "verified": (
                root_ok
                and org_ok
                and receipt_ok
                and root_signature_ok
                and org_signature_ok
                and receipt_signature_ok
                and federation_ok
                and signature_ok
            ),
            "checks": {
                "receipt_signature": signature_ok,
                "root_certificate": root_ok,
                "organization_certificate": org_ok,
                "receipt_certificate": receipt_ok,
                "root_certificate_signature": root_signature_ok,
                "organization_certificate_signature": org_signature_ok,
                "receipt_certificate_signature": receipt_signature_ok,
                "federation_consensus": federation_ok,
            },
            "chain_id": chain.get("chain_id"),
            "chain_hash": chain.get("chain_hash"),
        }


def _certificate(
    *,
    certificate_id: str,
    subject: str,
    issuer: str,
    scope: str,
    evidence_hash: str | None = None,
) -> dict[str, Any]:
    payload = {
        "certificate_id": certificate_id,
        "subject": subject,
        "issuer": issuer,
        "scope": scope,
        "evidence_hash": evidence_hash or sha256(f"{certificate_id}:{subject}:{issuer}:{scope}".encode()).hexdigest(),
    }
    payload["public_key_hash"] = sha256(f"{certificate_id}:{subject}:public".encode()).hexdigest()
    payload["certificate_hash"] = sha256(str(sorted(payload.items())).encode("utf-8")).hexdigest()
    payload["signature"] = _sign_certificate(payload, issuer_key=sha256(f"{issuer}:public".encode()).hexdigest())
    return payload


def _sign_certificate(certificate: dict[str, Any], *, issuer_key: str) -> str:
    unsigned = {key: value for key, value in certificate.items() if key == "signature" or key != "signature"}
    unsigned.pop("signature", None)
    return sha256(f"{issuer_key}:{sorted(unsigned.items())}".encode("utf-8")).hexdigest()


def _verify_certificate(certificate: dict[str, Any], *, issuer_key: str) -> bool:
    return certificate.get("signature") == _sign_certificate(certificate, issuer_key=issuer_key)


def _flatten_chain(chain: dict[str, Any]) -> dict[str, Any]:
    return {
        "chain_id": chain.get("chain_id"),
        "organization_id": chain.get("organization_id"),
        "project_id": chain.get("project_id"),
        "root": chain.get("root_certificate", {}).get("certificate_hash"),
        "org": chain.get("organization_certificate", {}).get("certificate_hash"),
        "receipt": chain.get("receipt_certificate", {}).get("certificate_hash"),
        "federation": chain.get("federation_consensus", {}).get("payload_hash"),
    }


_DEFAULT_CERTIFICATE_AUTHORITY = NovaTrustCertificateAuthority()


def get_novatrust_certificate_authority() -> NovaTrustCertificateAuthority:
    return _DEFAULT_CERTIFICATE_AUTHORITY
