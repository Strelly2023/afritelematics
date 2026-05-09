from api.auth.auth_models import AuthContext


class RBACError(Exception):
    pass


class RBAC:

    def __init__(self):
        """
        Define permissions per role
        """
        self.permissions = {
            "admin": ["execute", "audit", "proof", "dashboard"],
            "auditor": ["audit", "proof", "dashboard"],
            "user": ["execute"],
            "node": ["execute"],
        }

    # -----------------------------------------------------------------
    # CHECK PERMISSION
    # -----------------------------------------------------------------

    def authorize(self, context: AuthContext, action: str):

        for role in context.roles:
            if action in self.permissions.get(role, []):
                return True

        raise RBACError(
            f"Access denied for user={context.user} action={action}"
        )