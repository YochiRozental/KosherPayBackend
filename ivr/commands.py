from __future__ import annotations

from typing import Union

from ivr.formatters import clean
from ivr.types import YemotFile, YemotMessage

_YEMOT_PREFIXES = ("f-", "t-", "s-", "date-", "dateH-", "z-", "m-", "n-", "a-", "d-")

BACK_VALUE = "BACK"
DEFAULT_IVR_TIMEOUT = 8
TIMEOUT_REPEAT_VALUE = "REPEAT"


def yemot_first_part(message: YemotMessage, *, clean_text: bool = True) -> str:
    """
    Builds the first part (id_list_message) for Yemot commands.
    - Plain text -> t-...
    - YemotFile / ("file", "...") -> f-...
    - If already prefixed (f-/t-/...) -> returned as-is
    """
    # tuple shorthand: ("file", "000")
    if isinstance(message, tuple):
        kind, data = message
        if kind != "file":
            raise ValueError(f"Unsupported tuple kind: {kind!r}")
        message = YemotFile(data)

    # YemotFile -> f-...
    if isinstance(message, YemotFile):
        p = (message.path or "").strip()
        if not p:
            raise ValueError("Empty YemotFile path")
        return p if p.startswith("f-") else f"f-{p}"

    # string -> maybe already prefixed; else t-...
    s = str(message)
    if s.startswith(_YEMOT_PREFIXES):
        return s

    s = clean(s) if clean_text else s
    return f"t-{s}"


def is_timeout_repeat(value: str | None) -> bool:
    return value == TIMEOUT_REPEAT_VALUE


def yemot_read(
        text: Union[YemotMessage, list[YemotMessage]],
        param: str,
        min_len: int,
        max_len: int,
        timeout: int = DEFAULT_IVR_TIMEOUT,
        read_type: str = "Digits",
        confirm: bool = True,
        playback: bool = True,
        read_none_ok: bool = False,
        none_value: str = "None",
) -> str:
    confirm_value = "yes" if confirm else "no"
    playback_value = "yes" if playback else "no"

    if isinstance(text, list):
        first_part = yemot_render_parts(text, clean_text=True)
    else:
        first_part = yemot_first_part(text, clean_text=True)

    fields = [""] * 15
    fields[0] = param
    fields[2] = str(max_len)
    fields[3] = str(min_len)
    fields[4] = str(timeout)
    fields[5] = read_type
    fields[6] = playback_value

    if read_none_ok:
        fields[11] = "Ok"
        fields[12] = none_value

    fields[14] = confirm_value

    second_part = ",".join(fields)
    return f"read={first_part}={second_part}"


def read_with_back(
        prompt: YemotMessage | list[YemotMessage],
        param: str,
        min_len: int,
        max_len: int,
        *,
        timeout: int = DEFAULT_IVR_TIMEOUT,
        read_type: str = "Digits",
        confirm: bool = True,
        playback: bool = True,
) -> str:
    return yemot_read(
        prompt,
        param,
        min_len,
        max_len,
        timeout=timeout,
        read_type=read_type,
        confirm=confirm,
        playback=playback,
        read_none_ok=True,
        none_value=TIMEOUT_REPEAT_VALUE,
    )


def yemot_menu(
        text: Union[YemotMessage, list[YemotMessage]],
        var: str,
        *,
        timeout: int = DEFAULT_IVR_TIMEOUT,
        options: str = "1.2.3",
        confirm: bool = False,
        read_none_ok: bool = False,
        none_value: str = "None",
) -> str:
    confirm_value = "yes" if confirm else "no"

    if isinstance(text, list):
        first_part = yemot_render_parts(text, clean_text=True)
    else:
        first_part = yemot_first_part(text, clean_text=True)

    fields = [""] * 15
    fields[0] = var
    fields[1] = "Digits"
    fields[2] = "1"
    fields[3] = "1"
    fields[4] = str(timeout)
    fields[5] = "No"
    fields[6] = "AskNo"
    fields[9] = options

    if read_none_ok:
        fields[11] = "Ok"
        fields[12] = none_value

    fields[14] = confirm_value

    second_part = ",".join(fields)
    return f"read={first_part}={second_part}"


def menu_with_back(
        text: YemotMessage | list[YemotMessage],
        var: str,
        *,
        timeout: int = DEFAULT_IVR_TIMEOUT,
        options: str = "1.2.3",
        confirm: bool = False,
) -> str:
    return yemot_menu(
        text,
        var,
        timeout=timeout,
        options=options,
        confirm=confirm,
        read_none_ok=True,
        none_value=TIMEOUT_REPEAT_VALUE,
    )


def is_back(value: str | None) -> bool:
    return value == BACK_VALUE


def yemot_say(message: YemotMessage, *, go_to_folder: str | None = None) -> str:
    """
    Unified 'id_list_message' builder (text or file).
    """
    base = f"id_list_message={yemot_first_part(message, clean_text=True)}"
    return f"{base}&go_to_folder={go_to_folder}" if go_to_folder else base


def yemot_say_parts(parts: list[YemotMessage], *, go_to_folder: str | None = None) -> str:
    """
    Say a sequence of parts (text/files) in order.
    IMPORTANT: Yemot separates id_list_message parts using '.' (dot), not ','.
    """
    joined = ".".join(yemot_first_part(p, clean_text=True) for p in parts)
    base = f"id_list_message={joined}"
    return f"{base}&go_to_folder={go_to_folder}" if go_to_folder else base


def yemot_render_parts(parts: list[YemotMessage], *, clean_text: bool = True) -> str:
    return ".".join(yemot_first_part(p, clean_text=clean_text) for p in parts)


def yemot_play(message: YemotMessage, *, go_to_folder: str | None = None) -> str:
    """
    Unified 'play' builder. Prefers playing files; if text passed, falls back to say.
    """
    first = yemot_first_part(message, clean_text=True)
    if not first.startswith("f-"):
        return yemot_say(message, go_to_folder=go_to_folder)
    base = f"play={first}"
    return f"{base}&go_to_folder={go_to_folder}" if go_to_folder else base


def yemot_record(
        text: YemotMessage | list[YemotMessage],
        param: str,
        *,
        folder: str,
        file_name: str | None = None,
        finish_on_hash_menu: bool = True,
        save_on_hangup: bool = True,
        append_to_existing: bool = False,
        min_seconds: int | None = None,
        max_seconds: int | None = None,
) -> str:
    if isinstance(text, list):
        first_part = yemot_render_parts(text, clean_text=True)
    else:
        first_part = yemot_first_part(text, clean_text=True)

    fields = [""] * 10
    fields[0] = param
    fields[2] = "record"
    fields[3] = folder
    fields[4] = file_name or ""
    fields[5] = "yes" if finish_on_hash_menu else "no"
    fields[6] = "yes" if save_on_hangup else "no"
    fields[7] = "yes" if append_to_existing else "no"

    if min_seconds is not None:
        fields[8] = str(min_seconds)

    if max_seconds is not None:
        fields[9] = str(max_seconds)

    second_part = ",".join(fields)
    return f"read={first_part}={second_part}"
