def recommendation_for(valid: bool) -> str:
    return "READY_FOR_PRR_APPROVAL" if valid else "EVIDENCE_PENDING"
