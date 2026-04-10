"""Persistence helper for caption records stored on local disk."""

from __future__ import annotations

from pathlib import Path

from src.config.settings import settings
from src.core.schemas import CaptionRecord


class CaptionStore:
    """Read and write caption records without leaking file details into pipelines."""

    def __init__(self, file_path: Path | None = None) -> None:
        settings.ensure_output_dirs()
        self.file_path = file_path or settings.caption_output_dir / "captions.jsonl"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, record: CaptionRecord) -> None:
        """Append one caption record to the JSONL store."""
        with self.file_path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json() + "\n")

    def list_image_ids(self) -> set[str]:
        """Return the set of image IDs already persisted in storage."""
        return {record.image_id for record in self.load_all()}

    def load_all(self) -> list[CaptionRecord]:
        """Load every stored caption record from disk."""
        if not self.file_path.exists():
            return []

        records: list[CaptionRecord] = []
        with self.file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    records.append(CaptionRecord.model_validate_json(line))
        return records
