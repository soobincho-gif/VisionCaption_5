"""CLI entrypoint for the offline indexing stages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config.settings import settings
from src.core.representation import CANDIDATE_BASELINE_REPRESENTATION_MODE, INDEXING_REPRESENTATION_MODES
from src.pipelines.build_caption_index import run_caption_pipeline
from src.pipelines.build_embedding_index import run_embedding_pipeline
from src.storage.caption_store import CaptionStore
from src.storage.embedding_store import EmbeddingStore


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for the indexing scaffold."""
    parser = argparse.ArgumentParser(description="Prepare or inspect indexing pipeline stages.")
    parser.add_argument(
        "--stage",
        choices=("captions", "embeddings", "all"),
        default="all",
        help="Choose which pipeline stage summary to run.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional record-processing limit for the selected indexing stage.",
    )
    parser.add_argument(
        "--representation-mode",
        choices=INDEXING_REPRESENTATION_MODES,
        default=CANDIDATE_BASELINE_REPRESENTATION_MODE,
        help=(
            "Text representation to embed for the embedding stage. "
            "The candidate baseline is the default; caption_only remains the control."
        ),
    )
    parser.add_argument(
        "--caption-path",
        type=Path,
        default=None,
        help="Optional caption JSONL path to write/read instead of the default captions store.",
    )
    parser.add_argument(
        "--embedding-output-path",
        type=Path,
        default=None,
        help="Optional embedding JSONL output path. Defaults to a representation-mode-specific file.",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=None,
        help="Optional image directory for the caption stage.",
    )
    return parser


def main() -> int:
    """Run the selected indexing scaffold stages and print their summaries."""
    parser = build_parser()
    args = parser.parse_args()

    summaries: list[dict[str, object]] = []
    caption_store = CaptionStore(file_path=args.caption_path) if args.caption_path else None
    if args.stage in {"captions", "all"}:
        summaries.append(
            run_caption_pipeline(
                limit=args.limit,
                image_dir=args.image_dir,
                store=caption_store,
            )
        )
    if args.stage in {"embeddings", "all"}:
        embedding_output_path = args.embedding_output_path or settings.embedding_output_path_for_mode(
            args.representation_mode
        )
        embedding_store = EmbeddingStore(file_path=embedding_output_path)
        summaries.append(
            run_embedding_pipeline(
                limit=args.limit,
                caption_store=caption_store,
                embedding_store=embedding_store,
                representation_mode=args.representation_mode,
            )
        )

    for summary in summaries:
        print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
