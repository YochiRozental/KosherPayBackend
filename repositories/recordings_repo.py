from __future__ import annotations

from typing import Any

from psycopg.rows import dict_row


def get_latest_user_recording(conn, *, user_id: str, record_type: str) -> dict[str, Any] | None:
    user_id = (user_id or "").strip()
    record_type = (record_type or "").strip()

    if not user_id or not record_type:
        return None

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id::text AS id,
                   user_id::text AS user_id,
                   record_type,
                   file_path,
                   created_at
            FROM recordings
            WHERE user_id = %s
              AND record_type = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id, record_type),
        )
        return cur.fetchone()


def create_user_recording(
        conn,
        *,
        user_id: str,
        record_type: str,
        file_path: str,
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO recordings (user_id, record_type, file_path)
            VALUES (%s, %s, %s)
            RETURNING id::text AS id,
                      user_id::text AS user_id,
                      record_type,
                      file_path,
                      created_at
            """,
            (user_id, record_type, file_path),
        )
        return cur.fetchone()
