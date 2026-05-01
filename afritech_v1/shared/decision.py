class Decision:
    def __init__(self, action: str, allowed: bool, reason: str):
        self.action = action
        self.allowed = allowed
        self.reason = reason

    def __repr__(self):
        return f"<Decision action={self.action} allowed={self.allowed} reason={self.reason}>"