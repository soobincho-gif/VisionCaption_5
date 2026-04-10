"""Shared helpers for small retrieval experiments and benchmark comparisons."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_benchmark_definition(benchmark_path: Path) -> dict[str, Any]:
    """Load an evaluation benchmark definition from disk."""
    with benchmark_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def reset_file(path: Path) -> None:
    """Remove a previous experiment artifact when regenerating a clean run."""
    if path.exists():
        path.unlink()


def serialize_results(results: list[Any]) -> list[dict[str, Any]]:
    """Convert typed retrieval results into plain JSON-friendly dictionaries."""
    return [result.model_dump(mode="json") for result in results]


def compute_recall_at_k(results_by_query: list[dict[str, Any]], k: int) -> float:
    """Compute recall at k for the benchmark query list."""
    if not results_by_query:
        return 0.0

    hits = 0
    for result in results_by_query:
        expected_image_ids = set(result["expected_image_ids"])
        ranked_image_ids = [item["image_id"] for item in result["results"][:k]]
        if any(image_id in expected_image_ids for image_id in ranked_image_ids):
            hits += 1

    return hits / len(results_by_query)
