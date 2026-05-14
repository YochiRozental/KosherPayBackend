from datetime import datetime

from ivr.config import IL_TZ


def clean(s: str) -> str:
    return (
        str(s)
        .replace("&", " ")
        .replace("=", " ")
        .replace(".", " ")
        .replace("\n", " ")
        .replace("\r", " ")
        .strip()
    )


def amount_to_int(amount_raw) -> int | None:
    try:
        return int(float(amount_raw))
    except (ValueError, TypeError):
        return None


def date_for_yemot(dt: datetime) -> str:
    d = dt.astimezone(IL_TZ).date()
    return f"date-{d.strftime('%d/%m/%Y')}"
