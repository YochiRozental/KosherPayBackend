from fastapi import APIRouter, Depends, Query, HTTPException, status

from auth.dependencies import get_current_user
from db.deps import get_db
from domain.account_creation_services import open_account
from domain.auth_services import authenticate_user
from domain.payment_requests_services import (
    request_payment,
    get_my_payment_requests,
    get_my_sent_payment_requests,
    approve_payment_request,
    reject_payment_request,
)
from domain.payment_services import get_transaction_history, deposit, withdraw, transfer
from domain.users_service import get_me, update_me
from domain.wallet_services import get_balance
from repositories.users_repo import (
    get_user_id_by_phone,
)
from routes.utils import ensure_success
from schemas.auth import OpenAccountRequest, OpenAccountResponse, LoginRequest, LoginResponse
from schemas.payment_requests import (
    PaymentRequestRequest,
    PaymentRequestResponse,
    PaymentRequestsListResponse,
)
from schemas.payments import (
    DepositRequest,
    WithdrawRequest,
    TransferRequest,
    BalanceResponse,
    OperationResponse,
    TransactionHistoryResponse,
)
from schemas.users import UpdateMeRequest, UserMeResponse

router = APIRouter(prefix="/api/web", tags=["web"])


@router.post("/open_account", response_model=OpenAccountResponse, status_code=status.HTTP_201_CREATED)
async def open_account_route(request: OpenAccountRequest, conn=Depends(get_db)):
    result = open_account(
        conn,
        phone_number=request.phone_number,
        secret_code=request.secret_code,
        name=request.name,
        bank_number=request.bank_number,
        branch_number=request.branch_number,
        account_number=request.account_number,
    )

    if not result.get("success"):
        if result.get("error_code") == "PHONE_ALREADY_EXISTS":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result)

    return result


@router.post("/login", response_model=LoginResponse)
async def login_route(request: LoginRequest, conn=Depends(get_db)):
    result = authenticate_user(conn, request.phone_number, request.secret_code)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result)
    return result


@router.get("/balance", response_model=BalanceResponse)
async def balance_route(conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    return get_balance(conn, user_id=current_user["user_id"])


@router.get("/history", response_model=TransactionHistoryResponse)
async def history_route(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        conn=Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    return get_transaction_history(conn, user_id=current_user["user_id"], limit=limit, offset=offset)


@router.post("/deposit", response_model=OperationResponse)
async def deposit_route(
        request: DepositRequest,
        conn=Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    result = deposit(conn, user_id=current_user["user_id"], amount=request.amount)
    return ensure_success(result)


@router.post("/withdraw", response_model=OperationResponse)
async def withdraw_route(
        request: WithdrawRequest,
        conn=Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    result = withdraw(conn, user_id=current_user["user_id"], amount=request.amount)
    return ensure_success(result)


@router.post("/transfer", response_model=OperationResponse)
async def transfer_route(
        request: TransferRequest,
        conn=Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    recipient_id = get_user_id_by_phone(conn, request.recipient_phone)
    if not recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "מקבל לא נמצא"},
        )

    result = transfer(
        conn,
        from_user_id=current_user["user_id"],
        to_user_id=recipient_id,
        amount=request.amount,
    )
    return ensure_success(result)


@router.post("/request_payment", response_model=PaymentRequestResponse)
async def request_payment_route(
        request: PaymentRequestRequest,
        conn=Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    recipient_id = get_user_id_by_phone(conn, request.recipient_phone)
    if not recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "משתמש לא נמצא"},
        )

    result = request_payment(
        conn,
        requester_id=current_user["user_id"],
        recipient_id=recipient_id,
        amount=request.amount,
    )
    return ensure_success(result)


@router.get("/payment_requests", response_model=PaymentRequestsListResponse)
async def my_requests(conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    return get_my_payment_requests(conn, user_id=current_user["user_id"])


@router.get("/payment_requests_sent", response_model=PaymentRequestsListResponse)
async def my_sent_requests(conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    return get_my_sent_payment_requests(conn, user_id=current_user["user_id"])


@router.post("/payment_requests/{req_id}/approve", response_model=OperationResponse)
async def approve_request(
        req_id: str,
        conn=Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    result = approve_payment_request(conn, user_id=current_user["user_id"], request_id=req_id)
    return ensure_success(result)


@router.post("/payment_requests/{req_id}/reject", response_model=OperationResponse)
async def reject_request(
        req_id: str,
        conn=Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    result = reject_payment_request(conn, user_id=current_user["user_id"], request_id=req_id)
    return ensure_success(result)


# ============================
# USER PROFILE (ME) - SINGLE SOURCE OF TRUTH
# ============================

@router.get("/me", response_model=UserMeResponse)
async def me_route(conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = get_me(conn, user_id=current_user["user_id"])
    return ensure_success(result, status_code=status.HTTP_404_NOT_FOUND)


@router.put("/me", response_model=UserMeResponse)
async def update_me_route(
        payload: UpdateMeRequest,
        conn=Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    result = update_me(
        conn,
        user_id=current_user["user_id"],
        name=payload.name,
        phone=payload.phone,
        secret_code=payload.secret_code,
        bank_number=payload.bank_number,
        branch_number=payload.branch_number,
        account_number=payload.account_number,
        account_holder=payload.account_holder,
    )
    return ensure_success(result)
