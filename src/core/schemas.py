"""Shared Pydantic schemas that define the project's storage and pipeline contracts."""

from __future__ import annotations

from datetime import datetime, timezone
import re

from pydantic import BaseModel, Field, field_validator

from src.core.types import CaptionRepresentationMode, ImageId, Vector


def utc_now() -> datetime:
    """Return a timezone-aware timestamp for persisted records."""
    return datetime.now(timezone.utc)


def _normalize_optional_text(value: object) -> str | None:
    """Normalize optional free-text fields into trimmed strings or None."""
    if value is None:
        return None

    normalized_value = str(value).strip()
    if not normalized_value:
        return None

    return normalized_value


def _normalize_string_list(value: object) -> list[str]:
    """Normalize provider output into a clean list of strings."""
    if value is None:
        return []

    if isinstance(value, str):
        normalized_value = value.strip()
        if not normalized_value:
            return []
        candidate_items = re.split(r"[\n;]+", normalized_value)
    elif isinstance(value, (list, tuple, set)):
        candidate_items = [str(item) for item in value]
    else:
        candidate_items = [str(value)]

    cleaned_items: list[str] = []
    seen_items: set[str] = set()
    for item in candidate_items:
        normalized_item = item.strip().strip("-").strip()
        if not normalized_item:
            continue
        dedupe_key = normalized_item.casefold()
        if dedupe_key in seen_items:
            continue
        seen_items.add(dedupe_key)
        cleaned_items.append(normalized_item)

    return cleaned_items


class CaptionContent(BaseModel):
    """Normalized caption fields returned by the vision service."""

    caption_text: str = Field(min_length=1, description="Two to four concise sentences for semantic retrieval.")
    image_type: str | None = Field(default=None, description="Short label such as photo, illustration, screenshot, dashboard, slide, or UI.")
    main_subject: str | None = Field(default=None, description="The main visible subject in one short phrase.")
    visible_objects: list[str] = Field(default_factory=list, max_length=10, description="Up to 10 distinctive visible objects or components.")
    visible_text: list[str] = Field(default_factory=list, max_length=14, description="Up to 14 short visible text snippets, labels, headings, or keywords.")
    layout_blocks: list[str] = Field(default_factory=list, max_length=8, description="Up to 8 layout blocks such as sidebar, card, panel, transcript, form, or footer.")
    distinctive_cues: list[str] = Field(default_factory=list, max_length=8, description="Up to 8 distinctive retrieval cues.")

    @field_validator("caption_text", mode="before")
    @classmethod
    def validate_caption_text(cls, value: object) -> str:
        """Require a non-empty caption string after trimming."""
        normalized_value = _normalize_optional_text(value)
        if not normalized_value:
            raise ValueError("caption_text is required.")
        return normalized_value

    @field_validator("image_type", "main_subject", mode="before")
    @classmethod
    def validate_optional_text_fields(cls, value: object) -> str | None:
        """Normalize optional text fields into trimmed strings."""
        return _normalize_optional_text(value)

    @field_validator("visible_objects", "visible_text", "layout_blocks", "distinctive_cues", mode="before")
    @classmethod
    def validate_list_fields(cls, value: object) -> list[str]:
        """Normalize structured list fields into clean lists of strings."""
        return _normalize_string_list(value)


class CaptionRecord(CaptionContent):
    """Stored caption data plus structured retrieval metadata for one image."""

    image_id: ImageId = Field(min_length=1)
    image_path: str = Field(min_length=1)
    retrieval_text: str = ""
    model_name: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("retrieval_text", mode="before")
    @classmethod
    def validate_retrieval_text(cls, value: object) -> str:
        """Keep retrieval_text as a trimmed string, defaulting to empty."""
        if value is None:
            return ""
        return str(value).strip()


class EmbeddingRecord(BaseModel):
    """Stored text embedding linked back to an image and its source caption."""

    image_id: ImageId = Field(min_length=1)
    source_text: str = Field(min_length=1)
    vector: Vector = Field(default_factory=list)
    representation_mode: CaptionRepresentationMode | None = None
    model_name: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class RetrievalResult(BaseModel):
    """Single ranked result returned by the search pipeline."""

    query_text: str = Field(min_length=1)
    image_id: ImageId = Field(min_length=1)
    image_path: str | None = None
    similarity_score: float = Field(ge=-1.0, le=1.0)
    rank: int = Field(ge=1)
    created_at: datetime = Field(default_factory=utc_now)
