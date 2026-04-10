"""Regression checks for mixed sanity report helpers."""

from __future__ import annotations

import json

from src.pipelines.evaluate_mixed_sanity import (
    _load_control_candidate_comparison_from_frozen_artifacts,
    _build_outcome_delta,
    _build_recommendation,
    _normalize_query_cases,
)


def _query_case(query_id: str, *, expected_image_id: str, top_image_id: str) -> dict[str, object]:
    """Create a compact normalized query record."""
    return {
        "query_id": query_id,
        "query": f"query for {query_id}",
        "expected_image_ids": [expected_image_id],
        "results": [
            {
                "image_id": top_image_id,
                "similarity_score": 0.8,
            },
            {
                "image_id": expected_image_id,
                "similarity_score": 0.7,
            },
        ],
    }


def test_outcome_delta_separates_improvements_from_regressions() -> None:
    """Pairwise outcome comparisons should track correctness flips in both directions."""
    metadata_lookup = {
        "q_helped": {"slice": "hard_ui"},
        "q_hurt": {"slice": "normal_ui"},
    }

    delta = _build_outcome_delta(
        before_queries=[
            _query_case("q_helped", expected_image_id="expected_a", top_image_id="wrong"),
            _query_case("q_hurt", expected_image_id="expected_b", top_image_id="expected_b"),
        ],
        after_queries=[
            _query_case("q_helped", expected_image_id="expected_a", top_image_id="expected_a"),
            _query_case("q_hurt", expected_image_id="expected_b", top_image_id="wrong"),
        ],
        query_metadata_lookup=metadata_lookup,
    )

    assert [item["query_id"] for item in delta["improvements"]] == ["q_helped"]
    assert [item["query_id"] for item in delta["regressions"]] == ["q_hurt"]


def test_recommendation_promotes_only_when_broader_gain_is_regression_free() -> None:
    """Promotion should require an improvement over the frozen candidate with no new regressions."""
    recommendation = _build_recommendation(
        candidate_summary={"recall_at_1": 0.80},
        rerank_with_paraphrase_summary={"recall_at_1": 0.90},
        best_vs_candidate_delta={"improvements": [{"query_id": "q1"}], "regressions": []},
        paraphrase_delta={"improvements": [{"query_id": "q1"}], "regressions": []},
    )
    keep_optional = _build_recommendation(
        candidate_summary={"recall_at_1": 0.80},
        rerank_with_paraphrase_summary={"recall_at_1": 0.90},
        best_vs_candidate_delta={"improvements": [{"query_id": "q1"}], "regressions": [{"query_id": "q2"}]},
        paraphrase_delta={"improvements": [{"query_id": "q1"}], "regressions": []},
    )

    assert recommendation["decision"] == "promote_to_broader_default"
    assert keep_optional["decision"] == "keep_optional"


def test_normalize_query_cases_prefers_reranked_results_when_present() -> None:
    """Rerank outputs should normalize without requiring a representation-style results field."""
    normalized_queries = _normalize_query_cases(
        [
            {
                "query_id": "q1",
                "query": "query 1",
                "expected_image_ids": ["expected"],
                "tags": ["paraphrase"],
                "hard_negative_image_ids": ["wrong"],
                "reranked_results": [{"image_id": "expected", "similarity_score": 0.8}],
            }
        ]
    )

    assert normalized_queries[0]["results"][0]["image_id"] == "expected"


def test_frozen_control_candidate_replay_loads_valid_artifacts(tmp_path) -> None:
    """Offline replay should load trusted frozen control/candidate artifacts without rebuilding."""
    benchmark = {
        "name": "mini_mixed_benchmark",
        "image_dir": str(tmp_path / "images"),
        "images": [
            {"image_id": "img_a"},
            {"image_id": "img_b"},
        ],
        "queries": [
            {
                "id": "q1",
                "query": "find image a",
                "expected_image_ids": ["img_a"],
            }
        ],
    }
    caption_path = tmp_path / "captions.jsonl"
    caption_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "image_id": "img_a",
                        "image_path": str(tmp_path / "images" / "img_a.png"),
                        "caption_text": "caption a",
                        "visible_objects": [],
                        "visible_text": [],
                        "layout_blocks": [],
                        "distinctive_cues": [],
                    }
                ),
                json.dumps(
                    {
                        "image_id": "img_b",
                        "image_path": str(tmp_path / "images" / "img_b.png"),
                        "caption_text": "caption b",
                        "visible_objects": [],
                        "visible_text": [],
                        "layout_blocks": [],
                        "distinctive_cues": [],
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    frozen_dir = tmp_path / "control_candidate"
    for mode in ("caption_only", "caption_plus_selected_structured"):
        mode_dir = frozen_dir / mode
        mode_dir.mkdir(parents=True)
        (mode_dir / "results.json").write_text(
            json.dumps(
                {
                    "recall_at_1": 1.0 if mode == "caption_plus_selected_structured" else 0.0,
                    "recall_at_3": 1.0,
                    "family_confusion_accuracy": {
                        "recall_at_1": 1.0 if mode == "caption_plus_selected_structured" else 0.0,
                        "recall_at_3": 1.0,
                        "hard_negative_confusion_count": 0,
                    },
                    "qualitative_error_buckets": {
                        "bucket_counts": {
                            "same-family UI confusion": 0,
                            "person-name confusion": 0,
                            "visible-text confusion": 0,
                            "OCR/stylized text failure": 0,
                            "layout confusion": 0,
                        }
                    },
                    "rerank_judgment": {
                        "recommendation": "not_applicable",
                    },
                    "queries": [
                        {
                            "query_id": "q1",
                            "query": "find image a",
                            "expected_image_ids": ["img_a"],
                            "results": [
                                {
                                    "image_id": "img_a",
                                    "similarity_score": 0.9,
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    comparison = _load_control_candidate_comparison_from_frozen_artifacts(
        benchmark,
        caption_path=caption_path,
        frozen_control_candidate_dir=frozen_dir,
    )

    assert comparison["execution_mode"] == "frozen_artifact_replay_based"
    assert comparison["representation_modes"]["caption_plus_selected_structured"]["recall_at_1"] == 1.0
    assert comparison["control_candidate_summary"]["candidate_mode"] == "caption_plus_selected_structured"
