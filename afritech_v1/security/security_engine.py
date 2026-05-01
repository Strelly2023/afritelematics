def enforce(proof):
    if not proof["allowed"]:
        raise Exception(f"SECURITY BLOCK: {proof['action']}")
    return True