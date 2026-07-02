from __future__ import annotations

from datetime import datetime
from typing import Any

from psycopg.rows import dict_row


def cancel_active_challenges(
        conn,
        *,
        user_id: str,
        purpose: str = "reset_secret",
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE verification_challenges
            SET used_at = now()
            WHERE user_id = %s
              AND purpose = %s
              AND used_at IS NULL
            """,
            (user_id, purpose),
        )


def create_challenge(
        conn,
        *,
        user_id: str,
        user_phone_id: str,
        purpose: str,
        channel: str,
        code_hash: str,
        expires_at: datetime,
        provider: str | None = None,
        provider_call_id: str | None = None,
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO verification_challenges (
                user_id,
                user_phone_id,
                purpose,
                channel,
                method,
                code_hash,
                expires_at,
                provider,
                provider_call_id
            )
            VALUES (%s, %s, %s, %s, 'flash_call', %s, %s, %s, %s)
            RETURNING *
            """,
            (
                user_id,
                user_phone_id,
                purpose,
                channel,
                code_hash,
                expires_at,
                provider,
                provider_call_id,
            ),
        )
        return cur.fetchone()


def get_active_challenge_by_id(
        conn,
        *,
        challenge_id: str,
) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT *
            FROM verification_challenges
            WHERE id = %s
              AND used_at IS NULL
              AND expires_at > now()
            LIMIT 1
            """,
            (challenge_id,),
        )
        return cur.fetchone()


def increment_challenge_attempts(
        conn,
        *,
        challenge_id: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE verification_challenges
            SET attempts = attempts + 1
            WHERE id = %s
            """,
            (challenge_id,),
        )


def mark_challenge_used(
        conn,
        *,
        challenge_id: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE verification_challenges
            SET used_at = now()
            WHERE id = %s
            """,
            (challenge_id,),
        )


def mark_challenge_verified(conn, *, challenge_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE verification_challenges
            SET verified_at = now()
            WHERE id = %s
            """,
            (challenge_id,),
        )
