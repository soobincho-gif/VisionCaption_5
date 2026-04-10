"""Persistence helper for retrieval results and evaluation snapshots."""

from __future__ import annotations

from pathlib import Path

from src.config.settings import settings
from src.core.schemas import RetrievalResult


class ResultStore:
    """Store ranked search results separately from captions and embeddings."""

    def __init__(self, file_path: Path | None = None) -> None:
        settings.ensure_output_dirs()
        self.file_path = file_path or settings.retrieval_output_dir / "search_results.jsonl"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save_results(self, results: list[RetrievalResult]) -> None:
        """Append a batch of retrieval results to the JSONL store."""
        with self.file_path.open("a", encoding="utf-8") as handle:
            for result in results:
                handle.write(result.model_dump_json() + "\n")
