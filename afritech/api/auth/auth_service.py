import hashlib
from typing import Dict
from api.auth.auth_models import APIKey, AuthContext


class AuthService:

    def __init__(self):
        self._keys: Dict[str, APIKey] = {}

    # -----------------------------------------------------------------
    # REGISTER API KEY
    # -----------------------------------------------------------------

    def register_key(self, key: str, owner: str, roles: list):

        hashed = self._hash_key(key)

        self._keys[hashed] = APIKey(
            key=hashed,
            owner=owner,
            roles=roles
        )

    # -----------------------------------------------------------------
    # VALIDATE KEY
    # -----------------------------------------------------------------

    def authenticate(self, key: str) -> AuthContext:

        hashed = self._hash_key(key)

        record = self._keys.get(hashed)

        if not record:
            raise Exception("Invalid API key")

        return AuthContext(
            key=hashed,
            user=record.owner,
            roles=record.roles
        )

    # -----------------------------------------------------------------
    # HASHING (SECURE STORAGE)
    # -----------------------------------------------------------------

    def _hash_key(self, key: str):
        return hashlib.sha256(key.encode()).hexdigest()