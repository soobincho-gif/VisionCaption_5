"""Regression checks for benchmark-agnostic rerank ablation summaries."""

from __future__ import annotations

from src.pipelines.evaluate_top3_rerank_ablation import _build_residual_query_outcomes


def test_residual_query_outcomes_skips_missing_hard_benchmark_queries() -> None:
    """Broader benchmarks should not fail just because the hard residual IDs are absent."""
    outcomes = _build_residual_query_outcomes(
        [
            {
                "query_id": "q_other",
                "query": "other query",
                "activated": False,
                "activation_reasons": [],
                "corrected": False,
                "regression": False,
                "before_top_result": {"image_id": "wrong"},
                "after_top_result": {"image_id": "wrong"},
                "candidate_logs": [],
            }
        ]
    )

    assert outcomes == {}
