"""Run a deterministic top-3 rerank ablation on frozen benchmark results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.config.settings import settings
from src.core.rerank import (
    DEFAULT_DETERMINISTIC_RERANK_WEIGHTS,
    DeterministicRerankWeights,
    rerank_top_results,
)
from src.pipelines.evaluate_caption_representations import (
    DEFAULT_BENCHMARK_PATH,
    _build_failure_analysis,
    _compute_mean_top1_margin,
    _query_top1_correct,
    _summarize_family_confusion_accuracy,
    _summarize_tag_specific_accuracy,
)
from src.pipelines.evaluation_utils import compute_recall_at_k, load_benchmark_definition, reset_file
from src.storage.caption_store import CaptionStore

DEFAULT_SOURCE_EXPERIMENT_DIR = settings.eval_output_dir / "control_candidate_name_text_fidelity"
DEFAULT_SOURCE_CANDIDATE_RESULTS_PATH = (
    DEFAULT_SOURCE_EXPERIMENT_DIR / "caption_plus_selected_structured" / "results.json"
)
DEFAULT_SOURCE_CONTROL_RESULTS_PATH = DEFAULT_SOURCE_EXPERIMENT_DIR / "caption_only" / "results.json"
DEFAULT_CAPTION_PATH = settings.eval_output_dir / "structured_representation" / "captions.jsonl"
DEFAULT_OUTPUT_DIR = settings.eval_output_dir / "deterministic_top3_rerank_ablation"
PRIMARY_RERANK_FEATURES: tuple[str, ...] = (
    "exact_visible_text_overlap",
    "named_entity_match",
    "label_value_phrase_overlap",
    "component_cue_overlap",
    "question_paraphrase_overlap",
)
RERANK_FAILURE_ANALYSIS_BUCKETS: tuple[str, ...] = (
    "corrected_by_visible_text_overlap",
    "corrected_by_label_value_phrase_overlap",
    "corrected_by_entity_cue_overlap",
    "corrected_by_component_cue_overlap",
    "corrected_by_question_paraphrase_overlap",
    "still_unresolved",
)


def _load_results(path: Path) -> dict[str, Any]:
    """Load one stored experiment results artifact from disk."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_caption_lookup(caption_path: Path) -> dict[str, Any]:
    """Load caption records once for deterministic rerank feature extraction."""
    caption_store = CaptionStore(file_path=caption_path)
    return {
        record.image_id: record
        for record in caption_store.load_all()
    }


def _build_metrics_snapshot(benchmark: dict[str, Any], results_by_query: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute the report-facing metrics used in existing representation runs."""
    return {
        "recall_at_1": compute_recall_at_k(results_by_query, k=1),
        "recall_at_3": compute_recall_at_k(results_by_query, k=3),
        "mean_top1_margin": _compute_mean_top1_margin(results_by_query),
        "tag_specific_accuracy": _summarize_tag_specific_accuracy(results_by_query),
        "family_confusion_accuracy": _summarize_family_confusion_accuracy(benchmark, results_by_query),
        "qualitative_error_buckets": _build_failure_analysis(results_by_query),
    }


def _build_query_log(
    query_case: dict[str, Any],
    rerank_output: dict[str, Any],
) -> dict[str, Any]:
    """Combine one frozen query result with its reranked trace."""
    original_results = query_case["results"]
    reranked_results = rerank_output["reranked_results"]
    before_top_result = original_results[0] if original_results else None
    after_top_result = reranked_results[0] if reranked_results else None
    expected_image_ids = set(query_case["expected_image_ids"])
    corrected = bool(
        before_top_result
        and after_top_result
        and before_top_result["image_id"] not in expected_image_ids
        and after_top_result["image_id"] in expected_image_ids
    )
    regression = bool(
        before_top_result
        and after_top_result
        and before_top_result["image_id"] in expected_image_ids
        and after_top_result["image_id"] not in expected_image_ids
    )

    candidate_logs = []
    for candidate_log in rerank_output["candidate_logs"]:
        serialized_candidate_log = dict(candidate_log)
        serialized_candidate_log.pop("feature_bundle", None)
        candidate_logs.append(serialized_candidate_log)

    return {
        "query_id": query_case["query_id"],
        "query": query_case["query"],
        "expected_image_ids": query_case["expected_image_ids"],
        "tags": query_case.get("tags", []),
        "hard_negative_image_ids": query_case.get("hard_negative_image_ids", []),
        "activated": rerank_output["activated"],
        "activation_reasons": rerank_output["activation_reasons"],
        "corrected": corrected,
        "regression": regression,
        "before_top_result": before_top_result,
        "after_top_result": after_top_result,
        "original_results": original_results,
        "reranked_results": reranked_results,
        "candidate_logs": candidate_logs,
    }


def _extract_primary_rerank_driver(query_log: dict[str, Any]) -> str | None:
    """Attribute a correction to the strongest non-tie-break feature margin."""
    if not query_log["corrected"]:
        return None

    before_top_result = query_log["before_top_result"]
    after_top_result = query_log["after_top_result"]
    if before_top_result is None or after_top_result is None:
        return None

    candidate_logs = {
        candidate_log["image_id"]: candidate_log
        for candidate_log in query_log["candidate_logs"]
    }
    before_log = candidate_logs.get(before_top_result["image_id"])
    after_log = candidate_logs.get(after_top_result["image_id"])
    if before_log is None or after_log is None:
        return None

    feature_margin_by_name: dict[str, float] = {}
    for feature_name in PRIMARY_RERANK_FEATURES:
        feature_margin_by_name[feature_name] = (
            after_log["feature_contributions"][feature_name]["weighted_score"]
            - before_log["feature_contributions"][feature_name]["weighted_score"]
        )

    strongest_feature_name = max(feature_margin_by_name, key=feature_margin_by_name.get)
    if feature_margin_by_name[strongest_feature_name] <= 0:
        return None

    return strongest_feature_name


def _build_rerank_failure_analysis(query_logs: list[dict[str, Any]]) -> dict[str, Any]:
    """Bucket corrected and unresolved baseline misses by primary rerank evidence."""
    bucket_counts = {bucket: 0 for bucket in RERANK_FAILURE_ANALYSIS_BUCKETS}
    bucket_items = {bucket: [] for bucket in RERANK_FAILURE_ANALYSIS_BUCKETS}

    baseline_misses = [
        query_log
        for query_log in query_logs
        if query_log["before_top_result"] is not None
        and query_log["before_top_result"]["image_id"] not in set(query_log["expected_image_ids"])
    ]
    for query_log in baseline_misses:
        if not query_log["corrected"]:
            bucket_counts["still_unresolved"] += 1
            bucket_items["still_unresolved"].append(query_log["query_id"])
            continue

        primary_driver = _extract_primary_rerank_driver(query_log)
        if primary_driver == "exact_visible_text_overlap":
            bucket_name = "corrected_by_visible_text_overlap"
        elif primary_driver == "label_value_phrase_overlap":
            bucket_name = "corrected_by_label_value_phrase_overlap"
        elif primary_driver == "named_entity_match":
            bucket_name = "corrected_by_entity_cue_overlap"
        elif primary_driver == "component_cue_overlap":
            bucket_name = "corrected_by_component_cue_overlap"
        elif primary_driver == "question_paraphrase_overlap":
            bucket_name = "corrected_by_question_paraphrase_overlap"
        else:
            bucket_name = "still_unresolved"

        bucket_counts[bucket_name] += 1
        bucket_items[bucket_name].append(query_log["query_id"])

    return {
        "bucket_counts": bucket_counts,
        "bucket_items": bucket_items,
    }


def _build_residual_query_outcomes(query_logs: list[dict[str, Any]]) -> dict[str, Any]:
    """Return compact before/after outcomes for the known residual hard-benchmark misses when present."""
    tracked_query_ids = (
        "q010_dashboard_dark_panels",
        "q012_dashboard_slider_file_sizes",
        "q020_einstein_reflective_opinion",
        "q021_einstein_discovery_paraphrase",
    )
    outcomes: dict[str, Any] = {}
    for query_id in tracked_query_ids:
        query_log = next((query_log for query_log in query_logs if query_log["query_id"] == query_id), None)
        if query_log is None:
            continue
        outcomes[query_id] = {
            "query": query_log["query"],
            "activated": query_log["activated"],
            "activation_reasons": query_log["activation_reasons"],
            "corrected": query_log["corrected"],
            "regression": query_log["regression"],
            "before_top_image_id": (
                query_log["before_top_result"]["image_id"]
                if query_log["before_top_result"] is not None
                else None
            ),
            "after_top_image_id": (
                query_log["after_top_result"]["image_id"]
                if query_log["after_top_result"] is not None
                else None
            ),
            "primary_rerank_driver": _extract_primary_rerank_driver(query_log),
        }
    return outcomes


def _build_compact_summary(comparison: dict[str, Any]) -> dict[str, Any]:
    """Return a compact CLI-friendly summary."""
    return {
        "comparison_path": comparison["comparison_path"],
        "query_log_path": comparison["query_log_path"],
        "source_candidate_results_path": comparison["source_candidate_results_path"],
        "rerank_weights": comparison["rerank_weights"],
        "control_reference": {
            "recall_at_1": comparison["control_reference"]["recall_at_1"],
            "recall_at_3": comparison["control_reference"]["recall_at_3"],
            "hard_negative_confusion_count": comparison["control_reference"]["hard_negative_confusion_count"],
        },
        "candidate_before": {
            "recall_at_1": comparison["candidate_before"]["recall_at_1"],
            "recall_at_3": comparison["candidate_before"]["recall_at_3"],
            "hard_negative_confusion_count": comparison["candidate_before"]["hard_negative_confusion_count"],
        },
        "candidate_after": {
            "recall_at_1": comparison["candidate_after"]["recall_at_1"],
            "recall_at_3": comparison["candidate_after"]["recall_at_3"],
            "hard_negative_confusion_count": comparison["candidate_after"]["hard_negative_confusion_count"],
        },
        "residual_query_outcomes": comparison["residual_query_outcomes"],
        "regressions": comparison["regressions"],
        "rerank_failure_analysis": comparison["rerank_failure_analysis"]["bucket_counts"],
    }


def run_top3_rerank_ablation(
    benchmark_path: Path = DEFAULT_BENCHMARK_PATH,
    caption_path: Path = DEFAULT_CAPTION_PATH,
    source_candidate_results_path: Path = DEFAULT_SOURCE_CANDIDATE_RESULTS_PATH,
    source_control_results_path: Path = DEFAULT_SOURCE_CONTROL_RESULTS_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    weights: DeterministicRerankWeights = DEFAULT_DETERMINISTIC_RERANK_WEIGHTS,
) -> dict[str, Any]:
    """Rerank the frozen top-3 candidate results and compare before vs after."""
    benchmark = load_benchmark_definition(benchmark_path)
    caption_lookup = _build_caption_lookup(caption_path)
    source_candidate_results = _load_results(source_candidate_results_path)
    source_control_results = _load_results(source_control_results_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.json"
    comparison_path = output_dir / "comparison.json"
    query_log_path = output_dir / "query_logs.jsonl"
    reset_file(results_path)
    reset_file(comparison_path)
    reset_file(query_log_path)

    reranked_queries: list[dict[str, Any]] = []
    query_logs: list[dict[str, Any]] = []
    for query_case in source_candidate_results["queries"]:
        rerank_output = rerank_top_results(
            query_text=query_case["query"],
            ranked_results=query_case["results"],
            caption_lookup=caption_lookup,
            top_n=3,
            weights=weights,
        )
        reranked_queries.append(
            {
                "query_id": query_case["query_id"],
                "query": query_case["query"],
                "expected_image_ids": query_case["expected_image_ids"],
                "tags": query_case.get("tags", []),
                "hard_negative_image_ids": query_case.get("hard_negative_image_ids", []),
                "results": rerank_output["reranked_results"],
            }
        )
        query_logs.append(_build_query_log(query_case, rerank_output))

    before_metrics = _build_metrics_snapshot(benchmark, source_candidate_results["queries"])
    after_metrics = _build_metrics_snapshot(benchmark, reranked_queries)
    regressions = [query_log["query_id"] for query_log in query_logs if query_log["regression"]]
    corrected_queries = [query_log["query_id"] for query_log in query_logs if query_log["corrected"]]

    candidate_before = {
        "recall_at_1": before_metrics["recall_at_1"],
        "recall_at_3": before_metrics["recall_at_3"],
        "hard_negative_confusion_count": before_metrics["family_confusion_accuracy"]["hard_negative_confusion_count"],
        "failure_bucket_counts": before_metrics["qualitative_error_buckets"]["bucket_counts"],
    }
    candidate_after = {
        "recall_at_1": after_metrics["recall_at_1"],
        "recall_at_3": after_metrics["recall_at_3"],
        "hard_negative_confusion_count": after_metrics["family_confusion_accuracy"]["hard_negative_confusion_count"],
        "failure_bucket_counts": after_metrics["qualitative_error_buckets"]["bucket_counts"],
    }
    control_reference = {
        "recall_at_1": source_control_results["recall_at_1"],
        "recall_at_3": source_control_results["recall_at_3"],
        "hard_negative_confusion_count": source_control_results["family_confusion_accuracy"]["hard_negative_confusion_count"],
        "failure_bucket_counts": source_control_results["qualitative_error_buckets"]["bucket_counts"],
    }

    comparison = {
        "benchmark_name": benchmark["name"],
        "source_candidate_results_path": str(source_candidate_results_path),
        "source_control_results_path": str(source_control_results_path),
        "caption_path": str(caption_path),
        "rerank_weights": weights.as_dict(),
        "control_reference": control_reference,
        "candidate_before": candidate_before,
        "candidate_after": candidate_after,
        "candidate_delta": {
            "recall_at_1": candidate_after["recall_at_1"] - candidate_before["recall_at_1"],
            "recall_at_3": candidate_after["recall_at_3"] - candidate_before["recall_at_3"],
            "hard_negative_confusion_count": (
                candidate_after["hard_negative_confusion_count"] - candidate_before["hard_negative_confusion_count"]
            ),
        },
        "corrected_queries": corrected_queries,
        "regressions": regressions,
        "residual_query_outcomes": _build_residual_query_outcomes(query_logs),
        "rerank_failure_analysis": _build_rerank_failure_analysis(query_logs),
        "recommendation": (
            "keep_optional"
            if regressions or candidate_after["recall_at_1"] < 1.0
            else "consider_default_after_broader_validation"
        ),
    }

    results_payload = {
        "benchmark_name": benchmark["name"],
        "source_candidate_results_path": str(source_candidate_results_path),
        "source_control_results_path": str(source_control_results_path),
        "caption_path": str(caption_path),
        "rerank_weights": weights.as_dict(),
        "before_metrics": before_metrics,
        "after_metrics": after_metrics,
        "corrected_queries": corrected_queries,
        "regressions": regressions,
        "queries": query_logs,
    }

    with results_path.open("w", encoding="utf-8") as handle:
        json.dump(results_payload, handle, indent=2, ensure_ascii=False)
    with comparison_path.open("w", encoding="utf-8") as handle:
        json.dump(comparison, handle, indent=2, ensure_ascii=False)
    with query_log_path.open("w", encoding="utf-8") as handle:
        for query_log in query_logs:
            handle.write(json.dumps(query_log, ensure_ascii=False) + "\n")

    comparison["comparison_path"] = str(comparison_path)
    comparison["results_path"] = str(results_path)
    comparison["query_log_path"] = str(query_log_path)
    return comparison


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for the deterministic rerank ablation."""
    parser = argparse.ArgumentParser(description="Run a deterministic top-3 rerank ablation on frozen benchmark results.")
    parser.add_argument(
        "--benchmark-path",
        type=Path,
        default=DEFAULT_BENCHMARK_PATH,
        help="Benchmark JSON definition used for the original frozen run.",
    )
    parser.add_argument(
        "--caption-path",
        type=Path,
        default=DEFAULT_CAPTION_PATH,
        help="Caption JSONL path reused to extract rerank features.",
    )
    parser.add_argument(
        "--source-candidate-results-path",
        type=Path,
        default=DEFAULT_SOURCE_CANDIDATE_RESULTS_PATH,
        help="Frozen candidate results.json path whose top-3 outputs will be reranked.",
    )
    parser.add_argument(
        "--source-control-results-path",
        type=Path,
        default=DEFAULT_SOURCE_CONTROL_RESULTS_PATH,
        help="Frozen caption_only results.json path kept as the control reference.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where rerank ablation artifacts should be written.",
    )
    parser.add_argument(
        "--question-paraphrase-overlap-weight",
        type=float,
        default=DEFAULT_DETERMINISTIC_RERANK_WEIGHTS.question_paraphrase_overlap,
        help="Optional weight for question-like paraphrase overlap. Keep at 0.0 to preserve the current rerank behavior.",
    )
    return parser


def main() -> int:
    """Run the deterministic top-3 rerank ablation and print a compact summary."""
    parser = build_parser()
    args = parser.parse_args()
    comparison = run_top3_rerank_ablation(
        benchmark_path=args.benchmark_path,
        caption_path=args.caption_path,
        source_candidate_results_path=args.source_candidate_results_path,
        source_control_results_path=args.source_control_results_path,
        output_dir=args.output_dir,
        weights=DeterministicRerankWeights(
            exact_visible_text_overlap=DEFAULT_DETERMINISTIC_RERANK_WEIGHTS.exact_visible_text_overlap,
            named_entity_match=DEFAULT_DETERMINISTIC_RERANK_WEIGHTS.named_entity_match,
            label_value_phrase_overlap=DEFAULT_DETERMINISTIC_RERANK_WEIGHTS.label_value_phrase_overlap,
            component_cue_overlap=DEFAULT_DETERMINISTIC_RERANK_WEIGHTS.component_cue_overlap,
            question_paraphrase_overlap=args.question_paraphrase_overlap_weight,
            original_similarity=DEFAULT_DETERMINISTIC_RERANK_WEIGHTS.original_similarity,
        ),
    )
    print(json.dumps(_build_compact_summary(comparison), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
