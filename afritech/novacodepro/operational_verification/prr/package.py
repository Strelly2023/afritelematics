from __future__ import annotations

from ..hashing import domain_hash
from .models import PRRDomainResult, PRRPackage


DOMAINS = ("quality", "security", "performance", "accessibility", "ux", "operations", "observability", "resilience", "deployment", "mobile_release", "architecture", "governance")


def generate_prr_package(release_id: str, evidence_refs: list[str], environment: str = "ci") -> PRRPackage:
    status = "PASS" if evidence_refs else "PENDING"
    domains = tuple(PRRDomainResult(domain=domain, status=status, evidence_refs=tuple(evidence_refs)) for domain in DOMAINS)
    manifest_hash = domain_hash("novacodepro.prr.package", {"release_id": release_id, "evidence_refs": evidence_refs, "environment": environment})
    return PRRPackage(
        prr_id=f"prr-{release_id}",
        release_id=release_id,
        environment=environment,
        evidence_manifest_hash=manifest_hash,
        domains=domains,
        recommendation="READY_FOR_PRR_APPROVAL" if evidence_refs else "EVIDENCE_PENDING",
    )
