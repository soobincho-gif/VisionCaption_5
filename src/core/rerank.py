"""Deterministic top-k rerank helpers for benchmark ablations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

from src.core.schemas import CaptionRecord

WORD_PATTERN = re.compile(r"[a-z0-9]+")
VISIBLE_TEXT_SEPARATOR_PATTERN = re.compile(r"\s*(?:\n+|\|+|•|·|(?:\.\s*){2,}|…|;+|→|->)\s*")
VISIBLE_TEXT_SECTION_PATTERN = re.compile(
    r"(?=\b(?:"
    r"Image \d+|Sequence Memory|Event Candidates|Unresolved Ambiguities|"
    r"Evaluation Report|Pipeline Refinement Status|Generator Compliance Scores|"
    r"Flags / Warnings|Evaluator Summary|CURRENT PERSPECTIVE|LATEST PIPELINE RESULT|"
    r"Session summary|QUESTION TYPE|Question type|Answer Mode|Verification pass|"
    r"Scene Observations|Generated Story|Title"
    r")\b)"
)
NAME_PATTERN = re.compile(r"\b(?:[A-Z][a-z]+|[IVXLCDM]+)(?:\s+(?:[A-Z][a-z]+|[IVXLCDM]+)){1,3}\b")
ROMAN_NUMERAL_PATTERN = re.compile(r"^[IVXLCDM]+$")
QUERY_STOPWORDS: set[str] = {
    "a",
    "about",
    "an",
    "and",
    "app",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "chat",
    "do",
    "for",
    "from",
    "here",
    "in",
    "into",
    "interface",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "page",
    "rather",
    "screen",
    "than",
    "that",
    "the",
    "this",
    "to",
    "today",
    "what",
    "with",
    "you",
    "your",
}
ENTITY_STOPWORDS: set[str] = {
    "active",
    "answer",
    "candidates",
    "current",
    "dashboard",
    "evaluation",
    "evaluator",
    "figure",
    "flags",
    "generate",
    "generated",
    "generator",
    "historical",
    "image",
    "images",
    "interface",
    "issues",
    "latest",
    "memory",
    "mind",
    "multi-turn",
    "none",
    "observations",
    "perspective",
    "persona",
    "pipeline",
    "question",
    "report",
    "result",
    "salon",
    "scene",
    "selection",
    "sentiment",
    "sequence",
    "session",
    "snapshot",
    "status",
    "story",
    "storytelling",
    "summary",
    "transcript",
    "verification",
    "verify",
    "visual",
    "warnings",
}
INTERFACE_IMAGE_TYPE_KEYWORDS: set[str] = {"ui", "screenshot", "dashboard", "slide"}
COMPONENT_TERMS: set[str] = {
    "area",
    "bar",
    "box",
    "button",
    "buttons",
    "card",
    "dropdown",
    "field",
    "form",
    "input",
    "menu",
    "panel",
    "preview",
    "radio",
    "section",
    "sections",
    "slider",
    "status",
    "upload",
}
LOW_SIGNAL_SINGLETON_COMPONENT_TERMS: set[str] = {
    "area",
    "box",
    "panel",
    "section",
    "sections",
}
QUESTION_LIKE_PREFIXES: tuple[str, ...] = (
    "what ",
    "how ",
    "why ",
    "would ",
    "should ",
    "could ",
    "can ",
    "is ",
    "are ",
)
QUESTION_PARAPHRASE_LOW_SIGNAL_TOKENS: set[str] = {
    "ai",
    "app",
    "chat",
    "figure",
    "historical",
    "interface",
    "screen",
    "transcript",
    "ui",
}


@dataclass(frozen=True)
class DeterministicRerankWeights:
    """Explicit rerank weights kept small and easy to edit."""

    exact_visible_text_overlap: float = 1.2
    named_entity_match: float = 1.5
    label_value_phrase_overlap: float = 2.0
    component_cue_overlap: float = 1.3
    question_paraphrase_overlap: float = 0.0
    original_similarity: float = 0.25

    def as_dict(self) -> dict[str, float]:
        """Return a JSON-friendly view of the configured weights."""
        return asdict(self)


DEFAULT_DETERMINISTIC_RERANK_WEIGHTS = DeterministicRerankWeights()


def _normalize_text(value: str | None) -> str:
    """Collapse text into a stable lowercase form for exact matching."""
    return " ".join(str(value or "").lower().split())


def _tokenize(value: str) -> list[str]:
    """Tokenize user-facing text while removing generic glue words."""
    return [token for token in WORD_PATTERN.findall(_normalize_text(value)) if token not in QUERY_STOPWORDS]


def _tokenize_question_paraphrase(value: str) -> list[str]:
    """Tokenize question-like cues while dropping generic interface/topic words."""
    return [
        token
        for token in _tokenize(value)
        if token not in QUESTION_PARAPHRASE_LOW_SIGNAL_TOKENS
    ]


def _split_visible_text_item(value: str) -> list[str]:
    """Recover short cues from overlong OCR-like visible-text strings."""
    fragments = [_normalize_text(value)]
    for pattern in (VISIBLE_TEXT_SECTION_PATTERN, VISIBLE_TEXT_SEPARATOR_PATTERN):
        next_fragments: list[str] = []
        for fragment in fragments:
            pieces = [
                _normalize_text(piece.strip(" -|"))
                for piece in pattern.split(fragment)
                if _normalize_text(piece.strip(" -|"))
            ]
            next_fragments.extend(pieces if len(pieces) > 1 else [fragment])
        fragments = next_fragments

    deduped_fragments: list[str] = []
    for fragment in fragments:
        if len(fragment) < 4 or fragment in deduped_fragments:
            continue
        deduped_fragments.append(fragment)

    return deduped_fragments


def _looks_like_interface(record: CaptionRecord) -> bool:
    """Restrict UI-style features to interface-like records."""
    image_type = _normalize_text(record.image_type)
    if any(keyword in image_type for keyword in INTERFACE_IMAGE_TYPE_KEYWORDS):
        return True
    return bool(record.layout_blocks)


def extract_exact_text_cues(record: CaptionRecord) -> list[str]:
    """Return compact visible-text cues for exact phrase overlap."""
    prioritized_fragments: list[str] = []
    regular_fragments: list[str] = []
    for visible_text_item in record.visible_text:
        fragments = _split_visible_text_item(visible_text_item)
        if len(fragments) > 1 or len(visible_text_item) > 80 or "?" in visible_text_item:
            prioritized_fragments.extend(fragments)
            continue
        regular_fragments.extend(fragments)

    exact_text_cues: list[str] = []
    for fragment in prioritized_fragments:
        if "." in fragment and "?" not in fragment:
            continue
        if "," in fragment and "?" not in fragment:
            continue
        if "?" not in fragment and len(fragment.split()) > 8:
            continue
        if fragment not in exact_text_cues:
            exact_text_cues.append(fragment)

    for fragment in regular_fragments:
        if len(fragment) > 90 and "?" not in fragment:
            continue
        if fragment not in exact_text_cues:
            exact_text_cues.append(fragment)

    return exact_text_cues[:20]


def extract_named_entity_aliases(record: CaptionRecord) -> list[str]:
    """Return entity names plus lightweight aliases for person-like references."""
    named_entities: list[str] = []
    for source_text in (record.main_subject or "", record.caption_text):
        for match in NAME_PATTERN.finditer(source_text):
            entity = " ".join(match.group(0).split())
            entity_tokens = entity.split()
            if len(entity_tokens) < 2:
                continue
            if any(token.lower() in ENTITY_STOPWORDS for token in entity_tokens):
                continue

            normalized_entity = entity.lower()
            if normalized_entity not in named_entities:
                named_entities.append(normalized_entity)

            if len(entity_tokens) == 2:
                alias = entity_tokens[-1].lower()
                if alias not in named_entities:
                    named_entities.append(alias)
            elif len(entity_tokens) >= 3 and ROMAN_NUMERAL_PATTERN.match(entity_tokens[1]):
                alias = " ".join(entity_tokens[:2]).lower()
                short_alias = entity_tokens[0].lower()
                if alias not in named_entities:
                    named_entities.append(alias)
                if short_alias not in named_entities:
                    named_entities.append(short_alias)

    return named_entities[:8]


def extract_label_value_phrases(record: CaptionRecord) -> list[str]:
    """Recover compact label-value phrases from visible UI text."""
    exact_text_cues = extract_exact_text_cues(record)
    label_value_phrases: list[str] = []
    for index, exact_text_cue in enumerate(exact_text_cues[:-1]):
        if exact_text_cue == "question type":
            label_value_phrases.append(f"question type {exact_text_cues[index + 1]}")
        if exact_text_cue == "answer mode":
            label_value_phrases.append(f"answer mode {exact_text_cues[index + 1]}")

    text_blob = _normalize_text(" ".join(exact_text_cues + record.visible_text))
    for match in re.finditer(r"question type ([a-z ]+?) answer mode", text_blob):
        label_value_phrases.append(f"question type {match.group(1).strip()}")
    for match in re.finditer(r"answer mode ([a-z ]+?)(?: verification pass| verifier issues| memory state|$)", text_blob):
        label_value_phrases.append(f"answer mode {match.group(1).strip()}")

    for phrase in (
        "pipeline refinement status",
        "latest pipeline result",
        "current perspective",
        "session summary",
        "scene observations",
        "generated story",
        "title",
    ):
        if phrase in text_blob:
            label_value_phrases.append(phrase)

    deduped_phrases: list[str] = []
    for phrase in label_value_phrases:
        normalized_phrase = _normalize_text(phrase)
        if not normalized_phrase or normalized_phrase in deduped_phrases:
            continue
        deduped_phrases.append(normalized_phrase)

    return deduped_phrases


def build_rerank_feature_bundle(record: CaptionRecord) -> dict[str, Any]:
    """Collect deterministic rerank cues for one candidate record."""
    return {
        "looks_like_interface": _looks_like_interface(record),
        "exact_text_cues": extract_exact_text_cues(record),
        "named_entity_aliases": extract_named_entity_aliases(record),
        "label_value_phrases": extract_label_value_phrases(record),
        "component_cues": list(record.visible_objects),
    }


def _phrase_overlap_ratio(query_text: str, candidate_phrase: str) -> float:
    """Return query-token coverage over a candidate-side phrase."""
    query_tokens = set(_tokenize(query_text))
    phrase_tokens = set(_tokenize(candidate_phrase))
    if not query_tokens or not phrase_tokens:
        return 0.0

    overlap = query_tokens & phrase_tokens
    if not overlap:
        return 0.0

    return len(overlap) / len(phrase_tokens)


def _score_exact_visible_text_overlap(
    query_text: str,
    feature_bundle: dict[str, Any],
) -> tuple[float, list[str]]:
    """Count exact or keyword-level visible-text matches for UI-like candidates."""
    if not feature_bundle["looks_like_interface"]:
        return 0.0, []

    query_normalized = _normalize_text(query_text)
    query_tokens = set(_tokenize(query_text))
    entity_terms = set()
    for entity in feature_bundle["named_entity_aliases"]:
        entity_terms.update(entity.split())

    matched_terms: list[str] = []
    score = 0.0
    for exact_text_cue in feature_bundle["exact_text_cues"]:
        cue_tokens = _tokenize(exact_text_cue)
        if not cue_tokens:
            continue
        if set(cue_tokens).issubset(entity_terms):
            continue
        if "interface" in cue_tokens and len(cue_tokens) <= 3:
            continue

        if exact_text_cue in query_normalized:
            score += 1.0
            matched_terms.append(exact_text_cue)
            continue

        if len(cue_tokens) == 1 and len(cue_tokens[0]) >= 4 and cue_tokens[0] in query_tokens:
            score += 1.0
            matched_terms.append(exact_text_cue)

    return score, matched_terms


def _score_named_entity_match(
    query_text: str,
    feature_bundle: dict[str, Any],
) -> tuple[float, list[str]]:
    """Count exact entity or alias mentions in the query."""
    query_normalized = _normalize_text(query_text)
    matched_entities = [
        entity
        for entity in feature_bundle["named_entity_aliases"]
        if entity in query_normalized
    ]
    return float(len(matched_entities)), matched_entities


def _score_label_value_phrase_overlap(
    query_text: str,
    feature_bundle: dict[str, Any],
) -> tuple[float, list[str]]:
    """Score label-value phrases when the query explicitly names UI state."""
    if not feature_bundle["looks_like_interface"]:
        return 0.0, []

    score = 0.0
    matched_phrases: list[str] = []
    for label_value_phrase in feature_bundle["label_value_phrases"]:
        overlap_ratio = _phrase_overlap_ratio(query_text, label_value_phrase)
        overlap_count = len(set(_tokenize(query_text)) & set(_tokenize(label_value_phrase)))
        if overlap_ratio < 0.5 or overlap_count < 2:
            continue
        score += overlap_ratio
        matched_phrases.append(label_value_phrase)

    return score, matched_phrases


def _score_component_cue_overlap(
    query_text: str,
    feature_bundle: dict[str, Any],
) -> tuple[float, list[str]]:
    """Score UI component overlap using only shared component-like words."""
    if not feature_bundle["looks_like_interface"]:
        return 0.0, []

    query_tokens = set(_tokenize(query_text))
    score = 0.0
    matched_component_cues: list[str] = []
    for component_cue in feature_bundle["component_cues"]:
        component_tokens = [token for token in _tokenize(component_cue) if token in COMPONENT_TERMS]
        component_token_set = set(component_tokens)
        if not component_token_set:
            continue
        if (
            len(component_token_set) == 1
            and next(iter(component_token_set)) in LOW_SIGNAL_SINGLETON_COMPONENT_TERMS
        ):
            continue

        overlap = query_tokens & component_token_set
        if not overlap:
            continue

        score += len(overlap) / len(component_token_set)
        matched_component_cues.append(component_cue)

    return score, matched_component_cues


def _score_question_paraphrase_overlap(
    query_text: str,
    feature_bundle: dict[str, Any],
) -> tuple[float, list[str]]:
    """Score question-like visible-text cues when they share multiple content words with the query."""
    if not feature_bundle["looks_like_interface"]:
        return 0.0, []

    query_tokens = set(_tokenize_question_paraphrase(query_text))
    if len(query_tokens) < 2:
        return 0.0, []

    best_score = 0.0
    best_overlap_terms: list[str] = []
    for exact_text_cue in feature_bundle["exact_text_cues"]:
        normalized_cue = _normalize_text(exact_text_cue)
        if "?" not in normalized_cue and not normalized_cue.startswith(QUESTION_LIKE_PREFIXES):
            continue

        cue_tokens = set(_tokenize_question_paraphrase(normalized_cue))
        overlap_terms = sorted(query_tokens & cue_tokens)
        if len(overlap_terms) < 2:
            continue

        raw_score = len(overlap_terms) / len(query_tokens)
        if raw_score > best_score:
            best_score = raw_score
            best_overlap_terms = overlap_terms

    return best_score, best_overlap_terms


def _build_feature_contribution(
    feature_name: str,
    raw_score: float,
    matched_terms: list[str],
    weights: DeterministicRerankWeights,
) -> dict[str, Any]:
    """Format one feature's raw and weighted contribution for logging."""
    weight = getattr(weights, feature_name)
    return {
        "raw_score": raw_score,
        "weight": weight,
        "weighted_score": raw_score * weight,
        "matched_terms": matched_terms,
    }


def score_candidate_for_query(
    query_text: str,
    result: dict[str, Any],
    record: CaptionRecord,
    weights: DeterministicRerankWeights = DEFAULT_DETERMINISTIC_RERANK_WEIGHTS,
) -> dict[str, Any]:
    """Score one ranked candidate against one query using explicit rerank features."""
    feature_bundle = build_rerank_feature_bundle(record)
    exact_visible_text_score, exact_visible_text_matches = _score_exact_visible_text_overlap(query_text, feature_bundle)
    named_entity_score, named_entity_matches = _score_named_entity_match(query_text, feature_bundle)
    label_value_score, label_value_matches = _score_label_value_phrase_overlap(query_text, feature_bundle)
    component_cue_score, component_cue_matches = _score_component_cue_overlap(query_text, feature_bundle)
    question_paraphrase_score, question_paraphrase_matches = _score_question_paraphrase_overlap(
        query_text,
        feature_bundle,
    )

    feature_contributions = {
        "exact_visible_text_overlap": _build_feature_contribution(
            "exact_visible_text_overlap",
            exact_visible_text_score,
            exact_visible_text_matches,
            weights,
        ),
        "named_entity_match": _build_feature_contribution(
            "named_entity_match",
            named_entity_score,
            named_entity_matches,
            weights,
        ),
        "label_value_phrase_overlap": _build_feature_contribution(
            "label_value_phrase_overlap",
            label_value_score,
            label_value_matches,
            weights,
        ),
        "component_cue_overlap": _build_feature_contribution(
            "component_cue_overlap",
            component_cue_score,
            component_cue_matches,
            weights,
        ),
        "question_paraphrase_overlap": _build_feature_contribution(
            "question_paraphrase_overlap",
            question_paraphrase_score,
            question_paraphrase_matches,
            weights,
        ),
        "original_similarity": _build_feature_contribution(
            "original_similarity",
            float(result["similarity_score"]),
            [],
            weights,
        ),
    }
    rerank_score = sum(contribution["weighted_score"] for contribution in feature_contributions.values())

    return {
        "image_id": result["image_id"],
        "image_path": result.get("image_path"),
        "original_rank": int(result["rank"]),
        "original_similarity_score": float(result["similarity_score"]),
        "rerank_score": rerank_score,
        "feature_bundle": feature_bundle,
        "feature_contributions": feature_contributions,
    }


def determine_rerank_activation_reasons(candidate_logs: list[dict[str, Any]]) -> list[str]:
    """Only activate reranking when the query exposes supported rerank signals."""
    activation_reasons: list[str] = []
    if any(
        candidate_log["feature_contributions"]["label_value_phrase_overlap"]["raw_score"] > 0
        for candidate_log in candidate_logs
    ):
        activation_reasons.append("label_value_phrase_overlap")
    if any(
        candidate_log["feature_contributions"]["component_cue_overlap"]["raw_score"] > 0
        for candidate_log in candidate_logs
    ):
        activation_reasons.append("component_cue_overlap")
    if any(
        candidate_log["feature_contributions"]["exact_visible_text_overlap"]["raw_score"] >= 2
        for candidate_log in candidate_logs
    ):
        activation_reasons.append("exact_visible_text_overlap")
    if any(
        candidate_log["feature_contributions"]["question_paraphrase_overlap"]["weighted_score"] > 0
        for candidate_log in candidate_logs
    ):
        activation_reasons.append("question_paraphrase_overlap")
    return activation_reasons


def rerank_top_results(
    query_text: str,
    ranked_results: list[dict[str, Any]],
    caption_lookup: dict[str, CaptionRecord],
    top_n: int = 3,
    weights: DeterministicRerankWeights = DEFAULT_DETERMINISTIC_RERANK_WEIGHTS,
) -> dict[str, Any]:
    """Rerank only the top-n candidates, preserving original order when inactive."""
    top_candidates = ranked_results[:top_n]
    if not top_candidates:
        return {
            "activated": False,
            "activation_reasons": [],
            "candidate_logs": [],
            "reranked_results": list(ranked_results),
        }

    candidate_logs: list[dict[str, Any]] = []
    for result in top_candidates:
        image_id = result["image_id"]
        record = caption_lookup.get(image_id)
        if record is None:
            candidate_logs.append(
                {
                    "image_id": image_id,
                    "image_path": result.get("image_path"),
                    "original_rank": int(result["rank"]),
                    "original_similarity_score": float(result["similarity_score"]),
                    "rerank_score": float(result["similarity_score"]) * weights.original_similarity,
                    "feature_bundle": {
                        "looks_like_interface": False,
                        "exact_text_cues": [],
                        "named_entity_aliases": [],
                        "label_value_phrases": [],
                        "component_cues": [],
                    },
                    "feature_contributions": {
                        "exact_visible_text_overlap": _build_feature_contribution(
                            "exact_visible_text_overlap",
                            0.0,
                            [],
                            weights,
                        ),
                        "named_entity_match": _build_feature_contribution(
                            "named_entity_match",
                            0.0,
                            [],
                            weights,
                        ),
                        "label_value_phrase_overlap": _build_feature_contribution(
                            "label_value_phrase_overlap",
                            0.0,
                            [],
                            weights,
                        ),
                        "component_cue_overlap": _build_feature_contribution(
                            "component_cue_overlap",
                            0.0,
                            [],
                            weights,
                        ),
                        "question_paraphrase_overlap": _build_feature_contribution(
                            "question_paraphrase_overlap",
                            0.0,
                            [],
                            weights,
                        ),
                        "original_similarity": _build_feature_contribution(
                            "original_similarity",
                            float(result["similarity_score"]),
                            [],
                            weights,
                        ),
                    },
                }
            )
            continue
        candidate_logs.append(score_candidate_for_query(query_text, result, record, weights=weights))

    activation_reasons = determine_rerank_activation_reasons(candidate_logs)
    if not activation_reasons:
        reranked_results = list(ranked_results)
        for candidate_log in candidate_logs:
            candidate_log["final_rank"] = candidate_log["original_rank"]
            candidate_log["was_reordered"] = False
        return {
            "activated": False,
            "activation_reasons": [],
            "candidate_logs": candidate_logs,
            "reranked_results": reranked_results,
        }

    reranked_logs = sorted(
        candidate_logs,
        key=lambda item: (
            item["rerank_score"],
            item["original_similarity_score"],
            -item["original_rank"],
        ),
        reverse=True,
    )
    reranked_results: list[dict[str, Any]] = []
    final_rank_by_image_id: dict[str, int] = {}
    for final_rank, candidate_log in enumerate(reranked_logs, start=1):
        final_rank_by_image_id[candidate_log["image_id"]] = final_rank
        candidate_log["final_rank"] = final_rank
        candidate_log["was_reordered"] = final_rank != candidate_log["original_rank"]

    for result in top_candidates:
        reranked_result = dict(result)
        reranked_result["rank"] = final_rank_by_image_id[result["image_id"]]
        reranked_results.append(reranked_result)
    reranked_results.sort(key=lambda item: item["rank"])

    for result in ranked_results[top_n:]:
        reranked_result = dict(result)
        reranked_result["rank"] = len(reranked_results) + 1
        reranked_results.append(reranked_result)

    return {
        "activated": True,
        "activation_reasons": activation_reasons,
        "candidate_logs": reranked_logs,
        "reranked_results": reranked_results,
    }
