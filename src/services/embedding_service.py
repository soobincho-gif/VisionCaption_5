"""Service boundary for text embedding generation."""

from __future__ import annotations

from typing import Any

from src.config.settings import settings
from src.core.types import JsonDict, Vector


class EmbeddingService:
    """Hide embedding-provider details behind a small, testable interface."""

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model_name = model_name or settings.embedding_model
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self._client = client

    def is_configured(self) -> bool:
        """Return whether the service has enough configuration to call the provider."""
        return bool(self.api_key or self._client)

    def _get_client(self) -> Any:
        """Lazily construct the OpenAI client only when embeddings are requested."""
        if self._client is not None:
            return self._client

        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to the environment or .env before embedding.")

        from openai import OpenAI

        self._client = OpenAI(api_key=self.api_key)
        return self._client

    def describe_request(self, text: str) -> JsonDict:
        """Return the payload shape used for the baseline embedding request."""
        return {
            "model_name": self.model_name,
            "text": text.strip(),
            "encoding_format": "float",
        }

    def embed_text(self, text: str) -> Vector:
        """Embed one caption or query string into a reusable float vector."""
        normalized_text = text.strip()
        if not normalized_text:
            raise ValueError("Embedding input text cannot be empty.")

        client = self._get_client()
        response = client.embeddings.create(
            model=self.model_name,
            input=normalized_text,
            encoding_format="float",
        )
        if not response.data:
            raise RuntimeError("The embedding API returned no data.")

        vector = response.data[0].embedding
        if not vector:
            raise RuntimeError("The embedding API returned an empty vector.")

        return [float(value) for value in vector]
