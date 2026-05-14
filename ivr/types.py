from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union


@dataclass(frozen=True)
class YemotFile:
    path: str


YemotMessage = Union[str, YemotFile, tuple[Literal["file"], str]]
