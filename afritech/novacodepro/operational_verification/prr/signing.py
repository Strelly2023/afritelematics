from ..hashing import domain_hash


def sign_manifest(manifest: dict[str, object], assurance: str = "DEVELOPMENT_ONLY") -> dict[str, str]:
    return {"signature": domain_hash(f"novacodepro.prr.signature.{assurance}", manifest), "signature_assurance": assurance}
