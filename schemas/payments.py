from pydantic import BaseModel, Field
from typing import Optional


class DepositRequest(BaseModel):
    amount: float = Field(..., gt=0)


class WithdrawRequest(BaseModel):
    amount: float = Field(..., gt=0)


class TransferRequest(BaseModel):
    recipient_phone: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)


class TransactionHistoryResponse(BaseModel):
    success: bool
    count: int
    history: list[dict]
    message: Optional[str] = None


class BalanceResponse(BaseModel):
    success: bool
    balance: float | None = None
    currency: str | None = None
    message: Optional[str] = None


class OperationResponse(BaseModel):
    success: bool
    message: str
