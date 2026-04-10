"""Prompt templates used by captioning and future retrieval-oriented metadata work."""

from __future__ import annotations

from typing import Literal

CaptionPromptVariant = Literal["baseline", "retrieval_oriented_v2", "structured_retrieval_v3"]

BASE_CAPTION_PROMPT = """
Write a short caption for semantic image retrieval.
Mention the visible subjects, the setting, and any notable visual context in 1 to 2 sentences.
Only describe what can reasonably be seen in the image.
""".strip()

RETRIEVAL_ORIENTED_CAPTION_PROMPT = """
Write a retrieval-oriented caption for a single image in 2 to 4 concise sentences.

Requirements:
- Start by identifying the image type when it is clear: photo, illustration, screenshot, dashboard, slide, UI, or mixed media.
- Describe the main subject and the surrounding scene or context.
- Include distinctive visible objects, animals, icons, widgets, charts, or interface components.
- If readable text is present, preserve short exact keywords, titles, labels, headings, or phrases that would help retrieval.
- For screenshot-, dashboard-, slide-, or UI-like images, describe the visible layout structure such as sidebars, panels, cards, menus, chat areas, or stacked sections.
- Mention unusual cues that would help search, such as lighting, color, posture, camera angle, interface state, or composition.
- Stay faithful to what is visible. Do not guess hidden intent, invisible content, or unreadable text.
""".strip()

STRUCTURED_RETRIEVAL_CAPTION_PROMPT = """
Analyze a single image for semantic image retrieval and return both a free-form caption and structured metadata.

Requirements:
- Stay faithful to what is actually visible.
- Preserve the image type when clear: photo, illustration, screenshot, dashboard, slide, UI, or mixed media.
- Preserve the main subject.
- Preserve distinctive visible objects, animals, interface components, icons, or props.
- Preserve short readable text, titles, labels, or keywords when they are clearly visible.
- For UI-like images, describe the visible screen structure using layout blocks such as sidebar, toolbar, cards, transcript panel, upload area, form section, or footer.
- Preserve distinctive cues such as lighting, color palette, camera angle, posture, interface state, composition, or unusual styling.
- Keep the metadata compact and retrieval-focused:
  - visible_objects: at most 10 short phrases
  - visible_text: at most 14 short snippets, prioritizing titles, labels, exact questions, and distinctive keywords
  - layout_blocks: at most 8 short phrases
  - distinctive_cues: at most 8 short phrases

Return only a valid JSON object with this exact shape:
{
  "caption_text": "2 to 4 concise sentences for semantic retrieval",
  "image_type": "short image type label or empty string",
  "main_subject": "main visible subject or empty string",
  "visible_objects": ["short object phrase"],
  "visible_text": ["short exact visible keyword or phrase"],
  "layout_blocks": ["short UI or layout block phrase"],
  "distinctive_cues": ["short distinctive cue phrase"]
}

Rules:
- Use empty string for `image_type` or `main_subject` when unclear.
- Use empty arrays for list fields when nothing reliable is visible.
- Do not use markdown fences.
- Do not invent unreadable text.
""".strip()

PROMPT_VARIANTS: dict[CaptionPromptVariant, str] = {
    "baseline": BASE_CAPTION_PROMPT,
    "retrieval_oriented_v2": RETRIEVAL_ORIENTED_CAPTION_PROMPT,
    "structured_retrieval_v3": STRUCTURED_RETRIEVAL_CAPTION_PROMPT,
}


def build_caption_prompt(prompt_variant: CaptionPromptVariant = "baseline") -> str:
    """Return the caption prompt for the requested prompt variant."""
    try:
        return PROMPT_VARIANTS[prompt_variant]
    except KeyError as exc:
        raise ValueError(f"Unsupported caption prompt variant: {prompt_variant}") from exc
