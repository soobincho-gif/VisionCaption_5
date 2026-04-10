"""Offline embedding-index pipeline for the semantic retrieval baseline."""

from __future__ import annotations

from typing import Any

from src.config.settings import settings
from src.core.schemas import CaptionRecord
from src.core.representation import build_embedding_source_text, normalize_representation_mode
from src.core.schemas import EmbeddingRecord
from src.core.types import CaptionRepresentationMode
from src.services.embedding_service import EmbeddingService
from src.storage.caption_store import CaptionStore
from src.storage.embedding_store import EmbeddingStore


def _load_matching_embedding_records(
    embedding_store: EmbeddingStore,
    representation_mode: CaptionRepresentationMode,
) -> list[EmbeddingRecord]:
    """Return stored embeddings that match the requested representation mode."""
    return [
        record
        for record in embedding_store.load_all()
        if record.vector and record.representation_mode in (None, representation_mode)
    ]


def _build_embedding_coverage(
    caption_records: list[CaptionRecord],
    embedding_records: list[EmbeddingRecord],
) -> dict[str, Any]:
    """Summarize embedding coverage relative to the available caption records."""
    expected_image_ids = {record.image_id for record in caption_records}
    available_image_ids = {record.image_id for record in embedding_records}
    dimensions = sorted({len(record.vector) for record in embedding_records if record.vector})
    return {
        "expected_image_count": len(expected_image_ids),
        "available_embedding_count": len(available_image_ids),
        "missing_image_ids": sorted(expected_image_ids - available_image_ids),
        "extra_embedding_image_ids": sorted(available_image_ids - expected_image_ids),
        "embedding_dimensions": dimensions[0] if len(dimensions) == 1 else 0,
    }


def run_embedding_pipeline(
    limit: int | None = None,
    caption_store: CaptionStore | None = None,
    embedding_store: EmbeddingStore | None = None,
    representation_mode: CaptionRepresentationMode = "caption_only",
    reuse_existing: bool = False,
    require_complete_coverage: bool = False,
) -> dict[str, object]:
    """Read captions, generate embeddings, and persist embedding records."""
    normalized_representation_mode = normalize_representation_mode(representation_mode)
    caption_store = caption_store or CaptionStore()
    embedding_store = embedding_store or EmbeddingStore(
        file_path=settings.embedding_output_path_for_mode(normalized_representation_mode)
    )
    service = EmbeddingService()
    caption_records = caption_store.load_all()
    summary: dict[str, object] = {
        "status": "completed",
        "captions_available": len(caption_records),
        "captions_skipped_existing": 0,
        "captions_selected_for_run": 0,
        "embeddings_written": 0,
        "embedding_dimensions": 0,
        "caption_input_path": str(caption_store.file_path),
        "embedding_output_path": str(embedding_store.file_path),
        "model_name": service.model_name,
        "representation_mode": normalized_representation_mode,
        "reuse_existing_enabled": reuse_existing,
        "errors": [],
    }

    if not caption_records:
        summary["status"] = "no_captions_found"
        return summary

    existing_records = _load_matching_embedding_records(embedding_store, normalized_representation_mode)
    existing_coverage = _build_embedding_coverage(caption_records, existing_records)
    summary["embedding_coverage"] = existing_coverage
    if reuse_existing and not existing_coverage["missing_image_ids"] and existing_records:
        summary["status"] = "reused_existing_embeddings"
        summary["captions_skipped_existing"] = existing_coverage["available_embedding_count"]
        summary["embedding_dimensions"] = existing_coverage["embedding_dimensions"]
        return summary

    existing_ids = {record.image_id for record in existing_records}
    pending_caption_records = []
    seen_image_ids = set(existing_ids)
    captions_skipped_existing = 0
    for caption_record in caption_records:
        if caption_record.image_id in seen_image_ids:
            captions_skipped_existing += 1
            continue
        pending_caption_records.append(caption_record)
        seen_image_ids.add(caption_record.image_id)

    if limit is not None:
        pending_caption_records = pending_caption_records[:limit]

    summary["captions_skipped_existing"] = captions_skipped_existing
    summary["captions_selected_for_run"] = len(pending_caption_records)
    if not pending_caption_records:
        if require_complete_coverage and existing_coverage["missing_image_ids"]:
            missing_preview = ", ".join(existing_coverage["missing_image_ids"][:5])
            raise RuntimeError(
                "Embedding coverage is incomplete for representation mode "
                f"'{normalized_representation_mode}' at {embedding_store.file_path}. Missing image IDs: "
                f"{missing_preview}"
            )
        summary["status"] = "nothing_to_do"
        summary["embedding_dimensions"] = existing_coverage["embedding_dimensions"]
        return summary

    if not service.is_configured():
        missing_count = len(pending_caption_records)
        raise RuntimeError(
            "Embedding indexing cannot continue for representation mode "
            f"'{normalized_representation_mode}' because {missing_count} caption(s) still need vectors at "
            f"{embedding_store.file_path}. Reuse a complete frozen embedding artifact or rerun with network access."
        )

    errors: list[dict[str, str]] = []
    embeddings_written = 0
    embedding_dimensions = 0
    for caption_record in pending_caption_records:
        try:
            source_text = build_embedding_source_text(
                caption_record,
                representation_mode=normalized_representation_mode,
            )
            vector = service.embed_text(source_text)
            embedding_record = EmbeddingRecord(
                image_id=caption_record.image_id,
                source_text=source_text,
                vector=vector,
                representation_mode=normalized_representation_mode,
                model_name=service.model_name,
            )
            embedding_store.save(embedding_record)
            embeddings_written += 1
            embedding_dimensions = len(vector)
        except Exception as exc:
            errors.append(
                {
                    "image_id": caption_record.image_id,
                    "error": str(exc),
                }
            )

    summary["embeddings_written"] = embeddings_written
    summary["embedding_dimensions"] = embedding_dimensions
    summary["errors"] = errors
    if errors:
        summary["status"] = "completed_with_errors"

    final_records = _load_matching_embedding_records(embedding_store, normalized_representation_mode)
    final_coverage = _build_embedding_coverage(caption_records, final_records)
    summary["embedding_coverage"] = final_coverage
    if final_coverage["embedding_dimensions"]:
        summary["embedding_dimensions"] = final_coverage["embedding_dimensions"]
    if require_complete_coverage and final_coverage["missing_image_ids"]:
        missing_preview = ", ".join(final_coverage["missing_image_ids"][:5])
        raise RuntimeError(
            "Embedding generation finished without complete coverage for representation mode "
            f"'{normalized_representation_mode}' at {embedding_store.file_path}. Missing image IDs: "
            f"{missing_preview}. Refusing to continue evaluation with incomplete artifacts."
        )

    return summary
