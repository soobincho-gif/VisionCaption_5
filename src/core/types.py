"""Shared type aliases used to keep module boundaries readable."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, TypeAlias

ImageId: TypeAlias = str
Vector: TypeAlias = list[float]
FilePath: TypeAlias = str | Path
JsonDict: TypeAlias = dict[str, Any]
RankedCandidate: TypeAlias = tuple[ImageId, float]
CaptionRepresentationMode: TypeAlias = Literal[
    "caption_only",
    "structured_all_fields",
    "structured_selected_fields",
    "caption_plus_selected_structured",
    "structured_only",
    "caption_plus_structured",
]
