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

BANK_MAP = {
    "bank_number": ("bankAccount", "bankNumber"),
    "branch_number": ("bankAccount", "branchNumber"),
    "account_number": ("bankAccount", "accountNumber"),
    "account_holder": ("bankAccount", "accountHolder"),
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