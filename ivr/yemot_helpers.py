from datetime import timedelta

# def yemot_read(text, param, min_len, max_len, timeout=10, read_type="Digits"):
#     second_part = f"{param},,{max_len},{min_len},{timeout},{read_type},,,,,,,,,no"
#     return f"read=t-{text}={second_part}"

def yemot_read(text, param, min_len, max_len, timeout=10, read_type="Digits", confirm=True):

    confirm_value = "yes" if confirm else "no"

    second_part = (
        f"{param},,{max_len},{min_len},{timeout},{read_type}"
        f",,,,,,,,,{confirm_value}"
    )
    return f"read=t-{text}={second_part}"


STATUS_HE = {
    "pending": "ממתינה",
    "approved": "אושרה",
    "rejected": "נדחתה",
    "paid": "שולמה",
}

def get_history_range(choice, session, now):
    if choice == "1":  # היום
        return now.replace(hour=0, minute=0, second=0, microsecond=0), now

    if choice == "2":  # שבוע נוכחי
        days_from_sunday = (now.weekday() + 1) % 7
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_from_sunday)
        return start, now

    if choice == "3":  # חודש נוכחי
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now

    if choice == "__custom_range__":
        return session["start"], session["end"]

    return None, None
