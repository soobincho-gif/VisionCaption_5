"""Helpers for turning caption metadata into deterministic retrieval-ready text."""

from __future__ import annotations

import re

from src.core.schemas import CaptionContent, CaptionRecord
from src.core.types import CaptionRepresentationMode

ALL_STRUCTURED_FIELDS: tuple[str, ...] = (
    "image_type",
    "main_subject",
    "visible_objects",
    "visible_text",
    "layout_blocks",
    "distinctive_cues",
)
SELECTED_STRUCTURED_FIELDS: tuple[str, ...] = (
    "image_type",
    "main_subject",
    "visible_text",
    "layout_blocks",
    "distinctive_cues",
)
SUPPORTED_REPRESENTATION_MODES: tuple[CaptionRepresentationMode, ...] = (
    "caption_only",
    "structured_all_fields",
    "structured_selected_fields",
    "caption_plus_selected_structured",
)
CONTROL_REPRESENTATION_MODE: CaptionRepresentationMode = "caption_only"
CANDIDATE_BASELINE_REPRESENTATION_MODE: CaptionRepresentationMode = "caption_plus_selected_structured"
INDEXING_REPRESENTATION_MODES: tuple[CaptionRepresentationMode, ...] = (
    CONTROL_REPRESENTATION_MODE,
    CANDIDATE_BASELINE_REPRESENTATION_MODE,
)
UI_LIKE_IMAGE_TYPE_KEYWORDS: tuple[str, ...] = ("ui", "screenshot", "dashboard", "slide")
VISIBLE_TEXT_SEPARATOR_PATTERN = re.compile(r"\s*(?:\n+|\|+|•|·|(?:\.\s*){2,}|…|;+)\s*")
VISIBLE_TEXT_SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
VISIBLE_TEXT_SECTION_PATTERN = re.compile(
    r"(?=\b(?:"
    r"Image \d+|Sequence Memory|Event Candidates|Unresolved Ambiguities|"
    r"Evaluation Report|Generator Compliance Scores|Flags / Warnings|Evaluator Summary|"
    r"CURRENT PERSPECTIVE|LATEST PIPELINE RESULT|Session summary|QUESTION TYPE|"
    r"Question type|Answer Mode|Verification pass"
    r")\b)"
)
NAME_LIKE_PATTERN = re.compile(r"\b(?:[A-Z][a-z]+|[IVXLCDM]+)(?:\s+(?:[A-Z][a-z]+|[IVXLCDM]+)){1,3}\b")
ENTITY_STOPWORDS: set[str] = {
    "active",
    "answer",
    "candidates",
    "current",
    "dashboard",
    "evaluation",
    "evaluator",
    "figure",
    "flags",
    "generate",
    "generated",
    "generator",
    "historical",
    "image",
    "images",
    "interface",
    "issues",
    "latest",
    "memory",
    "multi-turn",
    "none",
    "observations",
    "perspective",
    "persona",
    "pipeline",
    "question",
    "report",
    "result",
    "salon",
    "scene",
    "selection",
    "sentiment",
    "sequence",
    "session",
    "snapshot",
    "status",
    "story",
    "storytelling",
    "summary",
    "transcript",
    "verification",
    "verify",
    "visual",
    "warnings",
}
ROMAN_NUMERAL_PATTERN = re.compile(r"^[IVXLCDM]+$")


def _normalize_text(value: str | None) -> str:
    """Trim optional text values into a consistent empty-or-string form."""
    if value is None:
        return ""
    return value.strip()


def _normalize_items(values: list[str] | None) -> list[str]:
    """Trim list items and remove duplicates while preserving order."""
    if not values:
        return []

    cleaned_items: list[str] = []
    seen_items: set[str] = set()
    for value in values:
        normalized_value = _normalize_text(value)
        if not normalized_value:
            continue
        dedupe_key = normalized_value.casefold()
        if dedupe_key in seen_items:
            continue
        seen_items.add(dedupe_key)
        cleaned_items.append(normalized_value)

    return cleaned_items


def _append_unique(target: list[str], value: str) -> None:
    """Append one normalized text item when it is not already present."""
    normalized_value = _normalize_inline_whitespace(value)
    if not normalized_value:
        return

    dedupe_key = normalized_value.casefold()
    if any(existing.casefold() == dedupe_key for existing in target):
        return

    target.append(normalized_value)


def _normalize_inline_whitespace(value: str | None) -> str:
    """Collapse repeated whitespace inside a retrieval text fragment."""
    return " ".join(_normalize_text(value).split())


def _looks_like_interface(content: CaptionContent) -> bool:
    """Return whether the record resembles a screenshot-style interface."""
    image_type = _normalize_text(content.image_type).casefold()
    if any(keyword in image_type for keyword in UI_LIKE_IMAGE_TYPE_KEYWORDS):
        return True
    return bool(_normalize_items(content.layout_blocks))


def _split_visible_text_item(value: str) -> list[str]:
    """Recover shorter text snippets from OCR-like strings that collapsed many cues together."""
    fragments = [_normalize_inline_whitespace(value)]
    for pattern in (
        VISIBLE_TEXT_SEPARATOR_PATTERN,
        VISIBLE_TEXT_SENTENCE_PATTERN,
        VISIBLE_TEXT_SECTION_PATTERN,
    ):
        next_fragments: list[str] = []
        for fragment in fragments:
            if not fragment:
                continue

            split_fragments = [
                _normalize_inline_whitespace(piece.strip(" -|"))
                for piece in pattern.split(fragment)
                if _normalize_inline_whitespace(piece.strip(" -|"))
            ]
            if len(split_fragments) <= 1:
                next_fragments.append(fragment)
                continue

            next_fragments.extend(split_fragments)

        fragments = next_fragments

    return fragments


def _collect_exact_text_cues(content: CaptionContent) -> list[str]:
    """Build short visible-text anchors that preserve exact wording when possible."""
    prioritized_fragments: list[str] = []
    regular_fragments: list[str] = []
    for visible_text_item in _normalize_items(content.visible_text):
        fragments = _split_visible_text_item(visible_text_item)
        if len(fragments) > 1 or len(visible_text_item) > 80 or "?" in visible_text_item:
            prioritized_fragments.extend(fragments)
            continue
        regular_fragments.extend(fragments)

    exact_text_cues: list[str] = []
    for fragment in prioritized_fragments:
        if len(fragment) < 4:
            continue
        if not _is_high_signal_long_text_fragment(fragment):
            continue
        _append_unique(exact_text_cues, fragment)

    for fragment in regular_fragments:
        if len(fragment) < 4:
            continue
        if len(fragment) > 90 and "?" not in fragment:
            continue
        _append_unique(exact_text_cues, fragment)

    return exact_text_cues[:20]


def _is_high_signal_long_text_fragment(fragment: str) -> bool:
    """Keep only compact header-like or question-like snippets from overlong OCR blocks."""
    if "?" in fragment:
        return True
    if "." in fragment or "," in fragment:
        return False
    return len(fragment.split()) <= 8


def _build_entity_aliases(entity: str) -> list[str]:
    """Generate a few lightweight aliases for person-like named entities."""
    tokens = entity.split()
    aliases: list[str] = []
    if len(tokens) == 2:
        aliases.append(tokens[-1])
    elif len(tokens) >= 3 and ROMAN_NUMERAL_PATTERN.match(tokens[1]):
        aliases.append(" ".join(tokens[:2]))
        aliases.append(tokens[0])

    return aliases


def _collect_named_entity_cues(content: CaptionContent) -> list[str]:
    """Extract a small set of figure-name anchors from caption text and visible text."""
    named_entities: list[str] = []
    candidate_texts = [
        _normalize_text(content.main_subject),
        _normalize_text(content.caption_text),
    ]
    for candidate_text in candidate_texts:
        for match in NAME_LIKE_PATTERN.finditer(candidate_text):
            entity = _normalize_inline_whitespace(match.group(0))
            tokens = entity.split()
            if len(tokens) < 2:
                continue
            if any(token.casefold() in ENTITY_STOPWORDS for token in tokens):
                continue

            _append_unique(named_entities, entity)
            for alias in _build_entity_aliases(entity):
                _append_unique(named_entities, alias)

    return named_entities[:8]


def normalize_representation_mode(representation_mode: str) -> CaptionRepresentationMode:
    """Map legacy representation names onto the current comparison modes."""
    if representation_mode == "structured_only":
        return "structured_all_fields"
    if representation_mode == "caption_plus_structured":
        return "caption_plus_selected_structured"
    if representation_mode == "caption_only":
        return "caption_only"
    if representation_mode == "structured_all_fields":
        return "structured_all_fields"
    if representation_mode == "structured_selected_fields":
        return "structured_selected_fields"
    if representation_mode == "caption_plus_selected_structured":
        return "caption_plus_selected_structured"
    raise ValueError(f"Unsupported representation mode: {representation_mode}")


def build_structured_retrieval_text(
    content: CaptionContent,
    included_fields: tuple[str, ...] = ALL_STRUCTURED_FIELDS,
) -> str:
    """Flatten chosen structured caption fields into a deterministic retrieval artifact."""
    sections: list[str] = []

    image_type = _normalize_text(content.image_type)
    if "image_type" in included_fields and image_type:
        sections.append(f"image type: {image_type}")

    main_subject = _normalize_text(content.main_subject)
    if "main_subject" in included_fields and main_subject:
        sections.append(f"main subject: {main_subject}")

    visible_objects = _normalize_items(content.visible_objects)
    if "visible_objects" in included_fields and visible_objects:
        sections.append(f"visible objects: {', '.join(visible_objects)}")

    visible_text = _normalize_items(content.visible_text)
    if "visible_text" in included_fields and visible_text:
        sections.append(f"visible text: {' | '.join(visible_text)}")

    layout_blocks = _normalize_items(content.layout_blocks)
    if "layout_blocks" in included_fields and layout_blocks:
        sections.append(f"layout blocks: {' | '.join(layout_blocks)}")

    distinctive_cues = _normalize_items(content.distinctive_cues)
    if "distinctive_cues" in included_fields and distinctive_cues:
        sections.append(f"distinctive cues: {', '.join(distinctive_cues)}")

    return "\n".join(sections)


def build_selected_structured_retrieval_text(content: CaptionContent) -> str:
    """Flatten the smaller selected-field representation used for hard-case comparison."""
    return build_structured_retrieval_text(content, included_fields=SELECTED_STRUCTURED_FIELDS)


def build_candidate_baseline_retrieval_text(record: CaptionRecord) -> str:
    """Build the candidate representation with targeted fidelity cues for names and visible text."""
    sections: list[str] = []

    caption_text = _normalize_text(record.caption_text)
    if caption_text:
        sections.append(f"caption: {caption_text}")

    structured_selected_fields_text = build_selected_structured_retrieval_text(record)
    if structured_selected_fields_text:
        sections.append(structured_selected_fields_text)

    if _looks_like_interface(record):
        for visible_object in _normalize_items(record.visible_objects):
            sections.append(f"component cue: {visible_object}")

    for named_entity in _collect_named_entity_cues(record):
        sections.append(f"named entity cue: {named_entity}")

    for exact_text_cue in _collect_exact_text_cues(record):
        sections.append(f'exact text cue: "{exact_text_cue}"')

    return "\n".join(sections)


def build_embedding_source_text(
    record: CaptionRecord,
    representation_mode: CaptionRepresentationMode = "caption_only",
) -> str:
    """Return the text representation to embed for the requested mode."""
    normalized_mode = normalize_representation_mode(representation_mode)
    caption_text = _normalize_text(record.caption_text)
    structured_all_fields_text = _normalize_text(record.retrieval_text) or build_structured_retrieval_text(record)
    structured_selected_fields_text = build_selected_structured_retrieval_text(record)

    if normalized_mode == "caption_only":
        if not caption_text:
            raise ValueError(f"Caption record {record.image_id} does not contain caption_text.")
        return caption_text

    if normalized_mode == "structured_all_fields":
        if not structured_all_fields_text:
            raise ValueError(f"Caption record {record.image_id} does not contain structured retrieval_text.")
        return structured_all_fields_text

    if normalized_mode == "structured_selected_fields":
        if not structured_selected_fields_text:
            raise ValueError(f"Caption record {record.image_id} does not contain selected structured retrieval text.")
        return structured_selected_fields_text

    if normalized_mode == "caption_plus_selected_structured":
        candidate_text = build_candidate_baseline_retrieval_text(record)
        if candidate_text:
            return candidate_text
        raise ValueError(f"Caption record {record.image_id} does not contain any retrieval-ready text.")

    raise ValueError(f"Unsupported representation mode: {representation_mode}")
