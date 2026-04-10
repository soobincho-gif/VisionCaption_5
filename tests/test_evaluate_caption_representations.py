"""Regression checks for representation-comparison evaluation summaries."""

from __future__ import annotations

from src.pipelines.evaluate_caption_representations import (
    FAILURE_BUCKETS,
    _build_failure_analysis,
    _build_rerank_judgment,
    _classify_failure_bucket,
)


def _query_case(
    tags: list[str],
    expected_image_id: str = "expected",
    top_image_id: str = "wrong",
    hard_negative_image_ids: list[str] | None = None,
) -> dict[str, object]:
    """Create a compact evaluated query case for bucket and rerank tests."""
    return {
        "query_id": "q_test",
        "query": "test query",
        "expected_image_ids": [expected_image_id],
        "tags": tags,
        "hard_negative_image_ids": hard_negative_image_ids or [top_image_id],
        "results": [
            {
                "image_id": top_image_id,
                "similarity_score": 0.8,
            },
            {
                "image_id": "near_miss",
                "similarity_score": 0.7,
            },
            {
                "image_id": expected_image_id,
                "similarity_score": 0.6,
            },
        ],
    }


def test_failure_bucket_priority_uses_fixed_report_categories() -> None:
    """Top-1 misses should collapse into the five report-facing failure buckets."""
    assert _classify_failure_bucket(_query_case(["ui_family_disambiguation"])) == "same-family UI confusion"
    assert _classify_failure_bucket(_query_case(["person_name", "visible_text"])) == "person-name confusion"
    assert _classify_failure_bucket(_query_case(["visible_text", "ui_family_disambiguation"])) == "visible-text confusion"
    assert _classify_failure_bucket(_query_case(["visible_text", "photo_scene"])) == "OCR/stylized text failure"
    assert _classify_failure_bucket(_query_case(["layout_structure"])) == "layout confusion"


def test_failure_analysis_always_reports_all_fixed_buckets() -> None:
    """Bucket counts should stay structurally stable even when some buckets are empty."""
    failure_analysis = _build_failure_analysis(
        [
            _query_case(["ui_family_disambiguation"]),
            _query_case(["person_name", "visible_text"]),
        ]
    )

    assert tuple(failure_analysis["bucket_counts"]) == FAILURE_BUCKETS
    assert failure_analysis["bucket_counts"]["same-family UI confusion"] == 1
    assert failure_analysis["bucket_counts"]["person-name confusion"] == 1
    assert failure_analysis["bucket_counts"]["visible-text confusion"] == 0
    assert failure_analysis["bucket_counts"]["OCR/stylized text failure"] == 0
    assert failure_analysis["bucket_counts"]["layout confusion"] == 0


def test_rerank_judgment_records_signal_without_recommending_implementation() -> None:
    """Rerank readiness is a judgment artifact, not a reranker implementation switch."""
    rerank_judgment = _build_rerank_judgment([_query_case(["visible_text", "ui_family_disambiguation"])])

    assert rerank_judgment["rerank_signal_present"] is True
    assert rerank_judgment["should_implement_lightweight_rerank_now"] is False
    assert rerank_judgment["recommendation"] == "defer_rerank_until_representation_fidelity_pass"
