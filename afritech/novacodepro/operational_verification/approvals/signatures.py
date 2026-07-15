from ..hashing import domain_hash


def sign_approval(payload: dict[str, object]) -> str:
    return domain_hash("novacodepro.executive.approval", payload)
