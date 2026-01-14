import datetime

HEBREW_MONTHS = {
    1: "ינואר",
    2: "פברואר",
    3: "מרץ",
    4: "אפריל",
    5: "מאי",
    6: "יוני",
    7: "יולי",
    8: "אוגוסט",
    9: "ספטמבר",
    10: "אוקטובר",
    11: "נובמבר",
    12: "דצמבר"
}

def format_date_for_ivr(dt: datetime.datetime):
    day = dt.day
    month_name = HEBREW_MONTHS[dt.month]
    year = dt.year

    hour = dt.hour
    minute = dt.minute

    if minute == 0:
        time_text = f"{hour}"
    else:
        time_text = f"{hour} ו {minute}"

    return f"בתאריך {day} ב{month_name} {year} בשעה {time_text}"
