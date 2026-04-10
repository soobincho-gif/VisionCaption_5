"""Online search pipeline for the baseline semantic retrieval flow."""

from __future__ import annotations

from src.config.settings import settings
from src.core.schemas import RetrievalResult
from src.services.embedding_service import EmbeddingService
from src.services.similarity_service import SimilarityService
from src.storage.caption_store import CaptionStore
from src.storage.embedding_store import EmbeddingStore


def search(
    query: str,
    top_k: int | None = None,
    caption_store: CaptionStore | None = None,
    embedding_store: EmbeddingStore | None = None,
    embedding_service: EmbeddingService | None = None,
) -> list[RetrievalResult]:
    """Embed the query, rank stored caption embeddings, and return top-k results."""
    normalized_query = query.strip()
    if not normalized_query:
        return []

    requested_top_k = settings.default_top_k if top_k is None else max(0, top_k)
    if requested_top_k == 0:
        return []

    embedding_store = embedding_store or EmbeddingStore()
    embedding_records = embedding_store.load_all()
    if not embedding_records:
        return []

    embedding_service = embedding_service or EmbeddingService()
    if not embedding_service.is_configured():
        raise RuntimeError("Query retrieval requires OPENAI_API_KEY because the query still needs embedding.")

    query_vector = embedding_service.embed_text(normalized_query)
    if not query_vector:
        return []

    candidate_vectors = {
        record.image_id: record.vector
        for record in embedding_records
        if record.vector and len(record.vector) == len(query_vector)
    }
    if not candidate_vectors:
        return []

    similarity_service = SimilarityService()
    ranked_candidates = similarity_service.rank_candidates(
        query_vector=query_vector,
        candidates=candidate_vectors,
        top_k=requested_top_k,
    )

    caption_store = caption_store or CaptionStore()
    caption_lookup = {record.image_id: record for record in caption_store.load_all()}
    results: list[RetrievalResult] = []
    for rank, (image_id, similarity_score) in enumerate(ranked_candidates, start=1):
        caption_record = caption_lookup.get(image_id)
        results.append(
            RetrievalResult(
                query_text=normalized_query,
                image_id=image_id,
                image_path=caption_record.image_path if caption_record else None,
                similarity_score=similarity_score,
                rank=rank,
            )
        )

    return results
