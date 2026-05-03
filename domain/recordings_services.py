from __future__ import annotations

from typing import Any
import psycopg

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