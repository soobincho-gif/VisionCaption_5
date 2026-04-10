"""Service boundary for turning an image into a retrieval-friendly caption."""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
import re
from typing import Any

from src.config.prompts import CaptionPromptVariant, build_caption_prompt
from src.config.settings import settings
from src.core.schemas import CaptionContent
from src.core.types import FilePath, JsonDict


class VisionCaptionService:
    """Own the caption-generation contract and hide provider details from pipelines."""

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        prompt_variant: CaptionPromptVariant = "structured_retrieval_v3",
        client: Any | None = None,
    ) -> None:
        self.model_name = model_name or settings.vision_model
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.prompt_variant = prompt_variant
        self._client = client

    def is_configured(self) -> bool:
        """Return whether the service has enough configuration to call the provider."""
        return bool(self.api_key or self._client)

    def _get_client(self) -> Any:
        """Lazily construct the OpenAI client only when caption generation is needed."""
        if self._client is not None:
            return self._client

        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to the environment or .env before captioning.")

        from openai import OpenAI

        self._client = OpenAI(api_key=self.api_key)
        return self._client

    def _build_image_data_url(self, image_path: Path) -> str:
        """Encode a local image file as a data URL for the multimodal request."""
        mime_type, _ = mimetypes.guess_type(image_path.name)
        if mime_type is None:
            mime_type = "image/jpeg"

        encoded_bytes = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        return f"data:{mime_type};base64,{encoded_bytes}"

    def _build_response_input(self, image_path: Path) -> list[JsonDict]:
        """Build the multimodal input payload for one caption request."""
        return [
            {
                "role": "user",
                "type": "message",
                "content": [
                    {
                        "type": "input_text",
                        "text": build_caption_prompt(self.prompt_variant),
                    },
                    {
                        "type": "input_image",
                        "image_url": self._build_image_data_url(image_path),
                        "detail": settings.vision_image_detail,
                    },
                ],
            }
        ]

    def produces_structured_metadata(self) -> bool:
        """Return whether this prompt variant is expected to produce structured JSON."""
        return self.prompt_variant == "structured_retrieval_v3"

    def _extract_json_object(self, response_text: str) -> str:
        """Extract the first JSON object from a model response."""
        normalized_text = response_text.strip()
        fence_pattern = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
        normalized_text = re.sub(fence_pattern, "", normalized_text).strip()

        start_index = normalized_text.find("{")
        end_index = normalized_text.rfind("}")
        if start_index == -1 or end_index == -1 or end_index < start_index:
            raise RuntimeError("The vision model did not return a valid JSON object.")

        return normalized_text[start_index : end_index + 1]

    def _parse_caption_content(self, response_text: str) -> CaptionContent:
        """Parse the model response into normalized caption content."""
        if self.produces_structured_metadata():
            try:
                payload = json.loads(self._extract_json_object(response_text))
            except json.JSONDecodeError as exc:
                raise RuntimeError("The vision model returned malformed JSON for structured caption extraction.") from exc
            return CaptionContent.model_validate(payload)

        return CaptionContent(caption_text=response_text)

    def describe_request(self, image_path: FilePath) -> JsonDict:
        """Return the request shape used for the current caption extraction call."""
        image_path = Path(image_path)
        return {
            "image_path": str(image_path),
            "model_name": self.model_name,
            "prompt_variant": self.prompt_variant,
            "prompt": build_caption_prompt(self.prompt_variant),
            "structured_metadata": self.produces_structured_metadata(),
            "detail": settings.vision_image_detail,
            "max_output_tokens": settings.caption_max_output_tokens,
        }

    def generate_caption_content(self, image_path: FilePath) -> CaptionContent:
        """Generate caption text and optional structured metadata for one image."""
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file does not exist: {image_path}")

        client = self._get_client()
        response_input = self._build_response_input(image_path)

        if self.produces_structured_metadata():
            response = client.responses.parse(
                model=self.model_name,
                input=response_input,
                text_format=CaptionContent,
                max_output_tokens=settings.caption_max_output_tokens,
            )
            if response.output_parsed is not None:
                return response.output_parsed

            response_text = response.output_text.strip()
            if not response_text:
                raise RuntimeError(f"The vision model returned an empty structured caption for {image_path.name}.")
            return self._parse_caption_content(response_text)

        response = client.responses.create(
            model=self.model_name,
            input=response_input,
            max_output_tokens=settings.caption_max_output_tokens,
        )
        response_text = response.output_text.strip()
        if not response_text:
            raise RuntimeError(f"The vision model returned an empty caption for {image_path.name}.")

        return self._parse_caption_content(response_text)

    def generate_caption(self, image_path: FilePath) -> str:
        """Generate only the free-form caption string for one image."""
        return self.generate_caption_content(image_path).caption_text
