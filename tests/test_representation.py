"""Regression checks for caption representation construction."""

from __future__ import annotations

import pytest

from src.core.representation import build_embedding_source_text, normalize_representation_mode
from src.core.schemas import CaptionRecord


def _caption_record() -> CaptionRecord:
    """Create a representative structured caption record for unit tests."""
    return CaptionRecord(
        image_id="visual_storytelling_mobile",
        image_path="/tmp/visual_storytelling_mobile.png",
        caption_text="A vertical beige mobile UI waits for an image sequence.",
        image_type="mobile UI screenshot",
        main_subject="image sequence generation interface",
        visible_objects=["phone frame", "placeholder panel"],
        visible_text=["AWAITING IMAGE SEQUENCE", "Your story will appear here"],
        layout_blocks=["top title bar", "central placeholder card", "bottom action area"],
        distinctive_cues=["beige background", "vertical screen", "empty story preview"],
        retrieval_text="image type: mobile UI screenshot",
    )


def test_caption_only_representation_uses_free_caption() -> None:
    """The control mode should embed only the free-form caption text."""
    record = _caption_record()

    source_text = build_embedding_source_text(record, representation_mode="caption_only")

    assert source_text == record.caption_text


def test_candidate_representation_combines_caption_with_selected_fields() -> None:
    """The candidate baseline should include caption text and selected structured cues."""
    source_text = build_embedding_source_text(
        _caption_record(),
        representation_mode="caption_plus_selected_structured",
    )

    assert source_text.startswith("caption: A vertical beige mobile UI")
    assert "visible text: AWAITING IMAGE SEQUENCE | Your story will appear here" in source_text
    assert "layout blocks: top title bar | central placeholder card | bottom action area" in source_text
    assert "component cue: phone frame" in source_text
    assert 'exact text cue: "AWAITING IMAGE SEQUENCE"' in source_text
    assert "visible objects:" not in source_text


def test_candidate_representation_adds_named_entity_and_split_text_cues() -> None:
    """Candidate mode should surface person-like names and shorter exact text anchors."""
    record = CaptionRecord(
        image_id="history_chat_einstein_philosophical",
        image_path="/tmp/history_chat_einstein_philosophical.png",
        caption_text="Historical salon screenshot featuring Albert Einstein in a reflective conversation.",
        image_type="UI screenshot",
        main_subject="Albert Einstein dialogue interface",
        visible_objects=["persona dossier card", "transcript panel"],
        visible_text=[
            "Albert Einstein",
            (
                "CURRENT PERSPECTIVE Albert Einstein . . . "
                "What matters most in discovery? . . . "
                "Would you trust modern AI without caution?"
            ),
        ],
        layout_blocks=["sidebar", "transcript panel"],
        distinctive_cues=["soft beige palette"],
        retrieval_text="",
    )

    source_text = build_embedding_source_text(record, representation_mode="caption_plus_selected_structured")

    assert "named entity cue: Albert Einstein" in source_text
    assert "named entity cue: Einstein" in source_text
    assert 'exact text cue: "What matters most in discovery?"' in source_text
    assert 'exact text cue: "Would you trust modern AI without caution?"' in source_text


def test_legacy_representation_mode_normalizes_to_current_candidate() -> None:
    """Legacy experiment names should keep loading without changing stored artifacts."""
    assert normalize_representation_mode("caption_plus_structured") == "caption_plus_selected_structured"


def test_unsupported_representation_mode_raises_clean_error() -> None:
    """Unsupported representation modes should fail before embedding work starts."""
    with pytest.raises(ValueError, match="Unsupported representation mode"):
        normalize_representation_mode("unknown_mode")
