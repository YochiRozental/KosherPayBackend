from __future__ import annotations

from typing import Any

import psycopg

from repositories.recordings_repo import create_user_recording
from repositories.recordings_repo import get_latest_user_recording


def get_user_name_recording(conn, *, user_id: str) -> dict[str, Any]:
    user_id = (user_id or "").strip()

    if not user_id:
        return {
            "success": False,
            "message": "user_id חסר",
        }

    try:
        recording = get_latest_user_recording(
            conn,
            user_id=user_id,
            record_type="name",
        )
    except psycopg.Error:
        return {
            "success": False,
            "message": "שגיאה בשליפת הקלטת שם",
        }

    if not recording:
        return {
            "success": True,
            "exists": False,
            "file_path": "",
        }

    return {
        "success": True,
        "exists": True,
        "file_path": recording.get("file_path") or "",
    }


def save_user_name_recording(conn, *, user_id: str, file_path: str) -> dict:
    user_id = (user_id or "").strip()
    file_path = (file_path or "").strip()

    if not user_id or not file_path:
        return {"success": False, "message": "חסר user_id או file_path"}

    try:
        recording = create_user_recording(
            conn,
            user_id=user_id,
            record_type="name",
            file_path=file_path,
        )
        conn.commit()
        return {"success": True, "recording": dict(recording)}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": "שגיאה בשמירת הקלטה", "error": str(e)}
