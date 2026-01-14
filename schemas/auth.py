from pydantic import BaseModel, Field

class OpenAccountRequest(BaseModel):
    phone_number: str = Field(..., min_length=1)
    secret_code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    bank_number: str = Field(..., min_length=1)
    branch_number: str = Field(..., min_length=1)
    account_number: str = Field(..., min_length=1)

class OpenAccountResponse(BaseModel):
    success: bool
    message: str
    user_id: str | None = None
    bank_account_id: str | None = None
    error_code: str | None = None

class LoginRequest(BaseModel):
    phone_number: str = Field(..., min_length=1)
    secret_code: str = Field(..., min_length=1)

class LoginResponse(BaseModel):
    success: bool
    access_token: str | None = None
    refresh_token: str | None = None
    user: dict | None = None
    message: str | None = None
