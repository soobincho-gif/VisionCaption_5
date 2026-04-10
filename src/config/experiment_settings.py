"""Named frozen experiment settings for reproducible evaluation packaging."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from src.core.rerank import DEFAULT_DETERMINISTIC_RERANK_WEIGHTS, DeterministicRerankWeights
from src.core.types import CaptionRepresentationMode


@dataclass(frozen=True)
class FrozenExperimentSetting:
    """Record one named experiment configuration and its benchmark-backed context."""

    name: str
    description: str
    representation_mode: CaptionRepresentationMode
    rerank_top_n: int
    rerank_weights: DeterministicRerankWeights
    source_benchmark_path: Path
    known_hard_benchmark_metrics: dict[str, dict[str, Any]]
    promotion_status: Literal["optional", "broader_default"]
    promotion_note: str
    validation_caveat: str
    singleton_low_signal_container_guard_enabled: bool
    trusted_frozen_control_candidate_dir: Path | None = None


HARD_BEST_CAPTION_PLUS_SELECTED_STRUCTURED_TOP3_QPO025_V1 = FrozenExperimentSetting(
    name="hard_best_caption_plus_selected_structured_top3_qpo025_v1",
    description=(
        "Frozen hard-benchmark winner using caption_plus_selected_structured plus "
        "deterministic top-3 rerank with question_paraphrase_overlap=0.25."
    ),
    representation_mode="caption_plus_selected_structured",
    rerank_top_n=3,
    rerank_weights=DeterministicRerankWeights(
        exact_visible_text_overlap=DEFAULT_DETERMINISTIC_RERANK_WEIGHTS.exact_visible_text_overlap,
        named_entity_match=DEFAULT_DETERMINISTIC_RERANK_WEIGHTS.named_entity_match,
        label_value_phrase_overlap=DEFAULT_DETERMINISTIC_RERANK_WEIGHTS.label_value_phrase_overlap,
        component_cue_overlap=DEFAULT_DETERMINISTIC_RERANK_WEIGHTS.component_cue_overlap,
        question_paraphrase_overlap=0.25,
        original_similarity=DEFAULT_DETERMINISTIC_RERANK_WEIGHTS.original_similarity,
    ),
    source_benchmark_path=Path("data/samples/prompt_fidelity/benchmark.json"),
    known_hard_benchmark_metrics={
        "caption_only": {
            "recall_at_1": 0.6786,
            "recall_at_3": 1.0000,
            "hard_negative_confusion_count": 9,
        },
        "caption_plus_selected_structured": {
            "recall_at_1": 0.8571,
            "recall_at_3": 1.0000,
            "hard_negative_confusion_count": 4,
        },
        "broader_default": {
            "recall_at_1": 1.0000,
            "recall_at_3": 1.0000,
            "hard_negative_confusion_count": 0,
            "regression_count": 0,
        },
    },
    promotion_status="broader_default",
    promotion_note=(
        "Promoted as the broader evaluation default on 2026-04-10 after the trusted "
        "frozen-artifact replay validated caption_plus_selected_structured plus "
        "deterministic top-3 rerank with question_paraphrase_overlap=0.25 and the "
        "singleton low-signal container guard enabled."
    ),
    validation_caveat=(
        "Frozen-artifact replay over the trusted mixed-sanity control/candidate artifacts "
        "validated the broader default at Recall@1 = 1.0000 and Recall@3 = 1.0000 with "
        "no regressions. A full end-to-end rebuild is still pending because a network "
        "Connection error interrupted the embedding rebuild."
    ),
    singleton_low_signal_container_guard_enabled=True,
    trusted_frozen_control_candidate_dir=Path(
        "outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/"
        "mixed_sanity_v1/control_candidate"
    ),
)

EXPERIMENT_SETTINGS: dict[str, FrozenExperimentSetting] = {
    HARD_BEST_CAPTION_PLUS_SELECTED_STRUCTURED_TOP3_QPO025_V1.name:
    HARD_BEST_CAPTION_PLUS_SELECTED_STRUCTURED_TOP3_QPO025_V1,
}


def get_experiment_setting(name: str) -> FrozenExperimentSetting:
    """Return one frozen experiment setting by name."""
    try:
        return EXPERIMENT_SETTINGS[name]
    except KeyError as exc:
        available_names = ", ".join(sorted(EXPERIMENT_SETTINGS))
        raise KeyError(f"Unknown experiment setting '{name}'. Available settings: {available_names}") from exc
