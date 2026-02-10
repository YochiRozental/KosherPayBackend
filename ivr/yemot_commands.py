from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ivr.formatters import clean


def yemot_read(text, param, min_len, max_len, timeout=10, read_type="Digits", confirm=True):
    confirm_value = "yes" if confirm else "no"

    second_part = (
        f"{param},,{max_len},{min_len},{timeout},{read_type}"
        f",,,,,,,,,{confirm_value}"
    )
    return f"read=t-{text}={second_part}"


def yemot_menu(text: str, var: str, *, timeout: int = 7, options: str = "1.2.3", confirm: bool = False) -> str:
    text = clean(text)
    confirm_value = "yes" if confirm else "no"
    return f"read=t-{text}={var},Digits,1,1,{timeout},No,AskNo,,,{options},,,,,,,,{confirm_value}"


def parse_ddmmyyyy(s: str) -> datetime | None:
    """
    מקבל מחרוזת 8 ספרות: ddmmyyyy (למשל 08022026)
    ומחזיר datetime ב-UTC בתחילת היום (timezone-aware).
    """
    s = (s or "").strip()
    if len(s) != 8 or not s.isdigit():
        return None
    try:
        dt = datetime.strptime(s, "%d%m%Y")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def get_history_range(choice: str, session: dict, now: datetime) -> tuple[datetime | None, datetime | None]:
    """
    now חייב להיות timezone-aware (UTC)
    """
    if choice == "1":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        return start, end

    if choice == "2":
        days_from_sunday = (now.weekday() + 1) % 7
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_from_sunday)
        end = now
        return start, end

    if choice == "3":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
        return start, end

    if choice == "__custom_range__":
        start_iso = session.get("history_range_start_iso")
        end_iso = session.get("history_range_end_iso")
        if not start_iso or not end_iso:
            return None, None
        try:
            start = datetime.fromisoformat(start_iso)
            end = datetime.fromisoformat(end_iso)
            return start, end
        except ValueError:
            return None, None

    return None, None
