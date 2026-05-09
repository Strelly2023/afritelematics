from pydantic import BaseModel
from typing import List


class APIKey(BaseModel):
    key: str
    owner: str
    roles: List[str]


class AuthContext(BaseModel):
    key: str
    user: str
    roles: List[str]
