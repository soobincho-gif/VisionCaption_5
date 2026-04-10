"""Regression checks for frozen experiment-setting packaging."""

from __future__ import annotations

from src.config.experiment_settings import (
    HARD_BEST_CAPTION_PLUS_SELECTED_STRUCTURED_TOP3_QPO025_V1,
    get_experiment_setting,
)


def test_best_hard_setting_is_registered_with_expected_weights() -> None:
    """The mixed sanity pipeline should resolve the frozen hard-benchmark winner by name."""
    setting = get_experiment_setting(HARD_BEST_CAPTION_PLUS_SELECTED_STRUCTURED_TOP3_QPO025_V1.name)

    assert setting.representation_mode == "caption_plus_selected_structured"
    assert setting.rerank_top_n == 3
    assert setting.rerank_weights.question_paraphrase_overlap == 0.25
    assert setting.singleton_low_signal_container_guard_enabled is True
    assert setting.promotion_status == "broader_default"
    assert setting.known_hard_benchmark_metrics["broader_default"]["recall_at_1"] == 1.0
