from typing import Optional

from pydantic import BaseModel


class AdminAuthRequest(BaseModel):
    phone_number: str
    secret_code: str


class UsersListResponse(BaseModel):
    success: bool
    users: list[dict]
    message: Optional[str] = None
