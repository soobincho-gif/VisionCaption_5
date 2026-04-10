"""Session-only upload helpers for the Streamlit demo."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from io import BytesIO
from pathlib import Path
import tempfile
from typing import Any

from PIL import Image

from src.core.representation import build_embedding_source_text
from src.core.rerank import build_rerank_feature_bundle
from src.core.schemas import CaptionRecord
from src.services.embedding_service import EmbeddingService
from src.services.similarity_service import SimilarityService
from src.services.vision_caption_service import VisionCaptionService
from src.storage.embedding_store import EmbeddingStore


MAX_UPLOAD_BYTES = 12 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
SESSION_REPRESENTATION_MODE = "caption_plus_selected_structured"


def inspect_uploaded_image(
    image_bytes: bytes,
    filename: str,
    content_type: str | None = None,
) -> dict[str, Any]:
    """Validate an uploaded image and return UI-friendly metadata."""
    if not image_bytes:
        raise ValueError("The uploaded file is empty.")
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        max_mb = MAX_UPLOAD_BYTES / (1024 * 1024)
        raise ValueError(f"Upload is too large for the demo session. Keep files under {max_mb:.0f} MB.")

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.load()
            image_format = str(image.format or "").upper()
            if image_format not in ALLOWED_IMAGE_FORMATS:
                allowed = ", ".join(sorted(ALLOWED_IMAGE_FORMATS))
                raise ValueError(f"Unsupported image format: {image_format or 'unknown'}. Use {allowed}.")
            width, height = image.size
            mode = image.mode
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("The uploaded file could not be opened as an image.") from exc

    digest = hashlib.sha256(image_bytes).hexdigest()
    return {
        "filename": filename,
        "content_type": content_type or "image/unknown",
        "size_bytes": len(image_bytes),
        "width": width,
        "height": height,
        "format": image_format,
        "mode": mode,
        "sha256": digest,
        "image_id": f"uploaded_{digest[:12]}",
    }


def build_temporary_upload_record(
    image_bytes: bytes,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Generate a structured representation for an uploaded image without persistent storage."""
    caption_service = VisionCaptionService()
    if not caption_service.is_configured():
        raise RuntimeError(
            "OPENAI_API_KEY is not configured, so the demo cannot generate a visual representation for uploads."
        )

    suffix = Path(str(metadata.get("filename") or "upload.png")).suffix or ".png"
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
            handle.write(image_bytes)
            temp_path = Path(handle.name)

        caption_content = caption_service.generate_caption_content(temp_path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    caption_record = CaptionRecord(
        **caption_content.model_dump(mode="json"),
        image_id=str(metadata["image_id"]),
        image_path=f"session://{metadata['filename']}",
        model_name=caption_service.model_name,
    )
    source_text = build_embedding_source_text(
        caption_record,
        representation_mode=SESSION_REPRESENTATION_MODE,
    )
    feature_bundle = build_rerank_feature_bundle(caption_record)
    return {
        "image_id": caption_record.image_id,
        "caption_record": caption_record.model_dump(mode="json"),
        "source_text": source_text,
        "feature_bundle": feature_bundle,
        "representation_mode": SESSION_REPRESENTATION_MODE,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def build_temporary_embedding(source_text: str) -> dict[str, Any]:
    """Create a session-only embedding for an uploaded representation."""
    embedding_service = EmbeddingService()
    if not embedding_service.is_configured():
        raise RuntimeError(
            "OPENAI_API_KEY is not configured, so the demo cannot create a temporary upload embedding."
        )

    vector = embedding_service.embed_text(source_text)
    return {
        "vector": vector,
        "model_name": embedding_service.model_name,
        "dimensions": len(vector),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def run_retrieval_with_temporary_upload(
    query_text: str,
    uploaded_record: dict[str, Any],
    uploaded_embedding: dict[str, Any],
    gallery_embedding_path: Path,
    gallery_captions_by_id: dict[str, dict[str, Any]],
    retrieval_mode: str,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Rank the uploaded temporary record alone or alongside the frozen gallery."""
    normalized_query = query_text.strip()
    if not normalized_query:
        raise ValueError("Enter a query before running retrieval with the uploaded image.")

    embedding_service = EmbeddingService()
    if not embedding_service.is_configured():
        raise RuntimeError("OPENAI_API_KEY is not configured, so the query cannot be embedded.")

    query_vector = embedding_service.embed_text(normalized_query)
    uploaded_image_id = str(uploaded_record["image_id"])
    candidate_vectors: dict[str, list[float]] = {
        uploaded_image_id: [float(value) for value in uploaded_embedding["vector"]],
    }

    if retrieval_mode != "Use uploaded image only":
        if not gallery_embedding_path.is_file():
            raise FileNotFoundError(f"Frozen gallery embeddings are missing: {gallery_embedding_path}")
        for record in EmbeddingStore(file_path=gallery_embedding_path).load_all():
            if record.vector and len(record.vector) == len(query_vector):
                candidate_vectors[record.image_id] = record.vector

    comparable_vectors = {
        image_id: vector
        for image_id, vector in candidate_vectors.items()
        if len(vector) == len(query_vector)
    }
    if not comparable_vectors:
        raise RuntimeError("No comparable vectors were available for the selected retrieval mode.")

    ranked_candidates = SimilarityService().rank_candidates(
        query_vector=query_vector,
        candidates=comparable_vectors,
        top_k=top_k,
    )
    uploaded_caption = dict(uploaded_record.get("caption_record", {}))
    results: list[dict[str, Any]] = []
    for rank, (image_id, similarity_score) in enumerate(ranked_candidates, start=1):
        caption_record = uploaded_caption if image_id == uploaded_image_id else gallery_captions_by_id.get(image_id, {})
        image_path = None if image_id == uploaded_image_id else caption_record.get("image_path")
        results.append(
            {
                "query_text": normalized_query,
                "image_id": image_id,
                "image_path": image_path,
                "similarity_score": similarity_score,
                "rank": rank,
                "session_temporary": image_id == uploaded_image_id,
            }
        )

    return results
