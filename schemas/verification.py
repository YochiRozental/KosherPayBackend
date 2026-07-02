from pydantic import BaseModel, Field


class ForgotSecretStartRequest(BaseModel):
    phone_number: str = Field(..., min_length=7, max_length=20)


class ForgotSecretVerifyRequest(BaseModel):
    challenge_id: str
    code: str = Field(..., min_length=4, max_length=4)


class ForgotSecretResetRequest(BaseModel):
    challenge_id: str
    new_secret: str = Field(..., min_length=6, max_length=6)


class VerificationResponse(BaseModel):
    success: bool
    message: str
    challenge_id: str | None = None
    expires_in_minutes: int | None = None
