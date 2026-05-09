from fastapi import Header, HTTPException, Depends
from api.auth.auth_service import AuthService
from api.auth.rbac import RBAC

# Global instances (can be improved later)
auth_service = AuthService()
rbac = RBAC()


# -----------------------------------------------------------------
# DEPENDENCY: AUTHENTICATION
# -----------------------------------------------------------------

def get_current_user(x_api_key: str = Header(...)):

    try:
        return auth_service.authenticate(x_api_key)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# -----------------------------------------------------------------
# RBAC DEPENDENCY FACTORY
# -----------------------------------------------------------------

def require_permission(action: str):

    def dependency(user=Depends(get_current_user)):

        try:
            rbac.authorize(user, action)
            return user
        except Exception as e:
            raise HTTPException(status_code=403, detail=str(e))

    return dependency
