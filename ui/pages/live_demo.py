"""Live frozen-replay demo page for VisionCaption."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd
import streamlit as st

from src.core.representation import build_embedding_source_text
from src.core.schemas import CaptionRecord
from ui.components.metric_cards import MetricCard, render_metric_cards
from ui.components.query_panels import (
    render_callout,
    render_query_summary,
    render_section_heading,
    render_status_badges,
)
from ui.components.result_cards import build_card_thumbnail, build_result_reason, render_result_cards
from ui.utils.formatters import format_list, format_score, humanize_key, truncate_text
from ui.utils.load_artifacts import (
    ArtifactLoadError,
    BenchmarkBundle,
    build_query_rows,
    load_portfolio_artifacts,
    repo_path,
    resolve_replay_query,
)
from ui.utils.uploads import (
    build_temporary_embedding,
    build_temporary_upload_record,
    inspect_uploaded_image,
    run_retrieval_with_temporary_upload,
)


DEFAULT_QUERY_TEXT = "beige editorial AI chat about imagination and discovery rather than AI today"
QUICK_FILL_QUERIES = (
    "beige editorial AI chat about imagination and discovery",
    "vertical beige interface with awaiting image sequence",
    "dashboard dark panels with file sizes and slider",
)
UPLOAD_STATE_KEYS = (
    "uploaded_image_bytes",
    "uploaded_image_metadata",
    "uploaded_image_statuses",
    "uploaded_representation",
    "uploaded_embedding",
    "uploaded_retrieval_results",
    "uploaded_retrieval_error",
)


def render() -> None:
    """Render the live demo page."""
    try:
        artifacts = load_portfolio_artifacts()
    except ArtifactLoadError as exc:
        st.error(str(exc))
        return

    st.session_state.setdefault("live_demo_benchmark_key", "mixed_sanity")
    st.session_state.setdefault("live_demo_config_key", "final_default")
    st.session_state.setdefault("live_demo_query_text", DEFAULT_QUERY_TEXT)
    st.session_state.setdefault("live_demo_committed_query", DEFAULT_QUERY_TEXT)
    st.session_state.setdefault("live_demo_last_quick_fill", None)

    benchmark_key = st.session_state["live_demo_benchmark_key"]
    bundle = artifacts.benchmarks[benchmark_key]
    query_rows_by_config = {
        config_key: build_query_rows(bundle, config_key)
        for config_key in bundle.configs
    }

    st.markdown(
        """
        <div class="demo-console">
          <div class="eyebrow">Live Demo · Retrieval Console</div>
          <h2 class="section-title">Try a prompt, inspect the result, then add your own image.</h2>
          <p class="section-body">
            Frozen gallery replay stays deterministic. Uploaded images are session-only records that never persist by default.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_status_badges(
        [
            "Mode: frozen gallery replay",
            "Rebuild: disabled / unavailable",
            "Upload: session-only temporary record",
        ]
    )

    control_col, context_col = st.columns([1.2, 0.8], gap="large")
    with control_col:
        selected_query_id = _render_query_controls(bundle)
        st.segmented_control(
            "Retrieval config",
            options=list(bundle.configs),
            key="live_demo_config_key",
            format_func=lambda key: bundle.configs[key].spec.label,
        )
        if st.button("Run frozen replay", use_container_width=True):
            st.session_state["live_demo_committed_query"] = st.session_state.get("live_demo_query_text", "")

    with context_col:
        selected_query = bundle.queries_by_id[selected_query_id]
        render_callout(
            "Demo contract",
            (
                "Free-text input resolves to the closest frozen benchmark query, so the portfolio demo is reproducible "
                "while still feeling interactive."
            ),
            tone="success",
        )
        render_query_summary(
            query_text=selected_query["query"],
            query_id=selected_query["query_id"],
            expected_image_ids=selected_query.get("expected_image_ids", []),
            tags=selected_query.get("tags", []),
            subtitle="Benchmark example quick-fill source.",
            slice_label=selected_query.get("slice"),
        )

    committed_query = st.session_state.get("live_demo_committed_query", "").strip()
    if not committed_query:
        render_callout("Ready", "Type a query or load a benchmark example to start the replay.", tone="success")
        _render_upload_section(artifacts.captions_by_id, bundle, st.session_state["live_demo_config_key"])
        return

    config_key = st.session_state["live_demo_config_key"] or "final_default"
    resolved_query, match_info = resolve_replay_query(committed_query, bundle)
    selected_row = _find_row(query_rows_by_config[config_key], resolved_query["query_id"])
    query_log = selected_row.get("query_log") or selected_row
    results = list(selected_row.get("results", []))[:3]

    if not match_info.get("exact_match"):
        st.info(
            (
                "Frozen replay matched your input to "
                f"`{resolved_query['query_id']}` with similarity {match_info['score']}. "
                "The result below is intentionally replayed from that artifact."
            )
        )

    render_query_summary(
        query_text=str(resolved_query["query"]),
        query_id=str(resolved_query["query_id"]),
        expected_image_ids=resolved_query.get("expected_image_ids", []),
        tags=resolved_query.get("tags", []),
        subtitle=f"Config: {bundle.configs[config_key].spec.label}",
        slice_label=resolved_query.get("slice"),
    )

    _render_top1_hero(
        results=results,
        captions_by_id=artifacts.captions_by_id,
        query_text=str(resolved_query["query"]),
        query_log=query_log,
    )
    _render_replay_metrics(results, selected_row)

    render_section_heading(
        "Top-3 Results",
        "Ranked result cards",
        "Each card shows the final score, base similarity, rerank delta, and a short reason for selection.",
    )
    render_result_cards(
        results=results,
        captions_by_id=artifacts.captions_by_id,
        representation_mode=bundle.configs[config_key].spec.representation_mode,
        query_text=str(resolved_query["query"]),
        query_log=query_log,
        layout="grid",
        show_details=False,
    )

    _render_drilldown_tabs(
        bundle=bundle,
        query_id=str(resolved_query["query_id"]),
        config_key=config_key,
        query_text=str(resolved_query["query"]),
        selected_row=selected_row,
        query_log=query_log,
        captions_by_id=artifacts.captions_by_id,
    )

    _render_upload_section(artifacts.captions_by_id, bundle, config_key)


def _render_query_controls(bundle: BenchmarkBundle) -> str:
    """Render query controls and return the selected example query id."""
    default_query_id = _find_query_id_by_text(bundle, DEFAULT_QUERY_TEXT)
    default_index = bundle.query_order.index(default_query_id) if default_query_id in bundle.query_order else 0

    selected_quick_query = st.pills(
        "Sample query chips",
        options=list(QUICK_FILL_QUERIES),
        default=None,
        key="live_demo_quick_query",
    )
    if selected_quick_query and st.session_state.get("live_demo_last_quick_fill") != selected_quick_query:
        st.session_state["live_demo_query_text"] = selected_quick_query
        st.session_state["live_demo_committed_query"] = selected_quick_query
        st.session_state["live_demo_last_quick_fill"] = selected_quick_query

    selected_query_id = st.selectbox(
        "Benchmark quick-fill",
        options=bundle.query_order,
        index=default_index,
        format_func=lambda query_id: _query_option_label(bundle, query_id),
    )
    if st.button("Load selected benchmark example", use_container_width=True):
        query_text = str(bundle.queries_by_id[selected_query_id]["query"])
        st.session_state["live_demo_query_text"] = query_text
        st.session_state["live_demo_committed_query"] = query_text

    st.text_input(
        "Query text input",
        key="live_demo_query_text",
        placeholder="Describe a UI screenshot, historical chat interface, or visual scene.",
    )

    return selected_query_id


def _render_top1_hero(
    results: Sequence[Mapping[str, Any]],
    captions_by_id: Mapping[str, dict[str, Any]],
    query_text: str,
    query_log: Mapping[str, Any],
) -> None:
    """Render a prominent top-1 result summary."""
    if not results:
        render_callout("No result", "The selected frozen replay query has no stored top-k results.", tone="warning")
        return

    top_result = results[0]
    image_id = str(top_result["image_id"])
    caption_record = captions_by_id.get(image_id, {})
    candidate_log = _candidate_logs_by_id(query_log).get(image_id)
    reason = build_result_reason(top_result, caption_record, query_text, candidate_log)
    final_score = _final_score(top_result, candidate_log)
    rerank_delta = _rerank_delta(candidate_log)

    image_col, detail_col = st.columns([0.42, 0.58], gap="large")
    with image_col:
        image_path = top_result.get("image_path")
        if image_path and Path(str(image_path)).is_file():
            st.image(build_card_thumbnail(image_path=Path(str(image_path))), use_container_width=True)
        else:
            st.caption("Top result image preview unavailable.")
    with detail_col:
        st.markdown(
            f"""
            <div class="result-hero">
              <div class="eyebrow">Top-1 Hero Result</div>
              <h3>Rank #1 · {escape(humanize_key(image_id))}</h3>
              <div class="result-meta">
                <strong>Why selected:</strong> {escape(reason)}
              </div>
              <div class="result-score-row">
                <div class="score-pill"><span>Final rerank score</span><strong>{format_score(final_score)}</strong></div>
                <div class="score-pill"><span>Base similarity</span><strong>{format_score(float(top_result.get("similarity_score", 0.0)))}</strong></div>
                <div class="score-pill"><span>Rerank delta</span><strong>{rerank_delta:+.3f}</strong></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_replay_metrics(results: Sequence[Mapping[str, Any]], selected_row: Mapping[str, Any]) -> None:
    """Render compact metrics for the current replay query."""
    top_result = results[0] if results else None
    second_result = results[1] if len(results) > 1 else None
    top_margin = None
    if top_result and second_result:
        top_margin = float(top_result.get("similarity_score", 0.0)) - float(second_result.get("similarity_score", 0.0))

    expected_ids = set(selected_row.get("expected_image_ids", []))
    top1_hit = bool(top_result and top_result.get("image_id") in expected_ids)
    render_metric_cards(
        [
            MetricCard(
                label="Top-1",
                value=humanize_key(str(top_result["image_id"])) if top_result else "N/A",
                delta="expected hit" if top1_hit else "needs review",
                help_text="Highest-ranked frozen replay result.",
            ),
            MetricCard(
                label="Base Similarity",
                value=format_score(float(top_result.get("similarity_score", 0.0))) if top_result else "N/A",
                help_text="Cosine similarity before deterministic explanation features are shown.",
            ),
            MetricCard(
                label="Top-1 Margin",
                value=format_score(top_margin),
                help_text="Gap between rank 1 and rank 2 base similarities.",
            ),
            MetricCard(
                label="Replay Status",
                value="Correct" if top1_hit else "Unresolved",
                help_text="Whether the expected target is ranked first in this artifact.",
            ),
        ]
    )


def _render_drilldown_tabs(
    bundle: BenchmarkBundle,
    query_id: str,
    config_key: str,
    query_text: str,
    selected_row: Mapping[str, Any],
    query_log: Mapping[str, Any],
    captions_by_id: Mapping[str, dict[str, Any]],
) -> None:
    """Render detailed evidence tabs under the result cards."""
    top_result = selected_row.get("top_result") or (selected_row.get("results") or [None])[0]
    if not top_result:
        return

    image_id = str(top_result["image_id"])
    caption_record = dict(captions_by_id.get(image_id, {}))
    candidate_log = _candidate_logs_by_id(query_log).get(image_id, {})
    representation_mode = bundle.configs[config_key].spec.representation_mode
    source_text = _build_source_text(caption_record, representation_mode)

    render_section_heading(
        "Explainability",
        "Representation, rerank features, and comparison trace",
        "Details stay tucked into tabs so the demo remains readable while still proving what changed.",
    )
    representation_tab, rerank_tab, comparison_tab, raw_tab = st.tabs(
        ["Representation", "Rerank Features", "Before vs After", "Raw Trace"]
    )
    with representation_tab:
        st.caption("Source text")
        st.code(source_text or "No representation text available.", language="text")
        feature_bundle = dict(candidate_log.get("feature_bundle", {}))
        cue_rows = [
            {"Cue": "named entity cue", "Values": format_list(feature_bundle.get("named_entity_aliases", []), max_items=8)},
            {"Cue": "exact text cue", "Values": format_list(feature_bundle.get("exact_text_cues", []), max_items=8)},
            {"Cue": "component cue", "Values": format_list(feature_bundle.get("component_cues", []), max_items=8)},
        ]
        st.dataframe(pd.DataFrame(cue_rows), use_container_width=True, hide_index=True)

    with rerank_tab:
        feature_frame = _feature_contribution_frame(candidate_log)
        if feature_frame.empty:
            st.info("This config has no stored deterministic rerank contribution log for the top result.")
        else:
            st.dataframe(feature_frame, use_container_width=True, hide_index=True)

    with comparison_tab:
        comparison_frame, what_changed = _build_comparison_frame(bundle, query_id)
        _render_before_after_cards(comparison_frame)
        render_callout("What changed", what_changed, tone="success")

    with raw_tab:
        st.json(
            {
                "query_text": query_text,
                "selected_config": config_key,
                "selected_row": selected_row,
                "query_log": query_log,
            }
        )


def _render_upload_section(
    captions_by_id: dict[str, dict[str, Any]],
    bundle: BenchmarkBundle,
    config_key: str,
) -> None:
    """Render session-only image upload and optional retrieval controls."""
    render_section_heading(
        "Add Your Own Image",
        "Session-only upload workflow",
        "Upload stays in memory for this Streamlit session. Representation and retrieval only run after explicit button clicks.",
    )

    upload_col, status_col = st.columns([1.05, 0.95], gap="large")
    with upload_col:
        with st.container(border=True):
            st.session_state.setdefault("upload_widget_nonce", 0)
            uploaded = st.file_uploader(
                "Upload an image",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=False,
                key=f"live_demo_uploaded_file_{st.session_state['upload_widget_nonce']}",
            )
            if uploaded is not None:
                _store_uploaded_file(uploaded.getvalue(), uploaded.name, uploaded.type)

            metadata = st.session_state.get("uploaded_image_metadata")
            image_bytes = st.session_state.get("uploaded_image_bytes")
            if metadata and image_bytes:
                st.image(image_bytes, caption=str(metadata["filename"]), use_container_width=True)
                st.success("Image uploaded for this session.")
                st.markdown(
                    f"""
                    <div class="metadata-grid">
                      <div class="metadata-item"><span>Filename</span><strong>{escape(str(metadata["filename"]))}</strong></div>
                      <div class="metadata-item"><span>Dimensions</span><strong>{int(metadata["width"])} x {int(metadata["height"])}</strong></div>
                      <div class="metadata-item"><span>File size</span><strong>{escape(_format_file_size(int(metadata["size_bytes"])))}</strong></div>
                      <div class="metadata-item"><span>Format</span><strong>{escape(str(metadata["format"]))}</strong></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                render_callout("No upload yet", "Upload a PNG, JPG, JPEG, or WEBP image to inspect it.", tone="success")

    with status_col:
        retrieval_mode = st.selectbox(
            "Upload retrieval mode",
            options=[
                "Inspect my image",
                "Use uploaded image only",
                "Compare uploaded image against existing gallery",
                "Add uploaded image temporarily to retrieval pool",
            ],
            index=0,
            key="uploaded_retrieval_mode",
        )
        _render_upload_status()

        top_action_cols = st.columns(2)
        bottom_action_cols = st.columns(2)
        with top_action_cols[0]:
            if st.button("Generate representation", use_container_width=True):
                _generate_upload_representation()
        with top_action_cols[1]:
            if st.button("Add temporary pool", use_container_width=True):
                _prepare_upload_pool()
        with bottom_action_cols[0]:
            if st.button("Run retrieval", use_container_width=True):
                _run_upload_retrieval(captions_by_id, bundle, config_key, retrieval_mode or "Inspect my image")
        with bottom_action_cols[1]:
            if st.button("Remove upload", use_container_width=True):
                _clear_upload_state()
                st.rerun()

        if st.session_state.get("uploaded_retrieval_error"):
            st.warning(str(st.session_state["uploaded_retrieval_error"]))

    representation = st.session_state.get("uploaded_representation")
    if representation:
        with st.expander("Uploaded representation", expanded=False):
            st.code(str(representation.get("source_text", "")), language="text")
            st.json(representation.get("feature_bundle", {}))

    upload_results = st.session_state.get("uploaded_retrieval_results")
    metadata = st.session_state.get("uploaded_image_metadata")
    image_bytes = st.session_state.get("uploaded_image_bytes")
    if upload_results and metadata and image_bytes:
        st.subheader("Uploaded-image retrieval results")
        upload_id = str(metadata["image_id"])
        captions_with_upload = dict(captions_by_id)
        if representation:
            captions_with_upload[upload_id] = dict(representation.get("caption_record", {}))
        render_result_cards(
            results=upload_results,
            captions_by_id=captions_with_upload,
            representation_mode="caption_plus_selected_structured",
            query_text=st.session_state.get("live_demo_query_text", ""),
            query_log=None,
            layout="grid",
            show_details=False,
            image_bytes_by_id={upload_id: image_bytes},
        )


def _store_uploaded_file(image_bytes: bytes, filename: str, content_type: str | None) -> None:
    """Inspect and store upload bytes, resetting derived state when the image changes."""
    try:
        metadata = inspect_uploaded_image(image_bytes, filename, content_type)
    except ValueError as exc:
        st.error(str(exc))
        return

    previous_hash = st.session_state.get("uploaded_image_metadata", {}).get("sha256")
    if previous_hash == metadata["sha256"]:
        return

    for key in UPLOAD_STATE_KEYS:
        st.session_state.pop(key, None)
    st.session_state["uploaded_image_bytes"] = image_bytes
    st.session_state["uploaded_image_metadata"] = metadata
    st.session_state["uploaded_image_statuses"] = ["uploaded"]


def _generate_upload_representation() -> None:
    """Generate and store uploaded-image representation state."""
    metadata = st.session_state.get("uploaded_image_metadata")
    image_bytes = st.session_state.get("uploaded_image_bytes")
    if not metadata or not image_bytes:
        st.warning("Upload an image before generating a representation.")
        return

    try:
        with st.spinner("Generating representation..."):
            representation = build_temporary_upload_record(image_bytes, metadata)
        st.session_state["uploaded_representation"] = representation
        _add_upload_status("representation ready")
        st.session_state.pop("uploaded_embedding", None)
        st.session_state.pop("uploaded_retrieval_results", None)
        st.session_state.pop("uploaded_retrieval_error", None)
    except Exception as exc:
        st.session_state["uploaded_retrieval_error"] = f"Representation generation failed: {exc}"


def _run_upload_retrieval(
    captions_by_id: dict[str, dict[str, Any]],
    bundle: BenchmarkBundle,
    config_key: str,
    retrieval_mode: str,
) -> None:
    """Generate a temporary embedding when needed and run upload retrieval."""
    if retrieval_mode == "Inspect my image":
        st.info("Inspect mode stops after representation. Choose a retrieval mode to rank the upload.")
        return

    representation = st.session_state.get("uploaded_representation")
    if not representation:
        st.warning("Generate representation before running retrieval with the uploaded image.")
        return

    try:
        embedding = st.session_state.get("uploaded_embedding")
        if not embedding:
            st.warning("Add the image to the temporary retrieval pool before running retrieval.")
            return

        gallery_embedding_path = _gallery_embedding_path(bundle, config_key)
        with st.spinner("Running retrieval with uploaded image..."):
            results = run_retrieval_with_temporary_upload(
                query_text=st.session_state.get("live_demo_query_text", ""),
                uploaded_record=representation,
                uploaded_embedding=embedding,
                gallery_embedding_path=gallery_embedding_path,
                gallery_captions_by_id=captions_by_id,
                retrieval_mode=retrieval_mode,
                top_k=3,
            )
        st.session_state["uploaded_retrieval_results"] = results
        st.session_state.pop("uploaded_retrieval_error", None)
        _add_upload_status("retrieval complete")
    except Exception as exc:
        st.session_state["uploaded_retrieval_error"] = f"Upload retrieval failed: {exc}"


def _prepare_upload_pool() -> None:
    """Create the session-only uploaded-image embedding used by retrieval."""
    representation = st.session_state.get("uploaded_representation")
    if not representation:
        st.warning("Generate representation before adding the image to the temporary pool.")
        return

    try:
        with st.spinner("Creating temporary upload embedding..."):
            embedding = build_temporary_embedding(str(representation["source_text"]))
        st.session_state["uploaded_embedding"] = embedding
        st.session_state.pop("uploaded_retrieval_results", None)
        st.session_state.pop("uploaded_retrieval_error", None)
        _add_upload_status("temporary pool ready")
    except Exception as exc:
        st.session_state["uploaded_retrieval_error"] = f"Temporary pool setup failed: {exc}"


def _render_upload_status() -> None:
    """Render current upload state as clear chips."""
    statuses = st.session_state.get("uploaded_image_statuses", [])
    if statuses:
        render_status_badges(statuses)
    else:
        render_status_badges(["waiting for upload"], tone="muted")
    render_status_badges(
        [
            "Demo dataset: frozen",
            "Uploaded image: session-only",
        ],
        tone="muted",
    )


def _add_upload_status(status: str) -> None:
    """Append one upload status while preserving order."""
    statuses = list(st.session_state.get("uploaded_image_statuses", []))
    if status not in statuses:
        statuses.append(status)
    st.session_state["uploaded_image_statuses"] = statuses


def _clear_upload_state() -> None:
    """Remove all upload-derived session state."""
    for key in UPLOAD_STATE_KEYS:
        st.session_state.pop(key, None)
    st.session_state["upload_widget_nonce"] = int(st.session_state.get("upload_widget_nonce", 0)) + 1


def _gallery_embedding_path(bundle: BenchmarkBundle, config_key: str) -> Path:
    """Return the embedding artifact that corresponds to a config's representation."""
    config = bundle.configs[config_key]
    candidate_path = repo_path(Path(config.spec.artifact_path).with_name("embeddings.jsonl"))
    if candidate_path.is_file():
        return candidate_path

    if config.spec.previous_key:
        previous = bundle.configs[config.spec.previous_key]
        previous_path = repo_path(Path(previous.spec.artifact_path).with_name("embeddings.jsonl"))
        if previous_path.is_file():
            return previous_path

    return candidate_path


def _find_row(rows: Sequence[Mapping[str, Any]], query_id: str) -> Mapping[str, Any]:
    """Return one query row by id."""
    for row in rows:
        if row.get("query_id") == query_id:
            return row
    raise KeyError(f"Query is missing from frozen artifacts: {query_id}")


def _find_query_id_by_text(bundle: BenchmarkBundle, query_text: str) -> str:
    """Find the first benchmark query containing the given text."""
    normalized = query_text.lower().strip()
    for query_id in bundle.query_order:
        if normalized in str(bundle.queries_by_id[query_id]["query"]).lower():
            return query_id
    return bundle.query_order[0]


def _query_option_label(bundle: BenchmarkBundle, query_id: str) -> str:
    """Format a compact example-query label."""
    query = bundle.queries_by_id[query_id]
    return f"{query_id} · {truncate_text(str(query['query']), 82)}"


def _candidate_logs_by_id(query_log: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    """Return candidate rerank logs keyed by image id."""
    if not query_log:
        return {}
    return {
        str(entry["image_id"]): entry
        for entry in list(query_log.get("candidate_logs", []) or [])
        if isinstance(entry, Mapping) and entry.get("image_id")
    }


def _final_score(result: Mapping[str, Any], candidate_log: Mapping[str, Any] | None) -> float:
    """Return rerank score when available, otherwise base similarity."""
    if candidate_log:
        return float(candidate_log.get("rerank_score", result.get("similarity_score", 0.0)))
    return float(result.get("similarity_score", 0.0))


def _rerank_delta(candidate_log: Mapping[str, Any] | None) -> float:
    """Return weighted non-similarity rerank contribution."""
    if not candidate_log:
        return 0.0
    return sum(
        float(payload.get("weighted_score", 0.0))
        for feature_name, payload in dict(candidate_log.get("feature_contributions", {})).items()
        if feature_name != "original_similarity"
    )


def _feature_contribution_frame(candidate_log: Mapping[str, Any]) -> pd.DataFrame:
    """Build a feature-contribution table from a candidate log."""
    rows = []
    for feature_name, payload in dict(candidate_log.get("feature_contributions", {})).items():
        rows.append(
            {
                "Feature": humanize_key(feature_name),
                "Raw": float(payload.get("raw_score", 0.0)),
                "Weight": float(payload.get("weight", 0.0)),
                "Weighted": float(payload.get("weighted_score", 0.0)),
                "Matched terms": format_list(payload.get("matched_terms", []), max_items=5),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values("Weighted", ascending=False)


def _build_comparison_frame(bundle: BenchmarkBundle, query_id: str) -> tuple[pd.DataFrame, str]:
    """Build baseline/candidate/final comparison rows and a short summary."""
    rows = []
    top_by_config: dict[str, str] = {}
    for config_key in bundle.configs:
        query_row = _find_row(build_query_rows(bundle, config_key), query_id)
        top_result = query_row.get("top_result") or (query_row.get("results") or [None])[0]
        top_image_id = str(top_result.get("image_id")) if top_result else "N/A"
        top_by_config[config_key] = top_image_id
        rows.append(
            {
                "Config": bundle.configs[config_key].spec.label,
                "Top-1": top_image_id,
                "Score": format_score(float(top_result.get("similarity_score", 0.0))) if top_result else "N/A",
                "Correct": "Yes" if query_row.get("top1_correct") else "No",
                "Corrected": "Yes" if query_row.get("corrected") else "No",
                "Regression": "Yes" if query_row.get("regression") else "No",
            }
        )

    baseline = top_by_config.get("baseline", "N/A")
    final = top_by_config.get("final_default", "N/A")
    if baseline == final:
        summary = "The final default preserved the same top-1 as baseline for this query."
    else:
        summary = f"The top-1 changed from {baseline} to {final}, showing where structured cues or rerank altered the decision."
    return pd.DataFrame(rows), summary


def _render_before_after_cards(comparison_frame: pd.DataFrame) -> None:
    """Render config comparison as compact evidence cards instead of a spreadsheet."""
    cards_html = ['<div class="evidence-grid">']
    for row in comparison_frame.to_dict(orient="records"):
        status = "corrected" if row.get("Corrected") == "Yes" else "unchanged"
        if row.get("Regression") == "Yes":
            status = "regressed"
        cards_html.append(
            f"""
            <div class="evidence-card">
              <span class="status-badge {escape(status)}">{escape(status)}</span>
              <h3>{escape(str(row.get("Config", "Config")))}</h3>
              <p><strong>Top-1:</strong> {escape(str(row.get("Top-1", "N/A")))}</p>
              <p><strong>Score:</strong> {escape(str(row.get("Score", "N/A")))} · <strong>Correct:</strong> {escape(str(row.get("Correct", "No")))}</p>
            </div>
            """
        )
    cards_html.append("</div>")
    st.markdown("".join(cards_html), unsafe_allow_html=True)


def _build_source_text(caption_record: Mapping[str, Any], representation_mode: str) -> str:
    """Build source text from a caption artifact when possible."""
    if not caption_record:
        return ""
    try:
        record = CaptionRecord.model_validate(caption_record)
        return build_embedding_source_text(record, representation_mode=representation_mode)
    except Exception:
        return str(caption_record.get("retrieval_text") or caption_record.get("caption_text") or "")


def _format_file_size(size_bytes: int) -> str:
    """Format bytes as a compact display value."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"
