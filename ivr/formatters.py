from datetime import datetime, timezone

from ivr.constants import STATUS_HE, TYPE_HE


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


def _nice_day(created: datetime | None) -> str:
    if not created:
        return ""
    now = datetime.now(created.tzinfo or timezone.utc).date()
    d = created.date()
    if d == now:
        return "היום"
    if (now.toordinal() - d.toordinal()) == 1:
        return "אתמול"
    return created.strftime("בתאריך " + "%d/%m")


def format_text_line(tr: dict, *, counterparty: str | None = None) -> str:
    action = TYPE_HE.get(tr.get("type"), "פעולה")
    amt = amount_to_int(tr.get("amount"))

    created = tr.get("created_at") if isinstance(tr.get("created_at"), datetime) else None
    day = _nice_day(created)

    parts = []
    if day:
        parts.append(day)
    parts.append(action)
    if amt is not None:
        parts.append(f"{amt} שקלים")
    if counterparty:
        parts.append(f"מול {counterparty}")

    return clean(" ".join(parts))


def format_sent_request_line(req: dict) -> str:
    amount = amount_to_int(req.get("amount")) or 0
    created = req.get("created_at") if isinstance(req.get("created_at"), datetime) else None
    day = _nice_day(created)

    recipient_name = req.get("recipient_name") or req.get("to_name") or "משתמש"

    status = STATUS_HE.get(req.get("status"), str(req.get("status") or "ממתינה"))
    parts = []
    if day:
        parts.append(day)
    parts.append(f"בקשה אל {recipient_name}")
    parts.append(f"סכום {amount} שקלים")
    parts.append(f"סטטוס {status}")
    return clean(" ".join(parts))


def present_value(field_key: str, value) -> str:
    if value is None or str(value).strip() == "":
        return "לא מעודכן"
    if field_key == "secret_code":
        return "שמורה"
    return str(value).strip()
