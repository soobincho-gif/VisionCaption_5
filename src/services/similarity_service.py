"""Small vector utilities used by retrieval pipelines."""

from __future__ import annotations

import math

from src.core.types import RankedCandidate, Vector


class SimilarityService:
    """Provide deterministic similarity math without storage or provider concerns."""

    def compute_cosine_similarity(self, left: Vector, right: Vector) -> float:
        """Compute cosine similarity for two equally sized vectors."""
        if len(left) != len(right):
            raise ValueError("Cosine similarity requires vectors with equal length.")

        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0

        dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
        return dot_product / (left_norm * right_norm)

    def rank_candidates(
        self,
        query_vector: Vector,
        candidates: dict[str, Vector],
        top_k: int = 3,
    ) -> list[RankedCandidate]:
        """Return the top ranked candidate image IDs and similarity scores."""
        scored_candidates: list[RankedCandidate] = []
        for image_id, candidate_vector in candidates.items():
            score = self.compute_cosine_similarity(query_vector, candidate_vector)
            scored_candidates.append((image_id, score))

        scored_candidates.sort(key=lambda item: item[1], reverse=True)
        return scored_candidates[:top_k]
