"""Safe frozen-artifact loaders for the VisionCaption portfolio UI."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
import json
import re
from typing import Any

from ui.utils.formatters import normalize_text

WORD_PATTERN = re.compile(r"[a-z0-9]+")
REPO_ROOT = Path(__file__).resolve().parents[2]
PORTABLE_PATH_ANCHORS = ("data", "outputs")


class ArtifactLoadError(RuntimeError):
    """Raised when a required frozen artifact is missing or malformed."""


@dataclass(frozen=True)
class ConfigSpec:
    """Describe one UI-exposed configuration for a benchmark."""

    key: str
    label: str
    short_label: str
    description: str
    artifact_path: str
    comparison_path: str | None = None
    query_logs_path: str | None = None
    previous_key: str | None = None
    representation_mode: str = "caption_only"
    stage: str = "baseline"


@dataclass(frozen=True)
class ConfigArtifacts:
    """Loaded frozen artifacts for one benchmark/config combination."""

    spec: ConfigSpec
    results: dict[str, Any]
    comparison: dict[str, Any] | None
    query_logs_by_id: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class BenchmarkSpec:
    """Describe one benchmark surfaced in the app."""

    key: str
    label: str
    description: str
    benchmark_path: str
    configs: tuple[ConfigSpec, ...]


@dataclass(frozen=True)
class BenchmarkBundle:
    """Fully loaded benchmark data plus normalized indexes."""

    spec: BenchmarkSpec
    benchmark: dict[str, Any]
    images_by_id: dict[str, dict[str, Any]]
    queries_by_id: dict[str, dict[str, Any]]
    query_order: list[str]
    configs: dict[str, ConfigArtifacts]


@dataclass(frozen=True)
class PortfolioArtifacts:
    """Top-level data bundle used by the multipage UI."""

    repo_root: Path
    promotion_summary: dict[str, Any]
    mixed_validation_report: dict[str, Any]
    captions_by_id: dict[str, dict[str, Any]]
    benchmarks: dict[str, BenchmarkBundle]


HARD_BENCHMARK = BenchmarkSpec(
    key="hard",
    label="Hard Benchmark",
    description="The curated hard benchmark used to promote the stronger default.",
    benchmark_path="data/samples/prompt_fidelity/benchmark.json",
    configs=(
        ConfigSpec(
            key="baseline",
            label="Baseline",
            short_label="Baseline",
            description="Caption-only retrieval over the frozen hard benchmark.",
            artifact_path="outputs/eval/control_candidate_name_text_fidelity/caption_only/results.json",
            representation_mode="caption_only",
            stage="baseline",
        ),
        ConfigSpec(
            key="candidate",
            label="Candidate",
            short_label="Candidate",
            description="Structured representation with selected fields, before rerank.",
            artifact_path="outputs/eval/control_candidate_name_text_fidelity/caption_plus_selected_structured/results.json",
            previous_key="baseline",
            representation_mode="caption_plus_selected_structured",
            stage="candidate",
        ),
        ConfigSpec(
            key="final_default",
            label="Final Default",
            short_label="Final",
            description="Structured representation plus deterministic top-3 rerank with paraphrase overlap.",
            artifact_path="outputs/eval/deterministic_top3_rerank_q021_question_paraphrase/results.json",
            comparison_path="outputs/eval/deterministic_top3_rerank_q021_question_paraphrase/comparison.json",
            query_logs_path="outputs/eval/deterministic_top3_rerank_q021_question_paraphrase/query_logs.jsonl",
            previous_key="candidate",
            representation_mode="caption_plus_selected_structured",
            stage="final_default",
        ),
    ),
)

MIXED_SANITY_BENCHMARK = BenchmarkSpec(
    key="mixed_sanity",
    label="Mixed Sanity",
    description="The broader frozen replay validation set used to confirm the promoted default.",
    benchmark_path="data/samples/prompt_fidelity/benchmark_mixed_sanity_v1.json",
    configs=(
        ConfigSpec(
            key="baseline",
            label="Baseline",
            short_label="Baseline",
            description="Caption-only retrieval over the validated mixed-sanity replay set.",
            artifact_path=(
                "outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/"
                "mixed_sanity_v1/control_candidate/caption_only/results.json"
            ),
            representation_mode="caption_only",
            stage="baseline",
        ),
        ConfigSpec(
            key="candidate",
            label="Candidate",
            short_label="Candidate",
            description="Structured representation with selected fields, before rerank.",
            artifact_path=(
                "outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/"
                "mixed_sanity_v1/control_candidate/caption_plus_selected_structured/results.json"
            ),
            previous_key="baseline",
            representation_mode="caption_plus_selected_structured",
            stage="candidate",
        ),
        ConfigSpec(
            key="final_default",
            label="Final Default",
            short_label="Final",
            description="The promoted broader default: structured representation plus deterministic rerank.",
            artifact_path=(
                "outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/"
                "mixed_sanity_v1/candidate_rerank_with_paraphrase/results.json"
            ),
            comparison_path=(
                "outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/"
                "mixed_sanity_v1/candidate_rerank_with_paraphrase/comparison.json"
            ),
            query_logs_path=(
                "outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/"
                "mixed_sanity_v1/candidate_rerank_with_paraphrase/query_logs.jsonl"
            ),
            previous_key="candidate",
            representation_mode="caption_plus_selected_structured",
            stage="final_default",
        ),
    ),
)

BENCHMARK_SPECS = {spec.key: spec for spec in (HARD_BENCHMARK, MIXED_SANITY_BENCHMARK)}
PROMOTION_SUMMARY_PATH = (
    "outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/"
    "mixed_sanity_v1/default_promotion_summary.json"
)
MIXED_VALIDATION_REPORT_PATH = (
    "outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/mixed_sanity_v1/report.json"
)
CAPTIONS_PATH = "outputs/eval/structured_representation/captions.jsonl"


def repo_path(relative_path: str | Path) -> Path:
    """Resolve a repository-relative path."""
    return (REPO_ROOT / Path(relative_path)).resolve()


def portable_artifact_path(path_value: str | Path) -> str:
    """Resolve artifact-stored paths so old local absolute paths still work after deploy."""
    path_text = str(path_value).strip()
    if not path_text or "://" in path_text:
        return path_text

    path = Path(path_text)
    if not path.is_absolute():
        return str(repo_path(path))

    parts = path.parts
    for anchor in PORTABLE_PATH_ANCHORS:
        if anchor in parts:
            return str(repo_path(Path(*parts[parts.index(anchor) :])))
    return str(path)


def _normalize_paths_in_payload(value: Any) -> Any:
    """Recursively rewrite JSON path fields to deploy-safe repository paths."""
    if isinstance(value, list):
        return [_normalize_paths_in_payload(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if isinstance(item, str) and (key == "image_path" or key.endswith("_path")):
                normalized[key] = portable_artifact_path(item)
            else:
                normalized[key] = _normalize_paths_in_payload(item)
        return normalized
    return value


def require_file(relative_path: str | Path) -> Path:
    """Resolve a required file and fail clearly when it is missing."""
    path = repo_path(relative_path)
    if not path.is_file():
        raise ArtifactLoadError(
            f"Required artifact is missing: {path}\n"
            "The portfolio UI only supports the validated frozen replay package."
        )
    return path


def read_json(relative_path: str | Path) -> dict[str, Any]:
    """Load a JSON artifact from disk."""
    path = require_file(relative_path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(f"Malformed JSON artifact: {path}") from exc


def read_jsonl(relative_path: str | Path) -> list[dict[str, Any]]:
    """Load a JSONL artifact from disk."""
    path = require_file(relative_path)
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ArtifactLoadError(f"Malformed JSONL artifact at {path}:{line_number}") from exc
    return records


def _normalize_benchmark_query(raw_query: dict[str, Any]) -> dict[str, Any]:
    """Normalize benchmark query shape into one consistent mapping."""
    query = dict(raw_query)
    query_id = str(query.pop("id", query.get("query_id", "")))
    query["query_id"] = query_id
    query["expected_image_ids"] = [str(item) for item in query.get("expected_image_ids", [])]
    query["tags"] = [str(item) for item in query.get("tags", [])]
    query["hard_negative_image_ids"] = [str(item) for item in query.get("hard_negative_image_ids", [])]
    query["slice"] = str(query.get("slice") or _derive_slice_from_tags(query["tags"]))
    return query


def _derive_slice_from_tags(tags: list[str]) -> str:
    """Infer a benchmark slice when older hard-benchmark fixtures omit one."""
    tag_set = set(tags)
    if "photo_scene" in tag_set or "illustration_style" in tag_set:
        return "photo_or_illustration"
    if "hard_negative" in tag_set or "ui_family_disambiguation" in tag_set:
        return "hard_ui"
    return "normal_ui"


def _normalize_benchmark_images(benchmark: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Attach absolute file paths to benchmark image metadata."""
    image_dir = repo_path(benchmark.get("image_dir", ""))
    images_by_id: dict[str, dict[str, Any]] = {}
    for image in benchmark.get("images", []):
        normalized = dict(image)
        normalized["image_path"] = str((image_dir / image["filename"]).resolve())
        images_by_id[image["image_id"]] = normalized
    return images_by_id


def _load_config_artifacts(spec: ConfigSpec) -> ConfigArtifacts:
    """Load one config's result, comparison, and query-log artifacts."""
    results = _normalize_paths_in_payload(read_json(spec.artifact_path))
    comparison = _normalize_paths_in_payload(read_json(spec.comparison_path)) if spec.comparison_path else None
    query_logs = _normalize_paths_in_payload(read_jsonl(spec.query_logs_path)) if spec.query_logs_path else []
    query_logs_by_id = {entry["query_id"]: entry for entry in query_logs}
    return ConfigArtifacts(
        spec=spec,
        results=results,
        comparison=comparison,
        query_logs_by_id=query_logs_by_id,
    )


def _load_benchmark_bundle(spec: BenchmarkSpec) -> BenchmarkBundle:
    """Load one benchmark's metadata plus all UI-exposed configurations."""
    benchmark = read_json(spec.benchmark_path)
    queries = [_normalize_benchmark_query(query) for query in benchmark.get("queries", [])]
    return BenchmarkBundle(
        spec=spec,
        benchmark=benchmark,
        images_by_id=_normalize_benchmark_images(benchmark),
        queries_by_id={query["query_id"]: query for query in queries},
        query_order=[query["query_id"] for query in queries],
        configs={config.key: _load_config_artifacts(config) for config in spec.configs},
    )


def _load_captions_by_id() -> dict[str, dict[str, Any]]:
    """Load caption records keyed by image id."""
    return {
        record["image_id"]: record
        for record in _normalize_paths_in_payload(read_jsonl(CAPTIONS_PATH))
    }


@lru_cache(maxsize=1)
def load_portfolio_artifacts() -> PortfolioArtifacts:
    """Load and cache the full artifact bundle needed by the UI."""
    return PortfolioArtifacts(
        repo_root=REPO_ROOT,
        promotion_summary=read_json(PROMOTION_SUMMARY_PATH),
        mixed_validation_report=read_json(MIXED_VALIDATION_REPORT_PATH),
        captions_by_id=_load_captions_by_id(),
        benchmarks={spec.key: _load_benchmark_bundle(spec) for spec in BENCHMARK_SPECS.values()},
    )


def get_representation_text(caption_record: dict[str, Any], representation_mode: str) -> str:
    """Return the text representation used by a selected config."""
    if representation_mode == "caption_only":
        return str(caption_record.get("caption_text", "")).strip()
    return str(caption_record.get("retrieval_text") or caption_record.get("caption_text", "")).strip()


def get_config_metrics(config_artifacts: ConfigArtifacts) -> dict[str, Any]:
    """Return a normalized metrics mapping across config artifact shapes."""
    if "recall_at_1" in config_artifacts.results:
        return config_artifacts.results
    return dict(config_artifacts.results.get("after_metrics", {}))


def build_query_rows(bundle: BenchmarkBundle, config_key: str) -> list[dict[str, Any]]:
    """Merge benchmark metadata and top-k results into a table-friendly row list."""
    config_artifacts = bundle.configs[config_key]
    result_queries = {
        query["query_id"]: dict(query)
        for query in config_artifacts.results.get("queries", [])
    }
    rows: list[dict[str, Any]] = []
    for query_id in bundle.query_order:
        benchmark_query = dict(bundle.queries_by_id[query_id])
        result_query = dict(result_queries.get(query_id, {}))
        results = list(result_query.get("results", []))
        if not results:
            results = list(result_query.get("reranked_results", []))
        if not results:
            results = list(result_query.get("top_results", []))
        results = [_normalize_result_image_path(result, bundle.images_by_id) for result in results]
        expected_image_ids = benchmark_query.get("expected_image_ids", [])
        top_result = results[0] if results else None
        second_result = results[1] if len(results) > 1 else None
        top1_correct = bool(top_result and top_result.get("image_id") in expected_image_ids)
        margin = None
        if top_result and second_result:
            margin = float(top_result["similarity_score"]) - float(second_result["similarity_score"])
        rows.append(
            {
                **benchmark_query,
                **result_query,
                "query_id": query_id,
                "results": results,
                "top_result": top_result,
                "second_result": second_result,
                "top1_correct": top1_correct,
                "top1_margin": margin,
                "failure_bucket": derive_failure_bucket(
                    tags=benchmark_query.get("tags", []),
                    top1_correct=top1_correct,
                    top_result_image_id=top_result.get("image_id") if top_result else None,
                    hard_negative_image_ids=benchmark_query.get("hard_negative_image_ids", []),
                ),
                "query_log": config_artifacts.query_logs_by_id.get(query_id),
            }
        )
    return rows


def _normalize_result_image_path(
    result: dict[str, Any],
    images_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Prefer deploy-safe benchmark image paths over stale artifact-local paths."""
    normalized = dict(result)
    image_id = str(normalized.get("image_id") or "")
    if image_id in images_by_id:
        normalized["image_path"] = images_by_id[image_id]["image_path"]
    elif normalized.get("image_path"):
        normalized["image_path"] = portable_artifact_path(str(normalized["image_path"]))
    return normalized


def derive_failure_bucket(
    tags: list[str],
    top1_correct: bool,
    top_result_image_id: str | None,
    hard_negative_image_ids: list[str],
) -> str:
    """Assign one primary failure bucket for filtering and table views."""
    if top1_correct:
        return "Correct"
    tag_set = set(tags)
    if "person_name" in tag_set:
        return "Person-name confusion"
    if "visible_text" in tag_set:
        return "Visible-text confusion"
    if "layout_structure" in tag_set:
        return "Layout confusion"
    if top_result_image_id and top_result_image_id in set(hard_negative_image_ids):
        return "Same-family UI confusion"
    if "paraphrase" in tag_set:
        return "Paraphrase miss"
    if "illustration_style" in tag_set:
        return "Illustration mismatch"
    if "photo_scene" in tag_set:
        return "Photo scene mismatch"
    return "Other retrieval miss"


def tokenize(value: str) -> set[str]:
    """Tokenize text into lowercase alphanumeric terms."""
    return {token for token in WORD_PATTERN.findall(normalize_text(value))}


def resolve_replay_query(query_text: str, bundle: BenchmarkBundle) -> tuple[dict[str, Any], dict[str, Any]]:
    """Map free text to the closest frozen benchmark query for offline-safe replay."""
    normalized_input = normalize_text(query_text)
    if not normalized_input:
        first_query = bundle.queries_by_id[bundle.query_order[0]]
        return first_query, {"exact_match": True, "score": 1.0, "matched_query_id": first_query["query_id"]}

    input_tokens = tokenize(normalized_input)
    best_query = bundle.queries_by_id[bundle.query_order[0]]
    best_score = -1.0
    exact_match = False

    for query in bundle.queries_by_id.values():
        candidate_text = query["query"]
        normalized_candidate = normalize_text(candidate_text)
        candidate_tokens = tokenize(candidate_text)
        token_overlap = 0.0
        if input_tokens or candidate_tokens:
            token_overlap = len(input_tokens & candidate_tokens) / max(len(input_tokens | candidate_tokens), 1)
        phrase_similarity = SequenceMatcher(None, normalized_input, normalized_candidate).ratio()
        score = (token_overlap * 0.7) + (phrase_similarity * 0.3)
        if normalized_input == normalized_candidate:
            score = 2.0
        if score > best_score:
            best_query = query
            best_score = score
            exact_match = normalized_input == normalized_candidate

    return best_query, {
        "exact_match": exact_match,
        "score": round(best_score, 4),
        "matched_query_id": best_query["query_id"],
    }


def lookup_previous_config(bundle: BenchmarkBundle, config_key: str) -> ConfigArtifacts | None:
    """Return the previous config in the staged progression, when available."""
    current = bundle.configs[config_key]
    if current.spec.previous_key is None:
        return None
    return bundle.configs[current.spec.previous_key]
