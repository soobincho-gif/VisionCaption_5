"""Helpers for the local photo-search demo."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
import json
from pathlib import Path

from src.pipelines.search_images import search
from src.storage.caption_store import CaptionStore
from src.storage.embedding_store import EmbeddingStore
from ui.utils.formatters import normalize_text
from ui.utils.photo_library import get_photo_by_image_id


LOCAL_CAPTION_PATH = Path("outputs/local_search/captions.jsonl")
LOCAL_EMBEDDING_PATH = Path("outputs/local_search/caption_embeddings.caption_plus_selected_structured.jsonl")
SAMPLE_QUERY_REPORT_PATH = Path("outputs/local_search/sample_query_report.json")


@dataclass(frozen=True)
class SampleQueryCase:
    """One curated sample query for the local photo set."""

    key: str
    title: str
    query: str
    expected_image_id: str
    theme: str
    tags: tuple[str, ...]


SAMPLE_QUERY_CASES: tuple[SampleQueryCase, ...] = (
    SampleQueryCase(
        key="sunset_sea",
        title="Sunset over water",
        query="orange sunset over the sea with a small boat",
        expected_image_id="B34835B5-7DEE-4B21-98C9-089C7EE07606_4_5005_c",
        theme="Night & Atmosphere",
        tags=("sunset", "sea", "boat"),
    ),
    SampleQueryCase(
        key="fireworks_leaves",
        title="Fireworks through branches",
        query="fireworks at night behind tree branches",
        expected_image_id="75B0893B-1FA9-4C5D-9EE0-7C65EEC2D627_4_5005_c",
        theme="Night & Atmosphere",
        tags=("fireworks", "night", "branches"),
    ),
    SampleQueryCase(
        key="printed_photos",
        title="Scattered prints",
        query="many printed photographs scattered on a table",
        expected_image_id="8037B247-3410-49F0-BBD2-CC6236902F7C_4_5005_c",
        theme="Quiet Moments",
        tags=("prints", "tabletop", "memories"),
    ),
    SampleQueryCase(
        key="raccoon_indoor",
        title="Raccoon portrait",
        query="raccoon sitting inside a wooden structure",
        expected_image_id="AEA24CE4-A4E5-4402-956D-1A76F24183F2_4_5005_c",
        theme="Curious Encounters",
        tags=("animal", "raccoon", "indoors"),
    ),
    SampleQueryCase(
        key="tower_bridge",
        title="Bridge and river boat",
        query="tower bridge over the river with a boat",
        expected_image_id="F7CEBADB-0613-43D4-BF6A-E2864AD2BC47_4_5005_c",
        theme="Travel & Places",
        tags=("london", "bridge", "boat"),
    ),
    SampleQueryCase(
        key="lava_night",
        title="Night lava flow",
        query="glowing lava flows at night from a volcano",
        expected_image_id="B6183053-6778-4BE6-8663-40412054B20F_4_5005_c",
        theme="Nature & Scale",
        tags=("lava", "volcano", "night"),
    ),
    SampleQueryCase(
        key="snowy_chapel",
        title="Snowy coastal church",
        query="snowy village with a red roof church by the coast",
        expected_image_id="85D46D9E-86E0-4CBD-8588-66CEECE2DA7C_4_5005_c",
        theme="Travel & Places",
        tags=("snow", "church", "coast"),
    ),
    SampleQueryCase(
        key="aurora_sky",
        title="Aurora sky",
        query="green aurora in a starry night sky",
        expected_image_id="821E72E5-C738-4A12-BD4F-B22D31CDA4F0_4_5005_c",
        theme="Night & Atmosphere",
        tags=("aurora", "night", "stars"),
    ),
    SampleQueryCase(
        key="eiffel_olympics",
        title="Eiffel rings",
        query="eiffel tower with olympic rings",
        expected_image_id="AF7CBE38-DAA5-467D-89FE-D80645BD3CBF_1_105_c",
        theme="Travel & Places",
        tags=("paris", "eiffel", "olympic"),
    ),
    SampleQueryCase(
        key="manchester_university",
        title="University facade",
        query="university of manchester stone building archway",
        expected_image_id="FB005307-FD87-4BD5-AC92-1479D47333AD_4_5005_c",
        theme="Travel & Places",
        tags=("manchester", "architecture", "university"),
    ),
)

SAMPLE_QUERIES: tuple[str, ...] = tuple(case.query for case in SAMPLE_QUERY_CASES)


def local_caption_store() -> CaptionStore:
    """Return the caption store used by the local photo demo."""
    return CaptionStore(file_path=LOCAL_CAPTION_PATH)


def local_embedding_store() -> EmbeddingStore:
    """Return the embedding store used by the local photo demo."""
    return EmbeddingStore(file_path=LOCAL_EMBEDDING_PATH)


def local_index_ready() -> bool:
    """Return whether local caption and embedding artifacts exist."""
    return LOCAL_CAPTION_PATH.is_file() and LOCAL_EMBEDDING_PATH.is_file()


@lru_cache(maxsize=64)
def run_local_search(query: str, top_k: int = 3):
    """Search the local photo set with the prepared embedding index."""
    return search(
        query,
        top_k=top_k,
        caption_store=local_caption_store(),
        embedding_store=local_embedding_store(),
    )


def load_caption_lookup() -> dict[str, object]:
    """Load caption records keyed by image id for result rendering."""
    return {record.image_id: record for record in local_caption_store().load_all()}


def load_caption_dict_lookup() -> dict[str, dict[str, object]]:
    """Load caption records as plain dictionaries keyed by image id."""
    return {record.image_id: record.model_dump(mode="json") for record in local_caption_store().load_all()}


def model_summary() -> dict[str, object]:
    """Return a compact summary of the local index."""
    caption_records = local_caption_store().load_all()
    embedding_records = local_embedding_store().load_all()
    embedding_dimensions = len(embedding_records[0].vector) if embedding_records and embedding_records[0].vector else 0
    return {
        "photo_count": len(caption_records),
        "embedding_count": len(embedding_records),
        "embedding_dimensions": embedding_dimensions,
        "titles_available": sum(1 for record in caption_records if get_photo_by_image_id(record.image_id)),
        "sample_query_count": len(SAMPLE_QUERY_CASES),
    }


def find_matching_sample_case(query: str) -> SampleQueryCase | None:
    """Return the sample case whose query exactly matches the given text."""
    normalized_query = normalize_text(query)
    for case in SAMPLE_QUERY_CASES:
        if normalize_text(case.query) == normalized_query:
            return case
    return None


def sample_report_ready() -> bool:
    """Return whether the saved sample-query report exists."""
    return SAMPLE_QUERY_REPORT_PATH.is_file()


def load_sample_query_report() -> dict[str, object]:
    """Load the saved sample-query report from disk."""
    if not SAMPLE_QUERY_REPORT_PATH.is_file():
        return {
            "query_count": 0,
            "recall_at_1": 0.0,
            "tag_accuracy": {},
            "theme_counts": {},
            "queries": [],
        }
    return json.loads(SAMPLE_QUERY_REPORT_PATH.read_text(encoding="utf-8"))


def build_sample_query_report_payload() -> dict[str, object]:
    """Build a compact report payload from the local sample query cases."""
    caption_lookup = load_caption_dict_lookup()
    rows: list[dict[str, object]] = []
    tag_counts: dict[str, int] = {}
    tag_hits: dict[str, int] = {}
    theme_counts: dict[str, int] = {}

    for case in SAMPLE_QUERY_CASES:
        results = [result.model_dump(mode="json") for result in run_local_search(case.query, top_k=3)]
        top_result = results[0] if results else None
        second_result = results[1] if len(results) > 1 else None
        top1_correct = bool(top_result and top_result["image_id"] == case.expected_image_id)
        top1_margin = None
        if top_result and second_result:
            top1_margin = float(top_result["similarity_score"]) - float(second_result["similarity_score"])

        row = {
            "query_id": case.key,
            "title": case.title,
            "query": case.query,
            "expected_image_ids": [case.expected_image_id],
            "tags": list(case.tags),
            "slice": case.theme,
            "results": results,
            "top_result": top_result,
            "top1_correct": top1_correct,
            "top1_margin": top1_margin,
            "query_log": None,
            "expected_photo_title": get_photo_by_image_id(case.expected_image_id).title
            if get_photo_by_image_id(case.expected_image_id)
            else case.expected_image_id,
            "expected_caption": caption_lookup.get(case.expected_image_id, {}).get("caption_text", ""),
        }
        rows.append(row)

        theme_counts[case.theme] = theme_counts.get(case.theme, 0) + 1
        for tag in case.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            if top1_correct:
                tag_hits[tag] = tag_hits.get(tag, 0) + 1

    recall_at_1 = sum(1 for row in rows if row["top1_correct"]) / len(rows) if rows else 0.0
    tag_accuracy = {
        tag: {
            "query_count": count,
            "recall_at_1": tag_hits.get(tag, 0) / count,
        }
        for tag, count in tag_counts.items()
    }

    return {
        "query_count": len(rows),
        "recall_at_1": recall_at_1,
        "tag_accuracy": tag_accuracy,
        "theme_counts": theme_counts,
        "queries": rows,
    }


def save_sample_query_report() -> dict[str, object]:
    """Recompute and save the local sample-query report."""
    payload = build_sample_query_report_payload()
    SAMPLE_QUERY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAMPLE_QUERY_REPORT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def sample_case_lookup() -> dict[str, SampleQueryCase]:
    """Return sample cases keyed by their query id."""
    return {case.key: case for case in SAMPLE_QUERY_CASES}


def sample_case_options() -> list[str]:
    """Return sample query ids in display order."""
    return [case.key for case in SAMPLE_QUERY_CASES]


def sample_case_label(query_id: str) -> str:
    """Return a readable label for one sample query id."""
    case = sample_case_lookup()[query_id]
    return f"{case.title} · {case.query}"
