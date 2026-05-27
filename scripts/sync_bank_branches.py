from __future__ import annotations

import json
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

from db.connection import get_db_connection

DATA_GOV_URL = "https://data.gov.il/api/3/action/datastore_search"
RESOURCE_ID = "2202bada-4baf-45f5-aa61-8c5bad9646d3"


def normalize_code(value) -> str:
    value = str(value or "").strip()

    if not value:
        return ""

    if value.isdigit():
        return str(int(value))

    return value


def parse_close_date(value):
    value = str(value or "").strip()

    if not value:
        return None

    # מנקה תווים נפוצים שעלולים להגיע מהמקור
    value = value.replace("\u200f", "").replace("\u200e", "").strip()

    # אם הגיע תאריך עם שעה — לוקחים רק את חלק התאריך
    value = value.split("T")[0].split(" ")[0].strip()

    formats = (
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d.%m.%y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    print(f"Warning: Could not parse Close_Date value: '{value}'")
    return None


def fetch_all_records() -> list[dict]:
    records: list[dict] = []
    limit = 1000
    offset = 0

    while True:
        res = requests.get(
            DATA_GOV_URL,
            params={
                "resource_id": RESOURCE_ID,
                "limit": limit,
                "offset": offset,
            },
            timeout=30,
        )
        res.raise_for_status()

        batch = res.json()["result"]["records"]

        if not batch:
            break

        records.extend(batch)
        offset += limit

        print(f"Fetched {len(records)} records...")

    return records


def upsert_branch(conn, record: dict) -> None:
    bank_code = normalize_code(record.get("Bank_Code"))
    branch_code = normalize_code(record.get("Branch_Code"))

    bank_name = str(record.get("Bank_Name") or "").strip()
    branch_name = str(record.get("Branch_Name") or "").strip()

    city = str(record.get("City") or "").strip() or None
    address = str(record.get("Address") or "").strip() or None

    raw_close_date = str(record.get("Close_Date") or "").strip()
    close_date = parse_close_date(raw_close_date)
    is_closed = bool(raw_close_date)

    if not bank_code or not branch_code or not bank_name or not branch_name:
        return

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bank_branches (
                bank_code,
                branch_code,
                bank_name,
                branch_name,
                city,
                address,
                is_closed,
                close_date,
                raw_data,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, NOW())
            ON CONFLICT (bank_code, branch_code)
            DO UPDATE SET
                bank_name = EXCLUDED.bank_name,
                branch_name = EXCLUDED.branch_name,
                city = EXCLUDED.city,
                address = EXCLUDED.address,
                is_closed = EXCLUDED.is_closed,
                close_date = EXCLUDED.close_date,
                raw_data = EXCLUDED.raw_data,
                updated_at = NOW()
            """,
            (
                bank_code,
                branch_code,
                bank_name,
                branch_name,
                city,
                address,
                is_closed,
                close_date,
                json.dumps(record, ensure_ascii=False),
            ),
        )


def main() -> None:
    records = fetch_all_records()

    with get_db_connection() as conn:
        for record in records:
            upsert_branch(conn, record)

    print(f"Done. Synced {len(records)} bank branches.")


if __name__ == "__main__":
    main()
