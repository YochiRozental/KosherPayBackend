from __future__ import annotations

import os

import requests

YEMOT_API_BASE_URL = os.getenv("YEMOT_API_BASE_URL", "https://www.call2all.co.il/ym/api")
YEMOT_USERNAME = os.getenv("YEMOT_USERNAME")
YEMOT_PASSWORD = os.getenv("YEMOT_PASSWORD")


def _get_token() -> str:
    if not YEMOT_USERNAME or not YEMOT_PASSWORD:
        raise RuntimeError("Missing YEMOT_USERNAME or YEMOT_PASSWORD")

    return f"{YEMOT_USERNAME}:{YEMOT_PASSWORD}"


def send_flash_call(*, phone_number: str) -> dict:
    phone_number = (phone_number or "").strip()

    if not phone_number:
        raise ValueError("Missing phone number")

    response = requests.get(
        f"{YEMOT_API_BASE_URL}/RunTzintuk",
        params={
            "token": _get_token(),
            "callerId": "RAND",
            "TzintukTimeOut": 10,
            "phones": phone_number,
        },
        timeout=15,
    )

    response.raise_for_status()
    data = response.json()

    if data.get("responseStatus") != "OK":
        raise RuntimeError(f"Yemot RunTzintuk failed: {data}")

    verify_code = data.get("verifyCode")

    if not verify_code:
        raise RuntimeError(f"Yemot did not return verifyCode: {data}")

    return {
        "verify_code": str(verify_code),
        "provider_call_id": str(data.get("yemotCallId") or data.get("callId") or ""),
        "raw": data,
    }
