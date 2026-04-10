"""CLI entrypoint for baseline text-to-image semantic retrieval."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.config.settings import settings
from src.core.representation import INDEXING_REPRESENTATION_MODES
from src.pipelines.search_images import search
from src.storage.caption_store import CaptionStore
from src.storage.embedding_store import EmbeddingStore


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for the retrieval command."""
    parser = argparse.ArgumentParser(description="Search indexed images with a text query.")
    parser.add_argument("query", type=str, help="Natural-language image description.")
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of ranked results to return.",
    )
    parser.add_argument(
        "--representation-mode",
        choices=INDEXING_REPRESENTATION_MODES,
        default=None,
        help="Use the convention-based embedding file for a supported representation mode.",
    )
    parser.add_argument(
        "--caption-path",
        type=Path,
        default=None,
        help="Optional caption JSONL path for resolving image paths in results.",
    )
    parser.add_argument(
        "--embedding-path",
        type=Path,
        default=None,
        help="Optional embedding JSONL path. Overrides --representation-mode path resolution.",
    )
    return parser


def main() -> int:
    """Run baseline retrieval and print ranked results in a readable format."""
    parser = build_parser()
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be at least 1.")

    embedding_path = args.embedding_path
    if embedding_path is None and args.representation_mode:
        embedding_path = settings.embedding_output_path_for_mode(args.representation_mode)

    caption_store = CaptionStore(file_path=args.caption_path) if args.caption_path else None
    embedding_store = EmbeddingStore(file_path=embedding_path) if embedding_path else None
    results = search(
        args.query,
        top_k=args.top_k,
        caption_store=caption_store,
        embedding_store=embedding_store,
    )

    if not results:
        print("No retrieval results were returned.")
        print("If you have not indexed sample images yet, add images to data/raw and run `python -m src.cli.index_images --stage all`.")
        return 0

    print(f"Query: {args.query}")
    if args.representation_mode:
        print(f"Representation mode: {args.representation_mode}")
    if embedding_path:
        print(f"Embedding path: {embedding_path}")
    print(f"Top {len(results)} results")
    for result in results:
        image_path = result.image_path or "(image path unavailable)"
        print(f"{result.rank}. {result.image_id} | score={result.similarity_score:.4f} | path={image_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
