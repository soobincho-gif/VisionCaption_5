"""Offline caption-index pipeline for the semantic retrieval baseline."""

from __future__ import annotations

from pathlib import Path

from src.config.prompts import CaptionPromptVariant
from src.config.settings import settings
from src.core.representation import build_structured_retrieval_text
from src.core.schemas import CaptionRecord
from src.services.vision_caption_service import VisionCaptionService
from src.storage.caption_store import CaptionStore


def discover_image_paths(image_dir: Path | None = None) -> list[Path]:
    """Collect candidate images from the configured raw-data directory."""
    target_dir = image_dir or settings.raw_data_dir
    if not target_dir.exists():
        return []

    supported_suffixes = set(settings.supported_image_extensions)
    iterator = target_dir.rglob("*") if settings.image_discovery_recursive else target_dir.iterdir()
    return sorted(path for path in iterator if path.is_file() and path.suffix.lower() in supported_suffixes)


def build_image_id(image_path: Path, image_root: Path | None = None) -> str:
    """Create a stable image ID from the path relative to the raw image root."""
    image_root = image_root or settings.raw_data_dir
    try:
        relative_path = image_path.resolve().relative_to(image_root.resolve())
    except ValueError:
        relative_path = Path(image_path.name)

    return relative_path.with_suffix("").as_posix().replace("/", "__")


def run_caption_pipeline(
    limit: int | None = None,
    image_dir: Path | None = None,
    store: CaptionStore | None = None,
    prompt_variant: CaptionPromptVariant = "structured_retrieval_v3",
) -> dict[str, object]:
    """Discover images, generate captions, and persist caption records."""
    settings.ensure_output_dirs()
    target_dir = image_dir or settings.raw_data_dir
    store = store or CaptionStore()
    image_paths = discover_image_paths(target_dir)
    if limit is not None:
        image_paths = image_paths[:limit]

    existing_ids = store.list_image_ids()
    pending_image_paths = [path for path in image_paths if build_image_id(path, image_root=target_dir) not in existing_ids]

    summary: dict[str, object] = {
        "status": "completed",
        "image_dir": str(target_dir),
        "images_discovered": len(image_paths),
        "images_skipped_existing": len(image_paths) - len(pending_image_paths),
        "captions_written": 0,
        "caption_output_path": str(store.file_path),
        "prompt_variant": prompt_variant,
        "structured_metadata_enabled": prompt_variant == "structured_retrieval_v3",
        "errors": [],
    }

    if not image_paths:
        summary["status"] = "no_images_found"
        return summary

    if not pending_image_paths:
        summary["status"] = "nothing_to_do"
        return summary

    service = VisionCaptionService(prompt_variant=prompt_variant)
    summary["model_name"] = service.model_name
    if not service.is_configured():
        raise RuntimeError("Caption indexing requires OPENAI_API_KEY because new images still need captions.")

    errors: list[dict[str, str]] = []
    captions_written = 0
    for image_path in pending_image_paths:
        try:
            caption_content = service.generate_caption_content(image_path)
            record = CaptionRecord(
                image_id=build_image_id(image_path, image_root=target_dir),
                image_path=str(image_path.resolve()),
                caption_text=caption_content.caption_text,
                image_type=caption_content.image_type,
                main_subject=caption_content.main_subject,
                visible_objects=caption_content.visible_objects,
                visible_text=caption_content.visible_text,
                layout_blocks=caption_content.layout_blocks,
                distinctive_cues=caption_content.distinctive_cues,
                retrieval_text=build_structured_retrieval_text(caption_content),
                model_name=service.model_name,
            )
            store.save(record)
            captions_written += 1
        except Exception as exc:
            errors.append(
                {
                    "image_path": str(image_path),
                    "error": str(exc),
                }
            )

    summary["captions_written"] = captions_written
    summary["errors"] = errors
    if errors:
        summary["status"] = "completed_with_errors"

    return summary
