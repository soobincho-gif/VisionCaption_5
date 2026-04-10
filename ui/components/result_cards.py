"""Top-k result cards and explanation panels."""

from __future__ import annotations

from html import escape
from io import BytesIO
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

from ui.utils.formatters import format_list, format_score, humanize_key, normalize_text, truncate_text
from ui.utils.load_artifacts import get_representation_text, tokenize

CARD_THUMBNAIL_SIZE = (960, 540)


def render_result_cards(
    results: Sequence[Mapping[str, object]],
    captions_by_id: Mapping[str, dict[str, object]],
    representation_mode: str,
    query_text: str,
    query_log: Mapping[str, object] | None = None,
    layout: str = "grid",
    show_details: bool = True,
    image_bytes_by_id: Mapping[str, bytes] | None = None,
) -> None:
    """Render one or more result cards in a grid or stacked layout."""
    if not results:
        st.info("No frozen results are available for this query.")
        return

    normalized_query_log = query_log or {}
    image_bytes_by_id = image_bytes_by_id or {}
    containers = st.columns(len(results)) if layout == "grid" else [st.container() for _ in results]
    candidate_logs = {
        entry["image_id"]: entry
        for entry in list(normalized_query_log.get("candidate_logs", []) or [])
        if isinstance(entry, Mapping) and entry.get("image_id")
    }

    for result, container in zip(results, containers):
        image_id = str(result["image_id"])
        caption_record = dict(captions_by_id.get(image_id, {}))
        explanation_log = candidate_logs.get(image_id)
        reason = build_result_reason(
            result=result,
            caption_record=caption_record,
            query_text=query_text,
            rerank_log=explanation_log,
        )
        with container:
            with st.container(border=True):
                if image_id in image_bytes_by_id:
                    st.image(_build_card_thumbnail(image_bytes=image_bytes_by_id[image_id]), use_container_width=True)
                elif result.get("image_path") and Path(str(result["image_path"])).is_file():
                    st.image(_build_card_thumbnail(image_path=Path(str(result["image_path"]))), use_container_width=True)
                else:
                    st.caption("Image preview unavailable in local artifact bundle.")
                st.markdown(
                    (
                        f"**#{result['rank']} {escape(_display_name(image_id, caption_record))}**  \n"
                        f"{_format_card_scores(result, explanation_log)}"
                    )
                )
                st.write(reason)

                if show_details:
                    with st.expander("Representation + rerank evidence", expanded=int(result["rank"]) == 1):
                        representation_text = get_representation_text(caption_record, representation_mode)
                        if representation_text:
                            st.caption("Indexed representation")
                            st.code(representation_text, language="text")

                        feature_frame = _build_feature_frame(explanation_log)
                        if feature_frame is not None:
                            st.caption("Deterministic rerank feature contributions")
                            st.dataframe(
                                feature_frame,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Feature": st.column_config.TextColumn(width="medium"),
                                    "Raw": st.column_config.NumberColumn(format="%.3f"),
                                    "Weight": st.column_config.NumberColumn(format="%.2f"),
                                    "Weighted": st.column_config.NumberColumn(format="%.3f"),
                                    "Matched terms": st.column_config.TextColumn(width="large"),
                                },
                            )
                        else:
                            st.caption(
                                "This stage has no stored rerank contribution log. The ordering reflects frozen embedding similarity."
                            )


def build_result_reason(
    result: Mapping[str, object],
    caption_record: Mapping[str, object],
    query_text: str,
    rerank_log: Mapping[str, object] | None,
) -> str:
    """Generate a concise explanation for why a result ranked where it did."""
    return _build_reason(
        result=result,
        caption_record=caption_record,
        query_text=query_text,
        rerank_log=rerank_log,
    )


def build_card_thumbnail(
    image_path: Path | None = None,
    image_bytes: bytes | None = None,
) -> Image.Image | str | bytes:
    """Return a consistent result-card thumbnail without stretching tall screenshots."""
    return _build_card_thumbnail(image_path=image_path, image_bytes=image_bytes)


def _display_name(image_id: str, caption_record: Mapping[str, object]) -> str:
    """Build a user-facing title for one image result."""
    main_subject = str(caption_record.get("main_subject") or "").strip()
    if main_subject:
        return main_subject.capitalize()
    return humanize_key(image_id)


def _build_card_thumbnail(
    image_path: Path | None = None,
    image_bytes: bytes | None = None,
) -> Image.Image | str | bytes:
    """Fit image previews into a stable landscape card without hiding UI evidence."""
    try:
        if image_bytes is not None:
            with Image.open(BytesIO(image_bytes)) as image:
                return _letterbox_image(image.convert("RGB"))
        if image_path is not None:
            with Image.open(image_path) as image:
                return _letterbox_image(image.convert("RGB"))
    except Exception:
        if image_path is not None:
            return str(image_path)
        if image_bytes is not None:
            return image_bytes
    return ""


def _letterbox_image(image: Image.Image) -> Image.Image:
    """Place the full image on a neutral card-sized canvas."""
    fitted = ImageOps.contain(image, CARD_THUMBNAIL_SIZE, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", CARD_THUMBNAIL_SIZE, (248, 250, 252))
    offset = (
        (CARD_THUMBNAIL_SIZE[0] - fitted.width) // 2,
        (CARD_THUMBNAIL_SIZE[1] - fitted.height) // 2,
    )
    canvas.paste(fitted, offset)
    return canvas


def _format_card_scores(
    result: Mapping[str, object],
    rerank_log: Mapping[str, object] | None,
) -> str:
    """Format score chips for result-card summaries."""
    base_similarity = float(result.get("similarity_score", 0.0))
    if not rerank_log:
        return (
            f"`final {format_score(base_similarity)}` "
            f"`base {format_score(base_similarity)}` "
            "`rerank +0.000`"
        )

    final_score = float(rerank_log.get("rerank_score", base_similarity))
    feature_delta = 0.0
    for feature_name, payload in dict(rerank_log.get("feature_contributions", {})).items():
        if feature_name == "original_similarity":
            continue
        feature_delta += float(payload.get("weighted_score", 0.0))
    return (
        f"`final {format_score(final_score)}` "
        f"`base {format_score(base_similarity)}` "
        f"`rerank {feature_delta:+.3f}`"
    )


def _build_reason(
    result: Mapping[str, object],
    caption_record: Mapping[str, object],
    query_text: str,
    rerank_log: Mapping[str, object] | None,
) -> str:
    """Generate a concise explanation for why a result ranked where it did."""
    if rerank_log:
        strongest_features = _top_positive_features(rerank_log)
        if strongest_features:
            feature_bits = []
            for feature_name, payload in strongest_features[:2]:
                matched_terms = payload.get("matched_terms", [])
                if matched_terms:
                    feature_bits.append(
                        f"{humanize_key(feature_name)} matched {format_list(matched_terms, max_items=2)}"
                    )
                else:
                    feature_bits.append(f"{humanize_key(feature_name)} added positive weight")
            return f"Rerank kept this image high because {', and '.join(feature_bits)}."
        return "Rerank left this image near the top mostly on its original similarity score."

    lexical_reason = _build_lexical_reason(caption_record, query_text)
    if lexical_reason:
        return lexical_reason
    return "This frozen ranking stayed near the top on embedding similarity over the selected representation."


def _build_lexical_reason(caption_record: Mapping[str, object], query_text: str) -> str | None:
    """Explain a non-reranked result using visible text, layout, or cue overlap."""
    query_tokens = tokenize(query_text)
    if not query_tokens:
        return None

    reasons: list[str] = []

    visible_text_hits = [
        cue
        for cue in list(caption_record.get("visible_text", []))
        if tokenize(str(cue)) & query_tokens or normalize_text(str(cue)) in normalize_text(query_text)
    ]
    if visible_text_hits:
        reasons.append(f"visible text matched {format_list(visible_text_hits, max_items=2)}")

    layout_hits = [
        cue for cue in list(caption_record.get("layout_blocks", [])) if tokenize(str(cue)) & query_tokens
    ]
    if layout_hits:
        reasons.append(f"layout cues matched {format_list(layout_hits, max_items=2)}")

    cue_hits = [
        cue for cue in list(caption_record.get("distinctive_cues", [])) if tokenize(str(cue)) & query_tokens
    ]
    if cue_hits:
        reasons.append(f"distinctive cues matched {format_list(cue_hits, max_items=2)}")

    if not reasons and caption_record.get("main_subject"):
        reasons.append(f"the main subject aligns with {truncate_text(str(caption_record['main_subject']), 55)}")

    if not reasons:
        return None
    return f"This result stayed high because {', and '.join(reasons)}."


def _top_positive_features(rerank_log: Mapping[str, object]) -> list[tuple[str, Mapping[str, object]]]:
    """Return positive rerank features sorted by weighted contribution."""
    feature_contributions = dict(rerank_log.get("feature_contributions", {}))
    ranked = sorted(
        (
            (feature_name, payload)
            for feature_name, payload in feature_contributions.items()
            if float(payload.get("weighted_score", 0.0)) > 0
        ),
        key=lambda item: float(item[1]["weighted_score"]),
        reverse=True,
    )
    return ranked


def _build_feature_frame(rerank_log: Mapping[str, object] | None) -> pd.DataFrame | None:
    """Build a small dataframe for rerank feature inspection."""
    if not rerank_log:
        return None
    rows = [
        {
            "Feature": humanize_key(feature_name),
            "Raw": float(payload.get("raw_score", 0.0)),
            "Weight": float(payload.get("weight", 0.0)),
            "Weighted": float(payload.get("weighted_score", 0.0)),
            "Matched terms": format_list(payload.get("matched_terms", []), max_items=3),
        }
        for feature_name, payload in dict(rerank_log.get("feature_contributions", {})).items()
    ]
    frame = pd.DataFrame(rows)
    return frame.sort_values("Weighted", ascending=False)
