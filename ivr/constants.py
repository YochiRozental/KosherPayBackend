from zoneinfo import ZoneInfo

TYPE_HE = {
    "deposit": "הופקדו",
    "withdraw": "נמשכו",
    "transfer": "הועברו",
    "payment_approve": "אושרה בקשת תשלום",
    "payment_reject": "נדחתה בקשת תשלום",
    "payment_request": "נשלחה בקשת תשלום",
}

STATUS_HE = {
    None: "ממתינה",
    "": "ממתינה",
    "pending": "ממתינה",
    "approved": "אושרה",
    "rejected": "נדחתה",
    "canceled": "בוטלה",
}

EDIT_FIELDS = [
    ("name", "LBL_NAME", "new_name", 2, 40, "Text"),
    ("phone", "LBL_PHONE", "new_phone", 9, 10, "Digits"),
    ("secret_code", "LBL_SECRET_CODE", "new_secret_code", 4, 6, "Digits"),
    ("bank_number", "LBL_BANK_NUMBER", "new_bank_number", 2, 2, "Digits"),
    ("branch_number", "LBL_BRANCH_NUMBER", "new_branch_number", 3, 3, "Digits"),
    ("account_number", "LBL_ACCOUNT_NUMBER", "new_account_number", 5, 10, "Digits"),
    ("account_holder", "LBL_ACCOUNT_HOLDER", "new_account_holder", 2, 40, "Text"),
]

IL_TZ = ZoneInfo("Asia/Jerusalem")

SR_STATUS_KEY_MAP = {
    None: "SR_STATUS_PENDING",
    "": "SR_STATUS_PENDING",
    "pending": "SR_STATUS_PENDING",
    "approved": "SR_STATUS_APPROVED",
    "rejected": "SR_STATUS_REJECTED",
}

HIST_TYPE_TO_PROMPT = {
    "payment_request": "HIST_ACT_PAYMENT_REQUEST",
    "payment_request_approved": "HIST_ACT_PAYMENT_APPROVED",
    "payment_request_rejected": "HIST_ACT_PAYMENT_REJECTED",
    "transfer": "HIST_ACT_TRANSFER",
    "deposit": "HIST_ACT_DEPOSIT",
    "withdraw": "HIST_ACT_WITHDRAW",
}

BANK_MAP = {
    "bank_number": ("bankAccount", "bankNumber"),
    "branch_number": ("bankAccount", "branchNumber"),
    "account_number": ("bankAccount", "accountNumber"),
    "account_holder": ("bankAccount", "accountHolder"),
}
