"""Experiment pipeline for comparing caption prompt variants on a small retrieval benchmark."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.config.prompts import CaptionPromptVariant
from src.config.settings import settings
from src.pipelines.build_caption_index import run_caption_pipeline
from src.pipelines.build_embedding_index import run_embedding_pipeline
from src.pipelines.evaluation_utils import compute_recall_at_k, load_benchmark_definition, reset_file, serialize_results
from src.pipelines.search_images import search
from src.storage.caption_store import CaptionStore
from src.storage.embedding_store import EmbeddingStore

DEFAULT_BENCHMARK_PATH = Path("data/samples/prompt_fidelity/benchmark.json")
DEFAULT_EXPERIMENT_DIR = settings.eval_output_dir / "prompt_fidelity"


def build_variant_paths(experiment_dir: Path, prompt_variant: CaptionPromptVariant) -> dict[str, Path]:
    """Return the output paths used for one prompt variant run."""
    variant_dir = experiment_dir / prompt_variant
    return {
        "variant_dir": variant_dir,
        "captions": variant_dir / "captions.jsonl",
        "embeddings": variant_dir / "embeddings.jsonl",
        "results": variant_dir / "results.json",
    }

def run_prompt_comparison(
    benchmark_path: Path | None = None,
    experiment_dir: Path | None = None,
    top_k: int = 3,
) -> dict[str, Any]:
    """Run baseline and improved prompt variants on the same benchmark dataset."""
    benchmark = load_benchmark_definition(benchmark_path or DEFAULT_BENCHMARK_PATH)
    image_dir = Path(benchmark["image_dir"])
    output_dir = experiment_dir or DEFAULT_EXPERIMENT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    variants: list[CaptionPromptVariant] = ["baseline", "retrieval_oriented_v2"]
    comparison: dict[str, Any] = {
        "benchmark_name": benchmark["name"],
        "image_dir": str(image_dir),
        "top_k": top_k,
        "image_count": len(benchmark["images"]),
        "query_count": len(benchmark["queries"]),
        "variants": {},
    }

    for prompt_variant in variants:
        variant_paths = build_variant_paths(output_dir, prompt_variant)
        variant_paths["variant_dir"].mkdir(parents=True, exist_ok=True)
        reset_file(variant_paths["captions"])
        reset_file(variant_paths["embeddings"])
        reset_file(variant_paths["results"])

        caption_store = CaptionStore(file_path=variant_paths["captions"])
        embedding_store = EmbeddingStore(file_path=variant_paths["embeddings"])

        caption_summary = run_caption_pipeline(
            image_dir=image_dir,
            store=caption_store,
            prompt_variant=prompt_variant,
        )
        embedding_summary = run_embedding_pipeline(
            caption_store=caption_store,
            embedding_store=embedding_store,
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
                    "query": query_case["query"],
                    "expected_image_ids": query_case["expected_image_ids"],
                    "results": serialize_results(results),
                }
            )

        variant_summary = {
            "caption_summary": caption_summary,
            "embedding_summary": embedding_summary,
            "recall_at_1": compute_recall_at_k(results_by_query, k=1),
            "recall_at_3": compute_recall_at_k(results_by_query, k=min(3, top_k)),
            "queries": results_by_query,
        }
        comparison["variants"][prompt_variant] = variant_summary

        with variant_paths["results"].open("w", encoding="utf-8") as handle:
            json.dump(variant_summary, handle, indent=2, ensure_ascii=False)

    baseline_summary = comparison["variants"]["baseline"]
    improved_summary = comparison["variants"]["retrieval_oriented_v2"]
    comparison["delta"] = {
        "recall_at_1": improved_summary["recall_at_1"] - baseline_summary["recall_at_1"],
        "recall_at_3": improved_summary["recall_at_3"] - baseline_summary["recall_at_3"],
    }

    comparison_path = output_dir / "comparison.json"
    with comparison_path.open("w", encoding="utf-8") as handle:
        json.dump(comparison, handle, indent=2, ensure_ascii=False)

    comparison["comparison_path"] = str(comparison_path)
    return comparison
