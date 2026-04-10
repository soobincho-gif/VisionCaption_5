"""Persistence helper for caption embeddings."""

from __future__ import annotations

from pathlib import Path

from src.config.settings import settings
from src.core.schemas import EmbeddingRecord


class EmbeddingStore:
    """Keep embedding persistence separate from provider and ranking logic."""

    def __init__(self, file_path: Path | None = None) -> None:
        settings.ensure_output_dirs()
        self.file_path = file_path or settings.embedding_output_dir / "caption_embeddings.jsonl"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, record: EmbeddingRecord) -> None:
        """Append one embedding record to the JSONL store."""
        with self.file_path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json() + "\n")

    def list_image_ids(self) -> set[str]:
        """Return the set of image IDs that already have persisted embeddings."""
        return {record.image_id for record in self.load_all()}

    def load_all(self) -> list[EmbeddingRecord]:
        """Load every stored embedding record from disk."""
        if not self.file_path.exists():
            return []

        records: list[EmbeddingRecord] = []
        with self.file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    records.append(EmbeddingRecord.model_validate_json(line))
        return records
