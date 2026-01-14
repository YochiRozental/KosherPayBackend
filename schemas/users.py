from pydantic import BaseModel, Field
from typing import Optional

class UserMeResponse(BaseModel):
    success: bool
    user: dict

class UpdateMeRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    phone: Optional[str] = Field(default=None, min_length=9)
    secret_code: Optional[str] = Field(default=None, min_length=4)

    bank_number: Optional[str] = None
    branch_number: Optional[str] = None
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
