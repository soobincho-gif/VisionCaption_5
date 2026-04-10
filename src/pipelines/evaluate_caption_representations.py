"""Experiment pipeline for comparing caption representation modes on one benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from src.config.prompts import PROMPT_VARIANTS, CaptionPromptVariant
from src.config.settings import settings
from src.core.representation import (
    CANDIDATE_BASELINE_REPRESENTATION_MODE,
    CONTROL_REPRESENTATION_MODE,
    normalize_representation_mode,
)
from src.core.types import CaptionRepresentationMode
from src.pipelines.build_caption_index import run_caption_pipeline
from src.pipelines.build_embedding_index import run_embedding_pipeline
from src.pipelines.evaluation_utils import compute_recall_at_k, load_benchmark_definition, reset_file, serialize_results
from src.pipelines.search_images import search
from src.storage.caption_store import CaptionStore
from src.storage.embedding_store import EmbeddingStore

DEFAULT_BENCHMARK_PATH = Path("data/samples/prompt_fidelity/benchmark.json")
DEFAULT_EXPERIMENT_DIR = settings.eval_output_dir / "structured_representation"
DEFAULT_CONTROL_CANDIDATE_EXPERIMENT_DIR = settings.eval_output_dir / "control_candidate_baseline"
DEFAULT_PROMPT_VARIANT: CaptionPromptVariant = "structured_retrieval_v3"
REPRESENTATION_MODES: tuple[CaptionRepresentationMode, ...] = (
    "caption_only",
    "structured_all_fields",
    "structured_selected_fields",
    "caption_plus_selected_structured",
)
CONTROL_CANDIDATE_REPRESENTATION_MODES: tuple[CaptionRepresentationMode, ...] = (
    CONTROL_REPRESENTATION_MODE,
    CANDIDATE_BASELINE_REPRESENTATION_MODE,
)
UI_LIKE_CATEGORIES = {"dashboard", "mobile_ui", "app_ui"}
FAILURE_BUCKETS: tuple[str, ...] = (
    "same-family UI confusion",
    "person-name confusion",
    "visible-text confusion",
    "OCR/stylized text failure",
    "layout confusion",
)


def _build_image_metadata_lookup(benchmark: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map image IDs to their declared benchmark metadata."""
    return {
        image_case["image_id"]: image_case
        for image_case in benchmark["images"]
    }


def _query_top_result(query_case: dict[str, Any]) -> dict[str, Any] | None:
    """Return the top-ranked result for one evaluated query."""
    ranked_results = query_case["results"]
    return ranked_results[0] if ranked_results else None


def _query_second_result(query_case: dict[str, Any]) -> dict[str, Any] | None:
    """Return the second-ranked result for one evaluated query when available."""
    ranked_results = query_case["results"]
    return ranked_results[1] if len(ranked_results) > 1 else None


def _query_top1_correct(query_case: dict[str, Any]) -> bool:
    """Return whether top-1 matches the expected image set for one query."""
    top_result = _query_top_result(query_case)
    if top_result is None:
        return False
    return top_result["image_id"] in set(query_case["expected_image_ids"])


def _query_hit_at_k(query_case: dict[str, Any], k: int) -> bool:
    """Return whether any expected image appears in the top-k ranked results."""
    expected_image_ids = set(query_case["expected_image_ids"])
    ranked_image_ids = [item["image_id"] for item in query_case["results"][:k]]
    return any(image_id in expected_image_ids for image_id in ranked_image_ids)


def _query_top1_margin(query_case: dict[str, Any]) -> float | None:
    """Return the top-1 minus top-2 similarity margin when both exist."""
    top_result = _query_top_result(query_case)
    second_result = _query_second_result(query_case)
    if top_result is None or second_result is None:
        return None
    return top_result["similarity_score"] - second_result["similarity_score"]


def _classify_failure_bucket(query_case: dict[str, Any]) -> str:
    """Assign every top-1 miss to one of the fixed qualitative failure buckets."""
    tags = set(query_case.get("tags", []))
    if "person_name" in tags:
        return "person-name confusion"
    if (
        "visible_text" in tags
        and "ui_family_disambiguation" not in tags
        and ("photo_scene" in tags or "illustration_style" in tags)
    ):
        return "OCR/stylized text failure"
    if "visible_text" in tags:
        return "visible-text confusion"
    if "layout_structure" in tags:
        return "layout confusion"
    return "same-family UI confusion"


def _build_failure_analysis(results_by_query: list[dict[str, Any]]) -> dict[str, Any]:
    """Collect failure details plus bucket counts for qualitative review."""
    failures: list[dict[str, Any]] = []
    for query_case in results_by_query:
        if _query_top1_correct(query_case):
            continue

        ranked_results = query_case["results"]
        failures.append(
            {
                "query_id": query_case["query_id"],
                "query": query_case["query"],
                "expected_image_ids": query_case["expected_image_ids"],
                "tags": query_case.get("tags", []),
                "hard_negative_image_ids": query_case.get("hard_negative_image_ids", []),
                "error_bucket": _classify_failure_bucket(query_case),
                "top_results": ranked_results[:3],
            }
        )

    bucket_counts: dict[str, int] = {bucket: 0 for bucket in FAILURE_BUCKETS}
    for failure in failures:
        bucket = failure["error_bucket"]
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1

    return {
        "count": len(failures),
        "bucket_counts": bucket_counts,
        "items": failures,
    }


def _compute_mean_top1_margin(results_by_query: list[dict[str, Any]]) -> float:
    """Compute the mean top-1 margin across all queries that have top-2 results."""
    margins = [
        margin
        for query_case in results_by_query
        if (margin := _query_top1_margin(query_case)) is not None
    ]
    if not margins:
        return 0.0
    return sum(margins) / len(margins)


def _summarize_tag_specific_accuracy(results_by_query: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Compute recall and margin statistics grouped by query tag."""
    query_cases_by_tag: dict[str, list[dict[str, Any]]] = {}
    for query_case in results_by_query:
        for tag in query_case.get("tags", []):
            query_cases_by_tag.setdefault(tag, []).append(query_case)

    tag_summary: dict[str, dict[str, Any]] = {}
    for tag, tagged_queries in sorted(query_cases_by_tag.items()):
        tag_summary[tag] = {
            "query_count": len(tagged_queries),
            "recall_at_1": sum(1 for query_case in tagged_queries if _query_top1_correct(query_case)) / len(tagged_queries),
            "recall_at_3": compute_recall_at_k(tagged_queries, k=3),
            "mean_top1_margin": _compute_mean_top1_margin(tagged_queries),
        }

    return tag_summary


def _build_rerank_judgment(results_by_query: list[dict[str, Any]]) -> dict[str, Any]:
    """Record whether the current error shape argues for lightweight reranking."""
    top1_misses = [
        query_case
        for query_case in results_by_query
        if not _query_top1_correct(query_case)
    ]
    top3_rescued_misses = [
        query_case
        for query_case in top1_misses
        if _query_hit_at_k(query_case, k=3)
    ]
    top1_miss_count = len(top1_misses)
    top3_rescue_rate = (
        len(top3_rescued_misses) / top1_miss_count
        if top1_miss_count
        else 0.0
    )
    rerank_signal_present = bool(top1_misses) and top3_rescue_rate >= 0.5

    return {
        "recommendation": "defer_rerank_until_representation_fidelity_pass",
        "rerank_signal_present": rerank_signal_present,
        "should_implement_lightweight_rerank_now": False,
        "top1_miss_count": top1_miss_count,
        "top1_miss_with_expected_in_top3_count": len(top3_rescued_misses),
        "top1_miss_with_expected_in_top3_rate": top3_rescue_rate,
        "decision_rule": (
            "If representation fidelity improves and top-3 still contains the expected image "
            "while top-1 remains frequently wrong, add a lightweight rerank stage."
        ),
        "current_read": (
            "The top-3 rescue signal is worth tracking, but remaining errors are still treated "
            "as representation-fidelity failures before reranking work starts."
        ),
    }


def _summarize_family_confusion_accuracy(
    benchmark: dict[str, Any],
    results_by_query: list[dict[str, Any]],
) -> dict[str, Any]:
    """Measure top-1 accuracy on same-family disambiguation and hard-negative queries."""
    image_metadata_lookup = _build_image_metadata_lookup(benchmark)
    targeted_queries = [
        query_case
        for query_case in results_by_query
        if "ui_family_disambiguation" in set(query_case.get("tags", []))
    ]
    query_details: list[dict[str, Any]] = []
    for query_case in targeted_queries:
        expected_image_id = query_case["expected_image_ids"][0]
        top_result = _query_top_result(query_case)
        second_result = _query_second_result(query_case)
        hard_negative_ids = query_case.get("hard_negative_image_ids", [])
        query_details.append(
            {
                "query_id": query_case["query_id"],
                "query": query_case["query"],
                "tags": query_case.get("tags", []),
                "expected_image_id": expected_image_id,
                "expected_family": image_metadata_lookup.get(expected_image_id, {}).get("family"),
                "hard_negative_image_ids": hard_negative_ids,
                "top_result": top_result,
                "second_result": second_result,
                "top1_correct": _query_top1_correct(query_case),
                "top1_margin": _query_top1_margin(query_case),
                "confused_with_hard_negative": bool(top_result and top_result["image_id"] in set(hard_negative_ids)),
            }
        )

    return {
        "query_count": len(targeted_queries),
        "recall_at_1": (
            sum(1 for detail in query_details if detail["top1_correct"]) / len(query_details)
            if query_details
            else 0.0
        ),
        "recall_at_3": compute_recall_at_k(targeted_queries, k=3) if targeted_queries else 0.0,
        "mean_top1_margin": _compute_mean_top1_margin(targeted_queries),
        "hard_negative_confusion_count": sum(1 for detail in query_details if detail["confused_with_hard_negative"]),
        "query_details": query_details,
    }


def _build_mode_paths(experiment_dir: Path, representation_mode: CaptionRepresentationMode) -> dict[str, Path]:
    """Return the output paths for one representation-mode run."""
    mode_dir = experiment_dir / representation_mode
    return {
        "mode_dir": mode_dir,
        "embeddings": mode_dir / "embeddings.jsonl",
        "results": mode_dir / "results.json",
    }


def _normalize_mode_sequence(
    representation_modes: Sequence[str] | None,
) -> tuple[CaptionRepresentationMode, ...]:
    """Normalize and de-duplicate representation modes while preserving order."""
    raw_modes = representation_modes or REPRESENTATION_MODES
    normalized_modes: list[CaptionRepresentationMode] = []
    seen_modes: set[CaptionRepresentationMode] = set()
    for representation_mode in raw_modes:
        normalized_mode = normalize_representation_mode(representation_mode)
        if normalized_mode in seen_modes:
            continue
        normalized_modes.append(normalized_mode)
        seen_modes.add(normalized_mode)

    return tuple(normalized_modes)


def _summarize_reused_captions(
    benchmark: dict[str, Any],
    caption_store: CaptionStore,
) -> dict[str, Any]:
    """Validate and summarize a fixed caption store reused for a benchmark run."""
    caption_records = caption_store.load_all()
    expected_image_ids = {image_case["image_id"] for image_case in benchmark["images"]}
    available_image_ids = {record.image_id for record in caption_records}
    missing_image_ids = sorted(expected_image_ids - available_image_ids)
    extra_image_ids = sorted(available_image_ids - expected_image_ids)
    if missing_image_ids:
        raise RuntimeError(
            "Cannot reuse captions because benchmark image IDs are missing: "
            + ", ".join(missing_image_ids)
        )

    return {
        "status": "reused_existing_captions",
        "caption_output_path": str(caption_store.file_path),
        "captions_available": len(caption_records),
        "benchmark_image_count": len(expected_image_ids),
        "extra_caption_image_ids": extra_image_ids,
    }


def _ensure_non_empty_ranked_results(
    results_by_query: list[dict[str, Any]],
    *,
    representation_mode: CaptionRepresentationMode,
    embedding_output_path: Path,
) -> None:
    """Reject malformed evaluation runs before they can become all-zero reports."""
    empty_query_ids = [
        query_case["query_id"]
        for query_case in results_by_query
        if not query_case["results"]
    ]
    if not empty_query_ids:
        return

    empty_preview = ", ".join(empty_query_ids[:5])
    raise RuntimeError(
        "Evaluation aborted for representation mode "
        f"'{representation_mode}' because {len(empty_query_ids)} query result(s) were empty while reading "
        f"{embedding_output_path}. Refusing to write an all-zero report. Check whether the embedding artifact "
        "is complete or switch to the frozen-artifact replay path."
    )


def _build_control_candidate_summary(comparison: dict[str, Any]) -> dict[str, Any] | None:
    """Compare the fixed control and candidate modes when both are present."""
    mode_summaries = comparison["representation_modes"]
    if not all(mode in mode_summaries for mode in CONTROL_CANDIDATE_REPRESENTATION_MODES):
        return None

    control = mode_summaries[CONTROL_REPRESENTATION_MODE]
    candidate = mode_summaries[CANDIDATE_BASELINE_REPRESENTATION_MODE]
    control_buckets = control["qualitative_error_buckets"]["bucket_counts"]
    candidate_buckets = candidate["qualitative_error_buckets"]["bucket_counts"]

    return {
        "control_mode": CONTROL_REPRESENTATION_MODE,
        "candidate_mode": CANDIDATE_BASELINE_REPRESENTATION_MODE,
        "recall_at_1_delta": candidate["recall_at_1"] - control["recall_at_1"],
        "recall_at_3_delta": candidate["recall_at_3"] - control["recall_at_3"],
        "family_recall_at_1_delta": (
            candidate["family_confusion_accuracy"]["recall_at_1"]
            - control["family_confusion_accuracy"]["recall_at_1"]
        ),
        "hard_negative_confusion_delta": (
            candidate["family_confusion_accuracy"]["hard_negative_confusion_count"]
            - control["family_confusion_accuracy"]["hard_negative_confusion_count"]
        ),
        "failure_bucket_delta": {
            bucket: candidate_buckets.get(bucket, 0) - control_buckets.get(bucket, 0)
            for bucket in FAILURE_BUCKETS
        },
        "interpretation": (
            "caption_only remains the control. caption_plus_selected_structured is the "
            "candidate baseline because it improves hard-case separation without changing ranking logic."
        ),
    }


def run_representation_comparison(
    benchmark_path: Path | None = None,
    experiment_dir: Path | None = None,
    top_k: int = 3,
    prompt_variant: CaptionPromptVariant = DEFAULT_PROMPT_VARIANT,
    representation_modes: Sequence[str] | None = None,
    caption_path: Path | None = None,
    reuse_captions: bool = False,
    reuse_embeddings: bool = False,
) -> dict[str, Any]:
    """Compare caption-only, structured-only, and combined representations."""
    benchmark = load_benchmark_definition(benchmark_path or DEFAULT_BENCHMARK_PATH)
    image_dir = Path(benchmark["image_dir"])
    output_dir = experiment_dir or DEFAULT_EXPERIMENT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    mode_sequence = _normalize_mode_sequence(representation_modes)

    caption_path = caption_path or output_dir / "captions.jsonl"
    caption_store = CaptionStore(file_path=caption_path)
    if reuse_captions:
        caption_summary = _summarize_reused_captions(benchmark, caption_store)
    else:
        reset_file(caption_path)
        caption_summary = run_caption_pipeline(
            image_dir=image_dir,
            store=caption_store,
            prompt_variant=prompt_variant,
        )

    comparison: dict[str, Any] = {
        "benchmark_name": benchmark["name"],
        "prompt_variant": prompt_variant,
        "image_dir": str(image_dir),
        "caption_output_path": str(caption_path),
        "caption_reuse_enabled": reuse_captions,
        "embedding_reuse_enabled": reuse_embeddings,
        "execution_mode": "rebuild_based",
        "top_k": top_k,
        "image_count": len(benchmark["images"]),
        "query_count": len(benchmark["queries"]),
        "caption_summary": caption_summary,
        "representation_modes": {},
    }

    for representation_mode in mode_sequence:
        mode_paths = _build_mode_paths(output_dir, representation_mode)
        mode_paths["mode_dir"].mkdir(parents=True, exist_ok=True)
        if not reuse_embeddings:
            reset_file(mode_paths["embeddings"])
        reset_file(mode_paths["results"])

        embedding_store = EmbeddingStore(file_path=mode_paths["embeddings"])
        embedding_summary = run_embedding_pipeline(
            caption_store=caption_store,
            embedding_store=embedding_store,
            representation_mode=representation_mode,
            reuse_existing=reuse_embeddings,
            require_complete_coverage=True,
        )

        results_by_query: list[dict[str, Any]] = []
        for query_case in benchmark["queries"]:
            results = search(
                query=query_case["query"],
                top_k=top_k,
                caption_store=caption_store,
                embedding_store=embedding_store,
            )
            results_by_query.append(
                {
                    "query_id": query_case["id"],
                    "query": query_case["query"],
                    "expected_image_ids": query_case["expected_image_ids"],
                    "tags": query_case.get("tags", []),
                    "hard_negative_image_ids": query_case.get("hard_negative_image_ids", []),
                    "results": serialize_results(results),
                }
            )

        _ensure_non_empty_ranked_results(
            results_by_query,
            representation_mode=representation_mode,
            embedding_output_path=mode_paths["embeddings"],
        )

        mode_summary = {
            "embedding_summary": embedding_summary,
            "recall_at_1": compute_recall_at_k(results_by_query, k=1),
            "recall_at_3": compute_recall_at_k(results_by_query, k=min(3, top_k)),
            "mean_top1_margin": _compute_mean_top1_margin(results_by_query),
            "tag_specific_accuracy": _summarize_tag_specific_accuracy(results_by_query),
            "family_confusion_accuracy": _summarize_family_confusion_accuracy(benchmark, results_by_query),
            "qualitative_error_buckets": _build_failure_analysis(results_by_query),
            "rerank_judgment": _build_rerank_judgment(results_by_query),
            "queries": results_by_query,
        }
        comparison["representation_modes"][representation_mode] = mode_summary

        with mode_paths["results"].open("w", encoding="utf-8") as handle:
            json.dump(mode_summary, handle, indent=2, ensure_ascii=False)

    control_candidate_summary = _build_control_candidate_summary(comparison)
    if control_candidate_summary is not None:
        comparison["control_candidate_summary"] = control_candidate_summary

    comparison_path = output_dir / "comparison.json"
    with comparison_path.open("w", encoding="utf-8") as handle:
        json.dump(comparison, handle, indent=2, ensure_ascii=False)

    comparison["comparison_path"] = str(comparison_path)
    return comparison


def run_control_candidate_comparison(
    benchmark_path: Path | None = None,
    experiment_dir: Path | None = None,
    top_k: int = 3,
    prompt_variant: CaptionPromptVariant = DEFAULT_PROMPT_VARIANT,
    caption_path: Path | None = None,
    reuse_captions: bool = False,
    reuse_embeddings: bool = False,
) -> dict[str, Any]:
    """Run the fixed caption-only control against the selected-structured candidate."""
    return run_representation_comparison(
        benchmark_path=benchmark_path,
        experiment_dir=experiment_dir or DEFAULT_CONTROL_CANDIDATE_EXPERIMENT_DIR,
        top_k=top_k,
        prompt_variant=prompt_variant,
        representation_modes=CONTROL_CANDIDATE_REPRESENTATION_MODES,
        caption_path=caption_path,
        reuse_captions=reuse_captions,
        reuse_embeddings=reuse_embeddings,
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for representation comparison experiments."""
    parser = argparse.ArgumentParser(description="Compare caption representation modes on a retrieval benchmark.")
    parser.add_argument(
        "--comparison-scope",
        choices=("control_candidate", "all"),
        default="control_candidate",
        help="Run only the fixed control/candidate pair or all representation modes.",
    )
    parser.add_argument(
        "--benchmark-path",
        type=Path,
        default=DEFAULT_BENCHMARK_PATH,
        help="Benchmark JSON definition to evaluate.",
    )
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=None,
        help="Directory where regenerated embeddings and retrieval results should be written.",
    )
    parser.add_argument(
        "--caption-path",
        type=Path,
        default=None,
        help="Caption JSONL path to write or reuse for this benchmark run.",
    )
    parser.add_argument(
        "--reuse-captions",
        action="store_true",
        help="Reuse --caption-path instead of regenerating captions.",
    )
    parser.add_argument(
        "--reuse-embeddings",
        action="store_true",
        help="Reuse existing embedding JSONL artifacts when they already cover the benchmark images.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of ranked retrieval results to keep per query.",
    )
    parser.add_argument(
        "--prompt-variant",
        choices=tuple(PROMPT_VARIANTS),
        default=DEFAULT_PROMPT_VARIANT,
        help="Caption prompt variant to use when captions are regenerated.",
    )
    return parser


def _build_cli_summary(comparison: dict[str, Any]) -> dict[str, Any]:
    """Return a compact CLI summary without printing every query result."""
    return {
        "benchmark_name": comparison["benchmark_name"],
        "comparison_path": comparison["comparison_path"],
        "caption_output_path": comparison["caption_output_path"],
        "caption_reuse_enabled": comparison["caption_reuse_enabled"],
        "embedding_reuse_enabled": comparison["embedding_reuse_enabled"],
        "execution_mode": comparison["execution_mode"],
        "top_k": comparison["top_k"],
        "representation_modes": {
            mode: {
                "recall_at_1": summary["recall_at_1"],
                "recall_at_3": summary["recall_at_3"],
                "hard_negative_confusion_count": summary["family_confusion_accuracy"]["hard_negative_confusion_count"],
                "failure_bucket_counts": summary["qualitative_error_buckets"]["bucket_counts"],
                "rerank_recommendation": summary["rerank_judgment"]["recommendation"],
            }
            for mode, summary in comparison["representation_modes"].items()
        },
        "control_candidate_summary": comparison.get("control_candidate_summary"),
    }


def main() -> int:
    """Run the requested representation comparison and print a compact summary."""
    parser = build_parser()
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be at least 1.")
    if args.reuse_captions and args.caption_path is None:
        parser.error("--reuse-captions requires --caption-path.")

    if args.comparison_scope == "control_candidate":
        comparison = run_control_candidate_comparison(
            benchmark_path=args.benchmark_path,
            experiment_dir=args.experiment_dir,
            top_k=args.top_k,
            prompt_variant=args.prompt_variant,
            caption_path=args.caption_path,
            reuse_captions=args.reuse_captions,
            reuse_embeddings=args.reuse_embeddings,
        )
    else:
        comparison = run_representation_comparison(
            benchmark_path=args.benchmark_path,
            experiment_dir=args.experiment_dir,
            top_k=args.top_k,
            prompt_variant=args.prompt_variant,
            caption_path=args.caption_path,
            reuse_captions=args.reuse_captions,
            reuse_embeddings=args.reuse_embeddings,
        )

    print(json.dumps(_build_cli_summary(comparison), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
