"""Local photo metadata used by the simplified portfolio UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PHOTO_ROOT = REPO_ROOT / "data/local_photos"


@dataclass(frozen=True)
class PhotoEntry:
    """Structured metadata for one local photo."""

    key: str
    title: str
    caption: str
    theme: str
    filename: str
    tags: tuple[str, ...]

    @property
    def path(self) -> str:
        """Return the absolute file path for the photo."""
        return str((PHOTO_ROOT / self.filename).resolve())

    @property
    def image_id(self) -> str:
        """Return the image id used by the caption/embedding pipelines."""
        return Path(self.filename).stem


PHOTO_LIBRARY: tuple[PhotoEntry, ...] = (
    PhotoEntry(
        key="sunset_sea",
        title="Sunset at Sea",
        caption="A warm horizon, a low sun, and a small boat holding the edge of the frame.",
        theme="Night & Atmosphere",
        filename="B34835B5-7DEE-4B21-98C9-089C7EE07606_4_5005_c.jpeg",
        tags=("sunset", "sea", "orange"),
    ),
    PhotoEntry(
        key="fireworks_canopy",
        title="Fireworks Through Leaves",
        caption="Bright bursts against a dark sky, partly hidden by nearby branches.",
        theme="Night & Atmosphere",
        filename="75B0893B-1FA9-4C5D-9EE0-7C65EEC2D627_4_5005_c.jpeg",
        tags=("fireworks", "night", "festival"),
    ),
    PhotoEntry(
        key="printed_memories",
        title="Printed Memories",
        caption="A tabletop full of printed snapshots, scattered like a quick travel diary.",
        theme="Quiet Moments",
        filename="8037B247-3410-49F0-BBD2-CC6236902F7C_4_5005_c.jpeg",
        tags=("prints", "memories", "table"),
    ),
    PhotoEntry(
        key="raccoon_hideout",
        title="Raccoon Hideout",
        caption="A raccoon tucked under a wooden structure, framed like a portrait.",
        theme="Curious Encounters",
        filename="AEA24CE4-A4E5-4402-956D-1A76F24183F2_4_5005_c.jpeg",
        tags=("raccoon", "animal", "indoors"),
    ),
    PhotoEntry(
        key="london_river_view",
        title="London River View",
        caption="Bridges, moving water, and a small boat cutting through the center of the city scene.",
        theme="Travel & Places",
        filename="F7CEBADB-0613-43D4-BF6A-E2864AD2BC47_4_5005_c.jpeg",
        tags=("london", "river", "bridge"),
    ),
    PhotoEntry(
        key="lava_flow",
        title="Lava at Night",
        caption="Thin red channels of lava glowing through a dark volcanic landscape.",
        theme="Nature & Scale",
        filename="B6183053-6778-4BE6-8663-40412054B20F_4_5005_c.jpeg",
        tags=("lava", "volcano", "night"),
    ),
    PhotoEntry(
        key="snowy_chapel",
        title="Snowy Coast Chapel",
        caption="A bright chapel and a snowy village sitting below steep coastal cliffs.",
        theme="Travel & Places",
        filename="85D46D9E-86E0-4CBD-8588-66CEECE2DA7C_4_5005_c.jpeg",
        tags=("snow", "coast", "chapel"),
    ),
    PhotoEntry(
        key="aurora_road",
        title="Aurora Roadside",
        caption="Green light stretching across the sky over a dark road and distant homes.",
        theme="Night & Atmosphere",
        filename="821E72E5-C738-4A12-BD4F-B22D31CDA4F0_4_5005_c.jpeg",
        tags=("aurora", "stars", "night"),
    ),
    PhotoEntry(
        key="eiffel_rings",
        title="Eiffel Tower Rings",
        caption="Olympic rings hanging below the Eiffel Tower, framed by leaves above.",
        theme="Travel & Places",
        filename="AF7CBE38-DAA5-467D-89FE-D80645BD3CBF_1_105_c.jpeg",
        tags=("paris", "eiffel", "landmark"),
    ),
    PhotoEntry(
        key="manchester_archway",
        title="Manchester Archway",
        caption="Stone arches and towers with the University of Manchester name in view.",
        theme="Travel & Places",
        filename="FB005307-FD87-4BD5-AC92-1479D47333AD_4_5005_c.jpeg",
        tags=("manchester", "architecture", "campus"),
    ),
)


def get_photo_library() -> tuple[PhotoEntry, ...]:
    """Return the ordered local photo library."""
    return PHOTO_LIBRARY


def get_theme_names() -> list[str]:
    """Return stable theme names in display order."""
    theme_order: list[str] = []
    for photo in PHOTO_LIBRARY:
        if photo.theme not in theme_order:
            theme_order.append(photo.theme)
    return theme_order


def get_photos_for_theme(theme: str) -> list[PhotoEntry]:
    """Return photos matching one theme."""
    return [photo for photo in PHOTO_LIBRARY if photo.theme == theme]


def count_photos_with_tag(tag: str) -> int:
    """Count photos that include one tag."""
    return sum(1 for photo in PHOTO_LIBRARY if tag in photo.tags)


def get_photo_by_image_id(image_id: str) -> PhotoEntry | None:
    """Return one photo entry by its pipeline image id."""
    for photo in PHOTO_LIBRARY:
        if photo.image_id == image_id:
            return photo
    return None
