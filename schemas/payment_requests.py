from typing import Optional

from pydantic import BaseModel, Field


class PaymentRequestRequest(BaseModel):
    recipient_phone: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)


class PaymentRequestResponse(BaseModel):
    success: bool
    message: str
    request_id: Optional[str] = None


class PaymentRequestsListResponse(BaseModel):
    success: bool
    requests: list[dict]
