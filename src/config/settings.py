"""Project settings and shared path conventions for the baseline implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for models, paths, and small runtime defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    raw_data_dir: Path = Path("data/raw")
    caption_output_dir: Path = Path("outputs/captions")
    embedding_output_dir: Path = Path("outputs/embeddings")
    retrieval_output_dir: Path = Path("outputs/retrieval_results")
    eval_output_dir: Path = Path("outputs/eval")

    supported_image_extensions: tuple[str, ...] = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
    )
    image_discovery_recursive: bool = True
    default_top_k: int = 3

    openai_api_key: str | None = None
    vision_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    vision_image_detail: Literal["low", "high", "auto"] = "auto"
    caption_max_output_tokens: int = 1000

    def ensure_output_dirs(self) -> None:
        """Create output directories expected by the scaffolded stores."""
        for path in (
            self.caption_output_dir,
            self.embedding_output_dir,
            self.retrieval_output_dir,
            self.eval_output_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def embedding_output_path_for_mode(self, representation_mode: str) -> Path:
        """Return the convention-based embedding JSONL path for a representation mode."""
        safe_mode = representation_mode.replace("/", "_").replace("\\", "_")
        return self.embedding_output_dir / f"caption_embeddings.{safe_mode}.jsonl"


settings = Settings()
