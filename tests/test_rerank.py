"""Regression checks for the deterministic top-3 rerank ablation."""

from __future__ import annotations

from src.core.rerank import DeterministicRerankWeights, rerank_top_results
from src.core.schemas import CaptionRecord


def _result(image_id: str, rank: int, similarity_score: float) -> dict[str, object]:
    """Create a compact retrieval-result dictionary for rerank tests."""
    return {
        "image_id": image_id,
        "image_path": f"/tmp/{image_id}.png",
        "similarity_score": similarity_score,
        "rank": rank,
    }


def test_rerank_uses_label_value_phrases_to_flip_reflective_opinion_query() -> None:
    """Label-value cues should beat a small original-score lead when the query names UI state."""
    caption_lookup = {
        "einstein_ai": CaptionRecord(
            image_id="einstein_ai",
            image_path="/tmp/einstein_ai.png",
            caption_text="Historical salon screen featuring Albert Einstein discussing AI today.",
            image_type="UI screenshot",
            main_subject="Albert Einstein dialogue interface",
            visible_objects=["latest pipeline result panel", "text input field"],
            visible_text=[
                "Albert Einstein",
                "QUESTION TYPE",
                "posthumous current events",
                "Answer Mode",
                "cautious historical projection",
            ],
            layout_blocks=["latest pipeline result panel"],
            distinctive_cues=["warm editorial tone"],
            retrieval_text="",
        ),
        "einstein_philosophical": CaptionRecord(
            image_id="einstein_philosophical",
            image_path="/tmp/einstein_philosophical.png",
            caption_text="Historical salon screen featuring Albert Einstein answering reflective questions.",
            image_type="UI screenshot",
            main_subject="Albert Einstein conversational interface",
            visible_objects=["latest pipeline result panel", "text input field"],
            visible_text=[
                "Albert Einstein",
                "Question Type",
                "philosophical",
                "Answer Mode",
                "reflective opinion",
            ],
            layout_blocks=["latest pipeline result panel"],
            distinctive_cues=["warm editorial tone"],
            retrieval_text="",
        ),
    }

    rerank_output = rerank_top_results(
        query_text="Einstein historical salon screen with question type philosophical and answer mode reflective opinion",
        ranked_results=[
            _result("einstein_ai", rank=1, similarity_score=0.58),
            _result("einstein_philosophical", rank=2, similarity_score=0.56),
        ],
        caption_lookup=caption_lookup,
        top_n=3,
    )

    assert rerank_output["activated"] is True
    assert "label_value_phrase_overlap" in rerank_output["activation_reasons"]
    assert rerank_output["reranked_results"][0]["image_id"] == "einstein_philosophical"


def test_rerank_uses_component_cues_to_flip_slider_query() -> None:
    """UI component overlap should separate slider-heavy dashboard queries from mobile siblings."""
    caption_lookup = {
        "dashboard": CaptionRecord(
            image_id="dashboard",
            image_path="/tmp/dashboard.png",
            caption_text="Dark storytelling dashboard with controls and reports.",
            image_type="dashboard UI",
            main_subject="visual storytelling interface",
            visible_objects=[
                "sentiment radio buttons",
                "max sentences slider",
                "generate story button",
            ],
            visible_text=[
                "happy",
                "sad",
                "suspenseful",
                "Generate Story",
                "Max Sentences",
            ],
            layout_blocks=["control panel"],
            distinctive_cues=["dark theme"],
            retrieval_text="",
        ),
        "mobile": CaptionRecord(
            image_id="mobile",
            image_path="/tmp/mobile.png",
            caption_text="Mobile storytelling UI with upload controls.",
            image_type="mobile UI",
            main_subject="visual storytelling interface",
            visible_objects=[
                "sentiment radio buttons",
                "generate story button",
                "workspace status panel",
            ],
            visible_text=[
                "happy",
                "sad",
                "suspenseful",
                "Generate Story",
                "Max Sentences",
            ],
            layout_blocks=["mobile panel"],
            distinctive_cues=["light theme"],
            retrieval_text="",
        ),
    }

    rerank_output = rerank_top_results(
        query_text="desktop storytelling dashboard with happy sad suspenseful radio buttons, max sentences slider, and orange Generate Story button",
        ranked_results=[
            _result("mobile", rank=1, similarity_score=0.69),
            _result("dashboard", rank=2, similarity_score=0.67),
        ],
        caption_lookup=caption_lookup,
        top_n=3,
    )

    assert rerank_output["activated"] is True
    assert "component_cue_overlap" in rerank_output["activation_reasons"]
    assert rerank_output["reranked_results"][0]["image_id"] == "dashboard"


def test_rerank_preserves_original_order_without_supported_signals() -> None:
    """When the explicit rerank signals are absent, the original order should remain unchanged."""
    caption_lookup = {
        "cafe_phone_person": CaptionRecord(
            image_id="cafe_phone_person",
            image_path="/tmp/cafe_phone_person.jpeg",
            caption_text="A man sits in a cafe looking at his phone.",
            image_type="photo",
            main_subject="man in cafe",
            visible_objects=["phone", "table"],
            visible_text=[],
            layout_blocks=[],
            distinctive_cues=["warm cafe lighting"],
            retrieval_text="",
        ),
        "illustrated_couple_sofa": CaptionRecord(
            image_id="illustrated_couple_sofa",
            image_path="/tmp/illustrated_couple_sofa.jpeg",
            caption_text="A couple sits on a sofa in an illustration.",
            image_type="illustration",
            main_subject="couple on sofa",
            visible_objects=["phone", "window"],
            visible_text=[],
            layout_blocks=[],
            distinctive_cues=["drawn living room"],
            retrieval_text="",
        ),
    }

    rerank_output = rerank_top_results(
        query_text="man sitting in a cozy cafe looking at his phone",
        ranked_results=[
            _result("cafe_phone_person", rank=1, similarity_score=0.71),
            _result("illustrated_couple_sofa", rank=2, similarity_score=0.59),
        ],
        caption_lookup=caption_lookup,
        top_n=3,
    )

    assert rerank_output["activated"] is False
    assert rerank_output["reranked_results"][0]["image_id"] == "cafe_phone_person"
    assert rerank_output["reranked_results"][1]["image_id"] == "illustrated_couple_sofa"


def test_optional_question_paraphrase_overlap_flips_discovery_vs_ai_today_query() -> None:
    """An opt-in paraphrase cue should separate discovery/imagination from the generic AI-today prompt."""
    caption_lookup = {
        "einstein_ai": CaptionRecord(
            image_id="einstein_ai",
            image_path="/tmp/einstein_ai.png",
            caption_text="Historical salon screen featuring Albert Einstein discussing AI today.",
            image_type="UI screenshot",
            main_subject="Albert Einstein dialogue interface",
            visible_objects=["latest pipeline result panel", "text input field"],
            visible_text=[
                "Albert Einstein",
                "What do you think about AI today?",
            ],
            layout_blocks=["latest pipeline result panel"],
            distinctive_cues=["warm editorial tone"],
            retrieval_text="",
        ),
        "einstein_philosophical": CaptionRecord(
            image_id="einstein_philosophical",
            image_path="/tmp/einstein_philosophical.png",
            caption_text="Historical salon screen featuring Albert Einstein answering reflective questions.",
            image_type="UI screenshot",
            main_subject="Albert Einstein conversational interface",
            visible_objects=["latest pipeline result panel", "text input field"],
            visible_text=[
                "Albert Einstein",
                "What matters more in discovery: logic or imagination?",
            ],
            layout_blocks=["latest pipeline result panel"],
            distinctive_cues=["warm editorial tone"],
            retrieval_text="",
        ),
    }

    rerank_output = rerank_top_results(
        query_text="beige editorial AI chat about imagination and discovery rather than AI today",
        ranked_results=[
            _result("einstein_ai", rank=1, similarity_score=0.53),
            _result("einstein_philosophical", rank=2, similarity_score=0.50),
        ],
        caption_lookup=caption_lookup,
        top_n=3,
        weights=DeterministicRerankWeights(question_paraphrase_overlap=0.25),
    )

    assert rerank_output["activated"] is True
    assert "question_paraphrase_overlap" in rerank_output["activation_reasons"]
    assert rerank_output["reranked_results"][0]["image_id"] == "einstein_philosophical"


def test_rerank_ignores_singleton_area_component_cue_for_cleopatra_answer_query() -> None:
    """A generic container word alone should not overturn an already-correct transcript match."""
    caption_lookup = {
        "cleopatra_diplomacy": CaptionRecord(
            image_id="cleopatra_diplomacy",
            image_path="/tmp/cleopatra_diplomacy.png",
            caption_text="Cleopatra chat interface with a detailed diplomatic answer.",
            image_type="UI screenshot",
            main_subject="Cleopatra dialogue interface",
            visible_objects=["text input field"],
            visible_text=[
                "Cleopatra",
                "Leadership",
                "Power",
                "Diplomacy",
            ],
            layout_blocks=["conversation panel"],
            distinctive_cues=["beige editorial tone"],
            retrieval_text="",
        ),
        "cleopatra_landing": CaptionRecord(
            image_id="cleopatra_landing",
            image_path="/tmp/cleopatra_landing.png",
            caption_text="Cleopatra landing page with starter content and transcript placeholder.",
            image_type="UI screenshot",
            main_subject="Cleopatra dialogue interface",
            visible_objects=["conversation transcript area", "text input bar"],
            visible_text=[
                "Cleopatra",
                "Leadership",
                "Power",
                "Diplomacy",
            ],
            layout_blocks=["transcript column"],
            distinctive_cues=["beige editorial tone"],
            retrieval_text="",
        ),
    }

    rerank_output = rerank_top_results(
        query_text=(
            "beige Cleopatra chat screen with detailed answer cards about leadership, "
            "diplomacy, and power plus a text input area"
        ),
        ranked_results=[
            _result("cleopatra_diplomacy", rank=1, similarity_score=0.6478),
            _result("cleopatra_landing", rank=2, similarity_score=0.6453),
        ],
        caption_lookup=caption_lookup,
        top_n=3,
    )

    candidate_logs = {candidate_log["image_id"]: candidate_log for candidate_log in rerank_output["candidate_logs"]}

    assert rerank_output["activated"] is True
    assert rerank_output["reranked_results"][0]["image_id"] == "cleopatra_diplomacy"
    assert candidate_logs["cleopatra_landing"]["feature_contributions"]["component_cue_overlap"]["raw_score"] == 0.5
    assert candidate_logs["cleopatra_landing"]["feature_contributions"]["component_cue_overlap"]["matched_terms"] == [
        "text input bar"
    ]
