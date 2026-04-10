"""Run the broader mixed sanity evaluation for the frozen best hard-benchmark setting."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
from typing import Any

from src.config.experiment_settings import (
    HARD_BEST_CAPTION_PLUS_SELECTED_STRUCTURED_TOP3_QPO025_V1,
    FrozenExperimentSetting,
    get_experiment_setting,
)
from src.config.settings import settings
from src.core.representation import CANDIDATE_BASELINE_REPRESENTATION_MODE, CONTROL_REPRESENTATION_MODE
from src.pipelines.evaluate_caption_representations import (
    _build_control_candidate_summary,
    run_control_candidate_comparison,
)
from src.pipelines.evaluate_top3_rerank_ablation import run_top3_rerank_ablation
from src.pipelines.evaluation_utils import compute_recall_at_k, load_benchmark_definition
from src.storage.caption_store import CaptionStore

DEFAULT_BENCHMARK_PATH = Path("data/samples/prompt_fidelity/benchmark_mixed_sanity_v1.json")
DEFAULT_EXPERIMENT_SETTING_NAME = HARD_BEST_CAPTION_PLUS_SELECTED_STRUCTURED_TOP3_QPO025_V1.name
DEFAULT_CAPTION_PATH = settings.eval_output_dir / "structured_representation" / "captions.jsonl"
DEFAULT_OUTPUT_DIR = settings.eval_output_dir / DEFAULT_EXPERIMENT_SETTING_NAME / "mixed_sanity_v1"
DEFAULT_ARTIFACT_MODE = "auto"


def _load_json(path: Path) -> dict[str, Any]:
    """Load one JSON artifact from disk."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _summarize_reused_captions(
    benchmark: dict[str, Any],
    caption_path: Path,
) -> dict[str, Any]:
    """Validate the caption artifact reused by frozen replay or rebuild-based runs."""
    caption_store = CaptionStore(file_path=caption_path)
    caption_records = caption_store.load_all()
    expected_image_ids = {image_case["image_id"] for image_case in benchmark["images"]}
    available_image_ids = {record.image_id for record in caption_records}
    missing_image_ids = sorted(expected_image_ids - available_image_ids)
    extra_image_ids = sorted(available_image_ids - expected_image_ids)
    if missing_image_ids:
        raise RuntimeError(
            "Cannot reuse captions because benchmark image IDs are missing from "
            f"{caption_path}: {', '.join(missing_image_ids)}"
        )

    return {
        "status": "reused_existing_captions",
        "caption_output_path": str(caption_path),
        "captions_available": len(caption_records),
        "benchmark_image_count": len(expected_image_ids),
        "extra_caption_image_ids": extra_image_ids,
    }


def _validate_query_results_shape(
    benchmark: dict[str, Any],
    queries: list[dict[str, Any]],
    *,
    artifact_path: Path,
) -> None:
    """Reject malformed frozen artifacts before they can become misleading reports."""
    expected_query_ids = {query_case["id"] for query_case in benchmark["queries"]}
    actual_query_ids = {query_case["query_id"] for query_case in queries}
    missing_query_ids = sorted(expected_query_ids - actual_query_ids)
    extra_query_ids = sorted(actual_query_ids - expected_query_ids)
    if missing_query_ids or extra_query_ids:
        raise RuntimeError(
            "Frozen-artifact replay cannot use "
            f"{artifact_path} because its query coverage does not match the benchmark. "
            f"Missing query IDs: {missing_query_ids or 'none'}. Extra query IDs: {extra_query_ids or 'none'}."
        )

    empty_query_ids = [
        query_case["query_id"]
        for query_case in queries
        if not query_case.get("results")
    ]
    if empty_query_ids:
        empty_preview = ", ".join(empty_query_ids[:5])
        raise RuntimeError(
            "Frozen-artifact replay cannot use "
            f"{artifact_path} because {len(empty_query_ids)} query result(s) were empty "
            f"({empty_preview}). Refusing to write an all-zero report."
        )


def _load_frozen_mode_summary(
    benchmark: dict[str, Any],
    results_path: Path,
) -> dict[str, Any]:
    """Load one frozen representation results artifact and validate its query payload."""
    if not results_path.exists():
        raise RuntimeError(f"Frozen-artifact replay expected results at {results_path}, but the file is missing.")

    mode_summary = _load_json(results_path)
    queries = mode_summary.get("queries")
    if not isinstance(queries, list):
        raise RuntimeError(
            f"Frozen-artifact replay expected a queries list in {results_path}, but the artifact was malformed."
        )

    _validate_query_results_shape(benchmark, queries, artifact_path=results_path)
    return mode_summary


def _load_control_candidate_comparison_from_frozen_artifacts(
    benchmark: dict[str, Any],
    *,
    caption_path: Path,
    frozen_control_candidate_dir: Path,
) -> dict[str, Any]:
    """Replay a previously validated control/candidate comparison without network calls."""
    caption_summary = _summarize_reused_captions(benchmark, caption_path)
    control_results_path = frozen_control_candidate_dir / CONTROL_REPRESENTATION_MODE / "results.json"
    candidate_results_path = frozen_control_candidate_dir / CANDIDATE_BASELINE_REPRESENTATION_MODE / "results.json"
    control_summary = _load_frozen_mode_summary(benchmark, control_results_path)
    candidate_summary = _load_frozen_mode_summary(benchmark, candidate_results_path)

    comparison: dict[str, Any] = {
        "benchmark_name": benchmark["name"],
        "prompt_variant": "frozen_artifact_replay",
        "image_dir": str(Path(benchmark["image_dir"])),
        "caption_output_path": str(caption_path),
        "caption_reuse_enabled": True,
        "embedding_reuse_enabled": True,
        "execution_mode": "frozen_artifact_replay_based",
        "top_k": 3,
        "image_count": len(benchmark["images"]),
        "query_count": len(benchmark["queries"]),
        "caption_summary": caption_summary,
        "representation_modes": {
            CONTROL_REPRESENTATION_MODE: control_summary,
            CANDIDATE_BASELINE_REPRESENTATION_MODE: candidate_summary,
        },
        "artifact_source": {
            "execution_mode": "frozen_artifact_replay_based",
            "frozen_control_candidate_dir": str(frozen_control_candidate_dir),
        },
        "comparison_path": str(frozen_control_candidate_dir / "comparison.json"),
        "control_results_path": str(control_results_path),
        "candidate_results_path": str(candidate_results_path),
    }

    control_candidate_summary = _build_control_candidate_summary(comparison)
    if control_candidate_summary is not None:
        comparison["control_candidate_summary"] = control_candidate_summary

    return comparison


def _resolve_control_candidate_artifacts(
    benchmark: dict[str, Any],
    *,
    benchmark_path: Path,
    caption_path: Path,
    output_dir: Path,
    experiment_setting: FrozenExperimentSetting,
    artifact_mode: str,
    frozen_control_candidate_dir: Path | None,
) -> tuple[dict[str, Any], Path, Path, dict[str, Any]]:
    """Choose rebuild-based execution or trusted frozen replay for the control/candidate stage."""
    requested_frozen_dir = frozen_control_candidate_dir or experiment_setting.trusted_frozen_control_candidate_dir
    if artifact_mode == "frozen" and requested_frozen_dir is None:
        raise RuntimeError(
            "Frozen artifact mode requires --frozen-control-candidate-dir or a trusted frozen directory on the "
            "experiment setting."
        )

    frozen_replay_error: str | None = None
    if artifact_mode in {"auto", "frozen"} and requested_frozen_dir is not None:
        try:
            comparison = _load_control_candidate_comparison_from_frozen_artifacts(
                benchmark,
                caption_path=caption_path,
                frozen_control_candidate_dir=requested_frozen_dir,
            )
            return (
                comparison,
                Path(comparison["control_results_path"]),
                Path(comparison["candidate_results_path"]),
                {
                    "requested_artifact_mode": artifact_mode,
                    "execution_mode": "frozen_artifact_replay_based",
                    "frozen_control_candidate_dir": str(requested_frozen_dir),
                    "source_comparison_path": comparison["comparison_path"],
                },
            )
        except RuntimeError as exc:
            frozen_replay_error = str(exc)
            if artifact_mode == "frozen":
                raise

    control_candidate_dir = output_dir / "control_candidate"
    comparison = run_control_candidate_comparison(
        benchmark_path=benchmark_path,
        experiment_dir=control_candidate_dir,
        caption_path=caption_path,
        reuse_captions=True,
        reuse_embeddings=artifact_mode == "auto",
    )
    return (
        comparison,
        control_candidate_dir / CONTROL_REPRESENTATION_MODE / "results.json",
        control_candidate_dir / CANDIDATE_BASELINE_REPRESENTATION_MODE / "results.json",
        {
            "requested_artifact_mode": artifact_mode,
            "execution_mode": "rebuild_based",
            "control_candidate_dir": str(control_candidate_dir),
            "source_comparison_path": comparison["comparison_path"],
            "auto_fallback_reason": frozen_replay_error,
        },
    )


def _top_result(query_case: dict[str, Any]) -> dict[str, Any] | None:
    """Return the top result for one normalized query case."""
    ranked_results = query_case["results"]
    return ranked_results[0] if ranked_results else None


def _top1_correct(query_case: dict[str, Any]) -> bool:
    """Return whether the top result is one of the expected image IDs."""
    top_result = _top_result(query_case)
    if top_result is None:
        return False
    return top_result["image_id"] in set(query_case["expected_image_ids"])


def _normalize_query_cases(raw_queries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert stored representation or rerank outputs into one shared query shape."""
    normalized_queries: list[dict[str, Any]] = []
    for raw_query in raw_queries:
        ranked_results = raw_query["reranked_results"] if "reranked_results" in raw_query else raw_query["results"]
        normalized_queries.append(
            {
                "query_id": raw_query["query_id"],
                "query": raw_query["query"],
                "expected_image_ids": raw_query["expected_image_ids"],
                "tags": raw_query.get("tags", []),
                "hard_negative_image_ids": raw_query.get("hard_negative_image_ids", []),
                "results": ranked_results,
            }
        )
    return normalized_queries


def _build_query_metadata_lookup(benchmark: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index benchmark metadata by query ID for reporting and slice analysis."""
    return {
        query_case["id"]: query_case
        for query_case in benchmark["queries"]
    }


def _build_slice_metrics(
    query_cases: list[dict[str, Any]],
    query_metadata_lookup: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Compute Recall@1/Recall@3 by benchmark slice."""
    grouped_queries: dict[str, list[dict[str, Any]]] = {}
    for query_case in query_cases:
        slice_name = query_metadata_lookup[query_case["query_id"]].get("slice", "unspecified")
        grouped_queries.setdefault(slice_name, []).append(query_case)

    slice_metrics: dict[str, dict[str, Any]] = {}
    for slice_name, slice_queries in sorted(grouped_queries.items()):
        slice_metrics[slice_name] = {
            "query_count": len(slice_queries),
            "recall_at_1": compute_recall_at_k(slice_queries, k=1),
            "recall_at_3": compute_recall_at_k(slice_queries, k=3),
        }

    return slice_metrics


def _build_system_summary(
    label: str,
    query_cases: list[dict[str, Any]],
    query_metadata_lookup: dict[str, dict[str, Any]],
    artifact_path: Path,
) -> dict[str, Any]:
    """Build one compact metrics row for the report."""
    return {
        "label": label,
        "query_count": len(query_cases),
        "correct_at_1_count": sum(1 for query_case in query_cases if _top1_correct(query_case)),
        "correct_at_3_count": sum(
            1
            for query_case in query_cases
            if any(
                ranked_result["image_id"] in set(query_case["expected_image_ids"])
                for ranked_result in query_case["results"][:3]
            )
        ),
        "recall_at_1": compute_recall_at_k(query_cases, k=1),
        "recall_at_3": compute_recall_at_k(query_cases, k=3),
        "slice_metrics": _build_slice_metrics(query_cases, query_metadata_lookup),
        "artifact_path": str(artifact_path),
    }


def _build_outcome_delta(
    before_queries: list[dict[str, Any]],
    after_queries: list[dict[str, Any]],
    query_metadata_lookup: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Collect accuracy-improving and accuracy-regressing query flips between two systems."""
    before_by_id = {query_case["query_id"]: query_case for query_case in before_queries}
    after_by_id = {query_case["query_id"]: query_case for query_case in after_queries}

    improvements: list[dict[str, Any]] = []
    regressions: list[dict[str, Any]] = []
    for query_id, before_query in before_by_id.items():
        after_query = after_by_id[query_id]
        before_correct = _top1_correct(before_query)
        after_correct = _top1_correct(after_query)
        if before_correct == after_correct:
            continue

        before_top_result = _top_result(before_query)
        after_top_result = _top_result(after_query)
        change_record = {
            "query_id": query_id,
            "slice": query_metadata_lookup[query_id].get("slice", "unspecified"),
            "query": before_query["query"],
            "before_top_image_id": before_top_result["image_id"] if before_top_result is not None else None,
            "after_top_image_id": after_top_result["image_id"] if after_top_result is not None else None,
            "expected_image_ids": before_query["expected_image_ids"],
        }
        if after_correct:
            improvements.append(change_record)
        else:
            regressions.append(change_record)

    return {
        "improvements": improvements,
        "regressions": regressions,
    }


def _build_ablation_rows(
    caption_only_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
    rerank_no_paraphrase_summary: dict[str, Any],
    rerank_with_paraphrase_summary: dict[str, Any],
    candidate_delta: dict[str, list[dict[str, Any]]],
    rerank_base_delta: dict[str, list[dict[str, Any]]],
    paraphrase_delta: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Construct the compact ablation rows used in the JSON and markdown report."""
    return [
        {
            "system": caption_only_summary["label"],
            "recall_at_1": caption_only_summary["recall_at_1"],
            "recall_at_3": caption_only_summary["recall_at_3"],
            "delta_vs_prior_recall_at_1": None,
            "regressions_vs_prior": None,
        },
        {
            "system": candidate_summary["label"],
            "recall_at_1": candidate_summary["recall_at_1"],
            "recall_at_3": candidate_summary["recall_at_3"],
            "delta_vs_prior_recall_at_1": candidate_summary["recall_at_1"] - caption_only_summary["recall_at_1"],
            "regressions_vs_prior": len(candidate_delta["regressions"]),
        },
        {
            "system": rerank_no_paraphrase_summary["label"],
            "recall_at_1": rerank_no_paraphrase_summary["recall_at_1"],
            "recall_at_3": rerank_no_paraphrase_summary["recall_at_3"],
            "delta_vs_prior_recall_at_1": (
                rerank_no_paraphrase_summary["recall_at_1"] - candidate_summary["recall_at_1"]
            ),
            "regressions_vs_prior": len(rerank_base_delta["regressions"]),
        },
        {
            "system": rerank_with_paraphrase_summary["label"],
            "recall_at_1": rerank_with_paraphrase_summary["recall_at_1"],
            "recall_at_3": rerank_with_paraphrase_summary["recall_at_3"],
            "delta_vs_prior_recall_at_1": (
                rerank_with_paraphrase_summary["recall_at_1"] - rerank_no_paraphrase_summary["recall_at_1"]
            ),
            "regressions_vs_prior": len(paraphrase_delta["regressions"]),
        },
    ]


def _render_ablation_table(ablation_rows: list[dict[str, Any]]) -> str:
    """Render a small report-friendly markdown table."""
    lines = [
        "| System | Recall@1 | Recall@3 | Delta vs prior (R@1) | Regressions vs prior |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in ablation_rows:
        delta_value = (
            "n/a"
            if row["delta_vs_prior_recall_at_1"] is None
            else f"{row['delta_vs_prior_recall_at_1']:+.4f}"
        )
        regressions_value = (
            "n/a"
            if row["regressions_vs_prior"] is None
            else str(row["regressions_vs_prior"])
        )
        lines.append(
            f"| {row['system']} | {row['recall_at_1']:.4f} | {row['recall_at_3']:.4f} | "
            f"{delta_value} | {regressions_value} |"
        )
    return "\n".join(lines) + "\n"


def _build_recommendation(
    candidate_summary: dict[str, Any],
    rerank_with_paraphrase_summary: dict[str, Any],
    best_vs_candidate_delta: dict[str, list[dict[str, Any]]],
    paraphrase_delta: dict[str, list[dict[str, Any]]],
) -> dict[str, str]:
    """Return the decision and rationale for optional vs broader default promotion."""
    if paraphrase_delta["regressions"]:
        return {
            "decision": "keep_optional",
            "rationale": (
                "The paraphrase-overlap cue introduced regressions relative to the no-paraphrase "
                "rerank path on the broader sanity set, so the hard-benchmark winner should remain optional."
            ),
        }

    if best_vs_candidate_delta["regressions"]:
        return {
            "decision": "keep_optional",
            "rationale": (
                "The full deterministic rerank stack still regressed at least one broader sanity "
                "query relative to the simpler candidate path, even though the paraphrase-overlap "
                "cue itself did not add any new regressions."
            ),
        }

    if rerank_with_paraphrase_summary["recall_at_1"] > candidate_summary["recall_at_1"]:
        return {
            "decision": "promote_to_broader_default",
            "rationale": (
                "The frozen best configuration improved Recall@1 on the broader mixed sanity set "
                "without introducing any observed regressions, so it is strong enough to promote."
            ),
        }

    return {
        "decision": "keep_optional",
        "rationale": (
            "The broader sanity set did not show a clear enough benefit over the simpler candidate "
            "path to justify making the hard-benchmark winner the broader default."
        ),
    }


def _build_default_promotion_summary(
    experiment_setting: FrozenExperimentSetting,
    report: dict[str, Any],
    run_provenance: dict[str, Any],
) -> dict[str, Any]:
    """Package the report-ready default-promotion summary artifact."""
    hard_metrics = experiment_setting.known_hard_benchmark_metrics
    mixed_systems = report["systems"]
    rows = [
        {
            "system": "caption_only",
            "role": "baseline",
            "hard_benchmark": hard_metrics["caption_only"],
            "mixed_sanity": {
                "recall_at_1": mixed_systems["caption_only"]["recall_at_1"],
                "recall_at_3": mixed_systems["caption_only"]["recall_at_3"],
            },
        },
        {
            "system": "caption_plus_selected_structured",
            "role": "candidate",
            "hard_benchmark": hard_metrics["caption_plus_selected_structured"],
            "mixed_sanity": {
                "recall_at_1": mixed_systems["caption_plus_selected_structured"]["recall_at_1"],
                "recall_at_3": mixed_systems["caption_plus_selected_structured"]["recall_at_3"],
            },
        },
        {
            "system": "caption_plus_selected_structured + deterministic_top3_rerank + question_paraphrase_overlap=0.25",
            "role": "final_default",
            "hard_benchmark": hard_metrics["broader_default"],
            "mixed_sanity": {
                "recall_at_1": mixed_systems["best_hard_config"]["recall_at_1"],
                "recall_at_3": mixed_systems["best_hard_config"]["recall_at_3"],
            },
        },
    ]

    return {
        "experiment_setting_name": experiment_setting.name,
        "promotion_status": experiment_setting.promotion_status,
        "promotion_note": experiment_setting.promotion_note,
        "default_configuration": {
            "representation_mode": experiment_setting.representation_mode,
            "rerank": "deterministic_top3_rerank",
            "rerank_top_n": experiment_setting.rerank_top_n,
            "question_paraphrase_overlap": experiment_setting.rerank_weights.question_paraphrase_overlap,
            "singleton_low_signal_container_guard_enabled": (
                experiment_setting.singleton_low_signal_container_guard_enabled
            ),
        },
        "baseline_vs_candidate_vs_final_default": rows,
        "hard_benchmark_result": {
            "recall_at_1": hard_metrics["broader_default"]["recall_at_1"],
            "recall_at_3": hard_metrics["broader_default"]["recall_at_3"],
            "regression_count": hard_metrics["broader_default"]["regression_count"],
        },
        "mixed_sanity_result": {
            "recall_at_1": mixed_systems["best_hard_config"]["recall_at_1"],
            "recall_at_3": mixed_systems["best_hard_config"]["recall_at_3"],
            "regression_count": len(report["pairwise_deltas"]["best_config_vs_candidate"]["regressions"]),
            "execution_mode": run_provenance["execution_mode"],
        },
        "validation_caveat": experiment_setting.validation_caveat,
    }


def _render_default_promotion_summary(summary: dict[str, Any]) -> str:
    """Render the compact default-promotion artifact in markdown."""
    lines = [
        "# Broader Default Promotion Summary",
        "",
        "## Promotion",
        f"- Status: {summary['promotion_status']}",
        f"- Note: {summary['promotion_note']}",
        (
            "- Default configuration: "
            f"{summary['default_configuration']['representation_mode']} + deterministic_top3_rerank "
            f"(top-{summary['default_configuration']['rerank_top_n']}), "
            f"question_paraphrase_overlap={summary['default_configuration']['question_paraphrase_overlap']:.2f}, "
            "singleton low-signal container guard enabled"
        ),
        "",
        "## Results",
        "| System | Role | Hard R@1 | Hard R@3 | Mixed R@1 | Mixed R@3 |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["baseline_vs_candidate_vs_final_default"]:
        lines.append(
            f"| {row['system']} | {row['role']} | "
            f"{row['hard_benchmark']['recall_at_1']:.4f} | {row['hard_benchmark']['recall_at_3']:.4f} | "
            f"{row['mixed_sanity']['recall_at_1']:.4f} | {row['mixed_sanity']['recall_at_3']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Validation Caveat",
            f"- {summary['validation_caveat']}",
            "",
        ]
    )
    return "\n".join(lines)


def run_mixed_sanity_evaluation(
    benchmark_path: Path = DEFAULT_BENCHMARK_PATH,
    caption_path: Path = DEFAULT_CAPTION_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    experiment_setting_name: str = DEFAULT_EXPERIMENT_SETTING_NAME,
    artifact_mode: str = DEFAULT_ARTIFACT_MODE,
    frozen_control_candidate_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the requested mixed sanity comparison and package the report outputs."""
    experiment_setting = get_experiment_setting(experiment_setting_name)
    benchmark = load_benchmark_definition(benchmark_path)
    query_metadata_lookup = _build_query_metadata_lookup(benchmark)

    output_dir.mkdir(parents=True, exist_ok=True)
    rerank_no_paraphrase_dir = output_dir / "candidate_rerank_no_paraphrase"
    rerank_with_paraphrase_dir = output_dir / "candidate_rerank_with_paraphrase"
    report_path = output_dir / "report.json"
    ablation_table_path = output_dir / "ablation_table.md"
    summary_json_path = output_dir / "default_promotion_summary.json"
    summary_md_path = output_dir / "default_promotion_summary.md"

    control_candidate_comparison, control_results_path, candidate_results_path, run_provenance = (
        _resolve_control_candidate_artifacts(
            benchmark,
            benchmark_path=benchmark_path,
            caption_path=caption_path,
            output_dir=output_dir,
            experiment_setting=experiment_setting,
            artifact_mode=artifact_mode,
            frozen_control_candidate_dir=frozen_control_candidate_dir,
        )
    )

    rerank_no_paraphrase_comparison = run_top3_rerank_ablation(
        benchmark_path=benchmark_path,
        caption_path=caption_path,
        source_candidate_results_path=candidate_results_path,
        source_control_results_path=control_results_path,
        output_dir=rerank_no_paraphrase_dir,
        weights=replace(experiment_setting.rerank_weights, question_paraphrase_overlap=0.0),
    )
    rerank_with_paraphrase_comparison = run_top3_rerank_ablation(
        benchmark_path=benchmark_path,
        caption_path=caption_path,
        source_candidate_results_path=candidate_results_path,
        source_control_results_path=control_results_path,
        output_dir=rerank_with_paraphrase_dir,
        weights=experiment_setting.rerank_weights,
    )

    caption_only_queries = control_candidate_comparison["representation_modes"][CONTROL_REPRESENTATION_MODE]["queries"]
    candidate_queries = control_candidate_comparison["representation_modes"][CANDIDATE_BASELINE_REPRESENTATION_MODE]["queries"]
    rerank_no_paraphrase_queries = _normalize_query_cases(_load_json(Path(rerank_no_paraphrase_comparison["results_path"]))["queries"])
    rerank_with_paraphrase_queries = _normalize_query_cases(_load_json(Path(rerank_with_paraphrase_comparison["results_path"]))["queries"])

    caption_only_summary = _build_system_summary(
        label="caption_only",
        query_cases=caption_only_queries,
        query_metadata_lookup=query_metadata_lookup,
        artifact_path=control_results_path,
    )
    candidate_summary = _build_system_summary(
        label="caption_plus_selected_structured",
        query_cases=candidate_queries,
        query_metadata_lookup=query_metadata_lookup,
        artifact_path=candidate_results_path,
    )
    rerank_no_paraphrase_summary = _build_system_summary(
        label="caption_plus_selected_structured + deterministic_top3_rerank",
        query_cases=rerank_no_paraphrase_queries,
        query_metadata_lookup=query_metadata_lookup,
        artifact_path=Path(rerank_no_paraphrase_comparison["results_path"]),
    )
    rerank_with_paraphrase_summary = _build_system_summary(
        label=(
            "caption_plus_selected_structured + deterministic_top3_rerank + "
            "question_paraphrase_overlap=0.25"
        ),
        query_cases=rerank_with_paraphrase_queries,
        query_metadata_lookup=query_metadata_lookup,
        artifact_path=Path(rerank_with_paraphrase_comparison["results_path"]),
    )

    candidate_delta = _build_outcome_delta(caption_only_queries, candidate_queries, query_metadata_lookup)
    rerank_base_delta = _build_outcome_delta(candidate_queries, rerank_no_paraphrase_queries, query_metadata_lookup)
    best_vs_candidate_delta = _build_outcome_delta(candidate_queries, rerank_with_paraphrase_queries, query_metadata_lookup)
    paraphrase_delta = _build_outcome_delta(
        rerank_no_paraphrase_queries,
        rerank_with_paraphrase_queries,
        query_metadata_lookup,
    )
    ablation_rows = _build_ablation_rows(
        caption_only_summary=caption_only_summary,
        candidate_summary=candidate_summary,
        rerank_no_paraphrase_summary=rerank_no_paraphrase_summary,
        rerank_with_paraphrase_summary=rerank_with_paraphrase_summary,
        candidate_delta=candidate_delta,
        rerank_base_delta=rerank_base_delta,
        paraphrase_delta=paraphrase_delta,
    )
    recommendation = _build_recommendation(
        candidate_summary=candidate_summary,
        rerank_with_paraphrase_summary=rerank_with_paraphrase_summary,
        best_vs_candidate_delta=best_vs_candidate_delta,
        paraphrase_delta=paraphrase_delta,
    )

    report = {
        "benchmark_name": benchmark["name"],
        "benchmark_path": str(benchmark_path),
        "experiment_setting": {
            "name": experiment_setting.name,
            "description": experiment_setting.description,
            "representation_mode": experiment_setting.representation_mode,
            "rerank_top_n": experiment_setting.rerank_top_n,
            "rerank_weights": experiment_setting.rerank_weights.as_dict(),
            "source_benchmark_path": str(experiment_setting.source_benchmark_path),
            "known_hard_benchmark_metrics": experiment_setting.known_hard_benchmark_metrics,
            "promotion_status": experiment_setting.promotion_status,
            "promotion_note": experiment_setting.promotion_note,
            "validation_caveat": experiment_setting.validation_caveat,
            "singleton_low_signal_container_guard_enabled": (
                experiment_setting.singleton_low_signal_container_guard_enabled
            ),
            "trusted_frozen_control_candidate_dir": (
                str(experiment_setting.trusted_frozen_control_candidate_dir)
                if experiment_setting.trusted_frozen_control_candidate_dir is not None
                else None
            ),
        },
        "caption_path": str(caption_path),
        "artifact_mode": artifact_mode,
        "run_provenance": run_provenance,
        "validation_status": {
            "frozen_artifact_replay": (
                "validated"
                if run_provenance["execution_mode"] == "frozen_artifact_replay_based"
                else "not_used"
            ),
            "end_to_end_rebuild": (
                "blocked_by_connection_error"
                if run_provenance["execution_mode"] == "frozen_artifact_replay_based"
                else "completed_in_this_run"
            ),
        },
        "query_count": len(benchmark["queries"]),
        "slice_counts": {
            slice_name: sum(1 for query_case in benchmark["queries"] if query_case.get("slice") == slice_name)
            for slice_name in sorted({query_case.get("slice", "unspecified") for query_case in benchmark["queries"]})
        },
        "systems": {
            "caption_only": caption_only_summary,
            "caption_plus_selected_structured": candidate_summary,
            "caption_plus_selected_structured_plus_deterministic_top3_rerank": rerank_no_paraphrase_summary,
            "best_hard_config": rerank_with_paraphrase_summary,
        },
        "ablation_rows": ablation_rows,
        "notable_regressions": {
            "candidate_vs_caption_only": candidate_delta["regressions"],
            "best_config_vs_candidate": best_vs_candidate_delta["regressions"],
        },
        "cases_helped_by_paraphrase_overlap": paraphrase_delta["improvements"],
        "cases_hurt_by_paraphrase_overlap": paraphrase_delta["regressions"],
        "pairwise_deltas": {
            "candidate_vs_caption_only": candidate_delta,
            "rerank_without_paraphrase_vs_candidate": rerank_base_delta,
            "best_config_vs_candidate": best_vs_candidate_delta,
            "paraphrase_overlap_vs_no_paraphrase": paraphrase_delta,
        },
        "recommendation": recommendation,
        "artifacts": {
            "control_candidate_comparison_path": control_candidate_comparison["comparison_path"],
            "rerank_no_paraphrase_comparison_path": rerank_no_paraphrase_comparison["comparison_path"],
            "rerank_with_paraphrase_comparison_path": rerank_with_paraphrase_comparison["comparison_path"],
            "report_path": str(report_path),
            "ablation_table_path": str(ablation_table_path),
            "default_promotion_summary_json_path": str(summary_json_path),
            "default_promotion_summary_markdown_path": str(summary_md_path),
        },
    }

    ablation_table = _render_ablation_table(ablation_rows)
    default_promotion_summary = _build_default_promotion_summary(
        experiment_setting=experiment_setting,
        report=report,
        run_provenance=run_provenance,
    )
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    with ablation_table_path.open("w", encoding="utf-8") as handle:
        handle.write(ablation_table)
    with summary_json_path.open("w", encoding="utf-8") as handle:
        json.dump(default_promotion_summary, handle, indent=2, ensure_ascii=False)
    with summary_md_path.open("w", encoding="utf-8") as handle:
        handle.write(_render_default_promotion_summary(default_promotion_summary))

    report["report_path"] = str(report_path)
    report["ablation_table_path"] = str(ablation_table_path)
    report["default_promotion_summary_json_path"] = str(summary_json_path)
    report["default_promotion_summary_markdown_path"] = str(summary_md_path)
    return report


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for the mixed sanity evaluation."""
    parser = argparse.ArgumentParser(description="Run the broader mixed sanity evaluation for the frozen best hard-benchmark setting.")
    parser.add_argument(
        "--benchmark-path",
        type=Path,
        default=DEFAULT_BENCHMARK_PATH,
        help="Mixed sanity benchmark JSON definition.",
    )
    parser.add_argument(
        "--caption-path",
        type=Path,
        default=DEFAULT_CAPTION_PATH,
        help="Fixed caption JSONL reused across mixed sanity runs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Root directory where mixed sanity artifacts should be written.",
    )
    parser.add_argument(
        "--experiment-setting-name",
        default=DEFAULT_EXPERIMENT_SETTING_NAME,
        help="Named frozen experiment setting to validate.",
    )
    parser.add_argument(
        "--artifact-mode",
        choices=("auto", "rebuild", "frozen"),
        default=DEFAULT_ARTIFACT_MODE,
        help=(
            "Choose whether to rebuild control/candidate artifacts, replay trusted frozen artifacts, "
            "or auto-select the frozen path when available."
        ),
    )
    parser.add_argument(
        "--frozen-control-candidate-dir",
        type=Path,
        default=None,
        help="Optional directory containing trusted frozen caption_only and candidate results for offline replay.",
    )
    return parser


def _build_cli_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Return a compact CLI-facing summary."""
    return {
        "benchmark_name": report["benchmark_name"],
        "experiment_setting_name": report["experiment_setting"]["name"],
        "artifact_mode": report["artifact_mode"],
        "execution_mode": report["run_provenance"]["execution_mode"],
        "query_count": report["query_count"],
        "caption_only": {
            "recall_at_1": report["systems"]["caption_only"]["recall_at_1"],
            "recall_at_3": report["systems"]["caption_only"]["recall_at_3"],
        },
        "candidate": {
            "recall_at_1": report["systems"]["caption_plus_selected_structured"]["recall_at_1"],
            "recall_at_3": report["systems"]["caption_plus_selected_structured"]["recall_at_3"],
        },
        "best_hard_config": {
            "recall_at_1": report["systems"]["best_hard_config"]["recall_at_1"],
            "recall_at_3": report["systems"]["best_hard_config"]["recall_at_3"],
        },
        "cases_helped_by_paraphrase_overlap": [
            case["query_id"]
            for case in report["cases_helped_by_paraphrase_overlap"]
        ],
        "cases_hurt_by_paraphrase_overlap": [
            case["query_id"]
            for case in report["cases_hurt_by_paraphrase_overlap"]
        ],
        "recommendation": report["recommendation"],
        "report_path": report["report_path"],
        "ablation_table_path": report["ablation_table_path"],
        "default_promotion_summary_json_path": report["default_promotion_summary_json_path"],
        "default_promotion_summary_markdown_path": report["default_promotion_summary_markdown_path"],
    }


def main() -> int:
    """Run the mixed sanity evaluation and print a compact summary."""
    parser = build_parser()
    args = parser.parse_args()
    report = run_mixed_sanity_evaluation(
        benchmark_path=args.benchmark_path,
        caption_path=args.caption_path,
        output_dir=args.output_dir,
        experiment_setting_name=args.experiment_setting_name,
        artifact_mode=args.artifact_mode,
        frozen_control_candidate_dir=args.frozen_control_candidate_dir,
    )
    print(json.dumps(_build_cli_summary(report), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
