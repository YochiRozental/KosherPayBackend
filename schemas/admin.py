from pydantic import BaseModel
from typing import Optional


class AdminAuthRequest(BaseModel):
    phone_number: str
    secret_code: str


class UsersListResponse(BaseModel):
    success: bool
    users: list[dict]
    message: Optional[str] = None
