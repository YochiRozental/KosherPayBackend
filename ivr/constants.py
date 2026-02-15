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
    # (key, label_tts, read_var, min, max, read_type)
    ("name", "שֵם", "new_name", 2, 40, "Text"),
    ("phone", "טלפון", "new_phone", 9, 10, "Digits"),
    ("secret_code", "קוד סודי", "new_secret_code", 4, 6, "Digits"),
    ("bank_number", "מספר בנק", "new_bank_number", 2, 2, "Digits"),
    ("branch_number", "מספר סניף", "new_branch_number", 3, 3, "Digits"),
    ("account_number", "מספר חשבון", "new_account_number", 5, 10, "Digits"),
    ("account_holder", "שם בעל החשבון", "new_account_holder", 2, 40, "Text"),
]
