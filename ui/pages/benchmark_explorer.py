"""Benchmark evidence explorer for the VisionCaption portfolio."""

from __future__ import annotations

from html import escape
from typing import Any, Mapping, Sequence

import pandas as pd
import streamlit as st

from ui.components.metric_cards import MetricCard, render_metric_cards
from ui.components.query_panels import render_callout, render_query_summary, render_section_heading, render_status_badges
from ui.utils.formatters import format_list, format_percent, format_score, humanize_key, truncate_text
from ui.utils.load_artifacts import (
    ArtifactLoadError,
    BenchmarkBundle,
    build_query_rows,
    get_config_metrics,
    load_portfolio_artifacts,
)


BUCKET_OPTIONS = (
    "person-name",
    "visible-text",
    "label-value phrase",
    "paraphrase",
    "layout",
    "same-family UI confusion",
)


def render() -> None:
    """Render benchmark controls, tables, and query detail evidence."""
    try:
        artifacts = load_portfolio_artifacts()
    except ArtifactLoadError as exc:
        st.error(str(exc))
        return

    render_section_heading(
        "Benchmark Explorer",
        "Evidence, not just a demo",
        "Filter the frozen benchmark artifacts, inspect per-query decisions, and connect improvements to concrete rerank features.",
    )

    filter_top_left, filter_top_right = st.columns([1.0, 1.0], gap="medium")
    with filter_top_left:
        benchmark_key = st.selectbox(
            "Benchmark selector",
            options=list(artifacts.benchmarks),
            format_func=lambda key: artifacts.benchmarks[key].spec.label,
        )
    bundle = artifacts.benchmarks[benchmark_key]
    with filter_top_right:
        config_key = st.segmented_control(
            "Config selector",
            options=list(bundle.configs),
            default="final_default" if "final_default" in bundle.configs else list(bundle.configs)[0],
            format_func=lambda key: bundle.configs[key].spec.label,
        )
    config_key = config_key or "final_default"

    rows = build_query_rows(bundle, config_key)
    slice_options = ["all", *sorted({str(row.get("slice", "normal_ui")) for row in rows})]
    filter_bottom_left, filter_bottom_mid, filter_bottom_right = st.columns([0.9, 0.9, 1.2], gap="medium")
    with filter_bottom_left:
        selected_slice = st.segmented_control(
            "Slice selector",
            options=slice_options,
            default="all",
            format_func=humanize_key,
        )
    selected_slice = selected_slice or "all"
    with filter_bottom_mid:
        status_filter = st.segmented_control(
            "Status filter",
            options=["all", "corrected", "unresolved", "regressed"],
            default="all",
            format_func=humanize_key,
        )
    status_filter = status_filter or "all"
    with filter_bottom_right:
        selected_buckets = st.pills(
            "Failure bucket filters",
            options=list(BUCKET_OPTIONS),
            selection_mode="multi",
            default=[],
            format_func=humanize_key,
        )
    selected_buckets = selected_buckets or []
    render_status_badges(
        [
            f"Benchmark: {bundle.spec.label}",
            f"Config: {bundle.configs[config_key].spec.short_label}",
            f"Rows: {len(rows)} frozen queries",
        ],
        tone="muted",
    )

    filtered_rows = [
        row
        for row in rows
        if _slice_matches(row, selected_slice)
        and _status_matches(row, status_filter)
        and _bucket_matches(row, selected_buckets)
    ]

    _render_metric_cards(bundle, config_key, filtered_rows)
    _render_ablation_summary(artifacts.mixed_validation_report, artifacts.promotion_summary, benchmark_key)
    selected_row = _render_query_table(filtered_rows)
    if selected_row is None:
        render_callout("No rows", "No benchmark queries match the current filters.", tone="warning")
        return

    _render_query_detail(bundle, selected_row, artifacts.captions_by_id)
    _render_bucket_explorer(rows)


def _render_metric_cards(bundle: BenchmarkBundle, config_key: str, filtered_rows: Sequence[Mapping[str, Any]]) -> None:
    """Render benchmark metric cards for the selected config and slice."""
    config_artifacts = bundle.configs[config_key]
    metrics = get_config_metrics(config_artifacts)
    corrected_count = sum(1 for row in filtered_rows if row.get("corrected"))
    regression_count = sum(1 for row in filtered_rows if row.get("regression"))
    hard_negative_confusion = int(
        dict(metrics.get("family_confusion_accuracy", {})).get("hard_negative_confusion_count", 0)
    )

    if filtered_rows:
        filtered_recall = sum(1 for row in filtered_rows if row.get("top1_correct")) / len(filtered_rows)
    else:
        filtered_recall = 0.0

    render_metric_cards(
        [
            MetricCard(
                label="Recall@1",
                value=format_percent(float(metrics.get("recall_at_1", filtered_recall))),
                delta=f"slice view: {format_percent(filtered_recall)}",
                help_text="Overall selected-config Recall@1, with filtered slice shown as delta.",
            ),
            MetricCard(
                label="Recall@3",
                value=format_percent(float(metrics.get("recall_at_3", 0.0))),
                help_text="Whether the expected target appears in the top 3.",
            ),
            MetricCard(
                label="Hard-Negative Confusion",
                value=str(hard_negative_confusion),
                help_text="How often the top-1 lands on a curated same-family hard negative.",
            ),
            MetricCard(
                label="Corrected Queries",
                value=str(corrected_count),
                help_text="Rows in the current filtered view corrected by the selected stage.",
            ),
            MetricCard(
                label="Regressions",
                value=str(regression_count),
                help_text="Rows in the current filtered view marked as regressions.",
            ),
        ],
        columns=5,
    )


def _render_ablation_summary(
    mixed_validation_report: Mapping[str, Any],
    promotion_summary: Mapping[str, Any],
    benchmark_key: str,
) -> None:
    """Render ablation rows that connect the UI to the report."""
    render_section_heading(
        "Ablation Summary",
        "Baseline -> candidate -> rerank -> paraphrase",
        "The progression shows how each added retrieval cue changed Recall@1 while controlling regressions.",
    )
    if benchmark_key == "mixed_sanity":
        ablation_rows = list(mixed_validation_report.get("ablation_rows", []))
    else:
        ablation_rows = [
            {
                "system": row.get("system"),
                "recall_at_1": dict(row.get("hard_benchmark", {})).get("recall_at_1"),
                "recall_at_3": dict(row.get("hard_benchmark", {})).get("recall_at_3"),
                "delta_vs_prior_recall_at_1": None,
                "regressions_vs_prior": dict(row.get("hard_benchmark", {})).get("regression_count"),
            }
            for row in promotion_summary.get("baseline_vs_candidate_vs_final_default", [])
        ]

    cards = ['<div class="stage-flow">']
    for index, row in enumerate(ablation_rows, start=1):
        delta = row.get("delta_vs_prior_recall_at_1")
        delta_text = format_percent(delta) if delta is not None else "baseline"
        regressions = row.get("regressions_vs_prior")
        regression_text = "N/A" if regressions is None else str(regressions)
        cards.append(
            f"""
            <div class="stage-card">
              <div class="stage-number">{index}</div>
              <div class="stage-title">{escape(truncate_text(str(row.get("system", "system")), 58))}</div>
              <p><strong>Recall@1:</strong> {escape(format_percent(row.get("recall_at_1")))}</p>
              <p><strong>Recall@3:</strong> {escape(format_percent(row.get("recall_at_3")))}</p>
              <p><strong>Delta:</strong> {escape(delta_text)} · <strong>Regressions:</strong> {escape(regression_text)}</p>
            </div>
            """
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)


def _render_query_table(filtered_rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """Render per-query evidence cards and return the selected row."""
    render_section_heading(
        "Per-Query Results",
        "Evidence cards instead of a spreadsheet",
        "Scan query outcomes by status, then select one query for a deeper before/after trace.",
    )
    if not filtered_rows:
        return None

    _render_query_evidence_cards(filtered_rows[:9])

    selected_query_id = st.selectbox(
        "Query detail drawer",
        options=[str(row["query_id"]) for row in filtered_rows],
        index=0,
        format_func=lambda query_id: _detail_option_label(filtered_rows, query_id),
    )
    return next(row for row in filtered_rows if row["query_id"] == selected_query_id)


def _render_query_detail(
    bundle: BenchmarkBundle,
    selected_row: Mapping[str, Any],
    captions_by_id: Mapping[str, dict[str, Any]],
) -> None:
    """Render query detail drawer with before/after and feature contributions."""
    render_section_heading(
        "Query Detail",
        "Why this query changed",
        "The drawer pairs the query, expected target, before/after top-3, and feature contributions.",
    )
    render_query_summary(
        query_text=str(selected_row["query"]),
        query_id=str(selected_row["query_id"]),
        expected_image_ids=selected_row.get("expected_image_ids", []),
        tags=selected_row.get("tags", []),
        subtitle=f"Bucket: {_primary_bucket(selected_row)}",
        slice_label=str(selected_row.get("slice", "normal_ui")),
    )

    before_results = list(selected_row.get("original_results") or selected_row.get("results") or [])[:3]
    after_results = list(selected_row.get("reranked_results") or selected_row.get("results") or [])[:3]
    before_col, after_col = st.columns(2, gap="large")
    with before_col:
        st.caption("Before top-3")
        st.dataframe(_results_frame(before_results, captions_by_id), use_container_width=True, hide_index=True)
    with after_col:
        st.caption("After top-3")
        st.dataframe(_results_frame(after_results, captions_by_id), use_container_width=True, hide_index=True)

    correction_bits = []
    if selected_row.get("corrected"):
        correction_bits.append("corrected by deterministic rerank")
    if selected_row.get("regression"):
        correction_bits.append("marked as regression")
    if selected_row.get("activation_reasons"):
        correction_bits.append(f"activated by {format_list(selected_row.get('activation_reasons', []), max_items=4)}")
    if not correction_bits:
        correction_bits.append("no stored correction event for this config")
    render_callout("Correction reason", "; ".join(correction_bits), tone="success")

    candidate_logs = list(selected_row.get("candidate_logs") or [])
    if candidate_logs:
        best_log = _candidate_log_for_after_top(selected_row, candidate_logs)
        st.caption("Feature contributions")
        _render_feature_bars(best_log)
    else:
        st.info("This selected config has no stored rerank feature-contribution log.")

    with st.expander("Raw notes", expanded=False):
        st.json(
            {
                "query_id": selected_row.get("query_id"),
                "top1_correct": selected_row.get("top1_correct"),
                "corrected": selected_row.get("corrected", False),
                "regression": selected_row.get("regression", False),
                "tags": selected_row.get("tags", []),
                "failure_bucket": selected_row.get("failure_bucket"),
                "activation_reasons": selected_row.get("activation_reasons", []),
            }
        )


def _render_bucket_explorer(rows: Sequence[Mapping[str, Any]]) -> None:
    """Render bucket counts for the full selected benchmark/config."""
    render_section_heading(
        "Bucket Explorer",
        "Failure and cue buckets",
        "These buckets make the development story visible: names, text, label-value phrases, paraphrases, layout, and same-family UI confusion.",
    )
    counts: dict[str, int] = {bucket: 0 for bucket in BUCKET_OPTIONS}
    for row in rows:
        for bucket in _row_buckets(row):
            if bucket in counts:
                counts[bucket] += 1
    cards = ['<div class="bucket-grid">']
    for bucket, count in counts.items():
        cards.append(
            f"""
            <div class="bucket-card">
              <div class="bucket-count">{count}</div>
              <div class="bucket-label">{escape(humanize_key(bucket))}</div>
              <p class="preview-note">Use the bucket filter above to inspect these cases.</p>
            </div>
            """
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)


def _render_query_evidence_cards(rows: Sequence[Mapping[str, Any]]) -> None:
    """Render compact per-query outcome cards."""
    cards = ['<div class="evidence-grid">']
    for row in rows:
        top_result = row.get("top_result") or (row.get("results") or [None])[0]
        status = _row_status(row)
        cards.append(
            f"""
            <div class="evidence-card">
              <span class="status-badge {status}">{status}</span>
              <h3>{escape(str(row.get("query_id", "query")))}</h3>
              <p>{escape(truncate_text(str(row.get("query", "")), 116))}</p>
              <p><strong>Expected:</strong> {escape(format_list(row.get("expected_image_ids", []), max_items=2))}</p>
              <p><strong>Top-1:</strong> {escape(str(top_result.get("image_id") if top_result else "N/A"))}</p>
            </div>
            """
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)


def _render_feature_bars(candidate_log: Mapping[str, Any]) -> None:
    """Render rerank feature contributions as horizontal bars."""
    contributions = []
    for feature_name, payload in dict(candidate_log.get("feature_contributions", {})).items():
        weighted = float(payload.get("weighted_score", 0.0))
        contributions.append(
            {
                "feature": humanize_key(feature_name),
                "weighted": weighted,
                "matched": format_list(payload.get("matched_terms", []), fallback="no direct terms", max_items=4),
            }
        )
    if not contributions:
        st.info("No feature contributions are stored for this row.")
        return

    max_weight = max(abs(item["weighted"]) for item in contributions) or 1.0
    html = []
    for item in sorted(contributions, key=lambda value: value["weighted"], reverse=True):
        width = min(100.0, max(2.0, abs(item["weighted"]) / max_weight * 100))
        html.append(
            f"""
            <div class="feature-bar-row">
              <div class="feature-bar-label">
                <span>{escape(item["feature"])}</span>
                <span>{item["weighted"]:.3f}</span>
              </div>
              <div class="feature-bar-track"><div class="feature-bar-fill" style="width:{width:.1f}%"></div></div>
              <div class="preview-note">{escape(item["matched"])}</div>
            </div>
            """
        )
    st.markdown("".join(html), unsafe_allow_html=True)


def _table_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Build one dataframe row for the per-query table."""
    top_result = row.get("top_result") or (row.get("results") or [None])[0]
    return {
        "query_id": row.get("query_id"),
        "query_text": truncate_text(str(row.get("query", "")), 96),
        "slice": row.get("slice", "normal_ui"),
        "expected_target": format_list(row.get("expected_image_ids", []), max_items=2),
        "predicted_target": top_result.get("image_id") if top_result else "N/A",
        "corrected?": "Yes" if row.get("corrected") else "No",
        "regression?": "Yes" if row.get("regression") else "No",
        "top1 score": format_score(float(top_result.get("similarity_score", 0.0))) if top_result else "N/A",
        "bucket": _primary_bucket(row),
        "notes": format_list(row.get("activation_reasons", []), fallback=row.get("failure_bucket", "none"), max_items=3),
    }


def _results_frame(results: Sequence[Mapping[str, Any]], captions_by_id: Mapping[str, dict[str, Any]]) -> pd.DataFrame:
    """Build a compact top-k dataframe."""
    rows = []
    for result in results:
        image_id = str(result.get("image_id", ""))
        caption = captions_by_id.get(image_id, {})
        rows.append(
            {
                "Rank": result.get("rank"),
                "Image": image_id,
                "Title": caption.get("main_subject") or humanize_key(image_id),
                "Score": format_score(float(result.get("similarity_score", 0.0))),
            }
        )
    return pd.DataFrame(rows)


def _feature_contribution_frame(candidate_log: Mapping[str, Any]) -> pd.DataFrame:
    """Build a feature-contribution dataframe."""
    rows = []
    for feature_name, payload in dict(candidate_log.get("feature_contributions", {})).items():
        rows.append(
            {
                "Feature": humanize_key(feature_name),
                "Raw": float(payload.get("raw_score", 0.0)),
                "Weight": float(payload.get("weight", 0.0)),
                "Weighted": float(payload.get("weighted_score", 0.0)),
                "Matched terms": format_list(payload.get("matched_terms", []), max_items=4),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values("Weighted", ascending=False)


def _candidate_log_for_after_top(
    row: Mapping[str, Any],
    candidate_logs: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Return the candidate log corresponding to the after top-1 result."""
    after_top = row.get("after_top_result") or row.get("top_result")
    after_image_id = str(after_top.get("image_id")) if after_top else ""
    for candidate_log in candidate_logs:
        if str(candidate_log.get("image_id")) == after_image_id:
            return candidate_log
    return candidate_logs[0]


def _slice_matches(row: Mapping[str, Any], selected_slice: str) -> bool:
    """Return whether a row matches the selected slice."""
    return selected_slice == "all" or str(row.get("slice")) == selected_slice


def _status_matches(row: Mapping[str, Any], status_filter: str) -> bool:
    """Return whether a row matches the selected status."""
    if status_filter == "all":
        return True
    if status_filter == "corrected":
        return bool(row.get("corrected"))
    if status_filter == "unresolved":
        return not bool(row.get("top1_correct"))
    if status_filter == "regressed":
        return bool(row.get("regression"))
    return True


def _row_status(row: Mapping[str, Any]) -> str:
    """Return a compact status label for one query row."""
    if row.get("regression"):
        return "regressed"
    if row.get("corrected"):
        return "corrected"
    return "unchanged"


def _bucket_matches(row: Mapping[str, Any], selected_buckets: Sequence[str]) -> bool:
    """Return whether a row matches selected cue/failure buckets."""
    if not selected_buckets:
        return True
    row_buckets = set(_row_buckets(row))
    return bool(row_buckets & set(selected_buckets))


def _row_buckets(row: Mapping[str, Any]) -> list[str]:
    """Map query tags and rerank activation reasons to portfolio bucket names."""
    tags = set(row.get("tags", []))
    activation_reasons = set(row.get("activation_reasons", []))
    buckets: list[str] = []
    if "person_name" in tags:
        buckets.append("person-name")
    if "visible_text" in tags:
        buckets.append("visible-text")
    if "label_value_phrase_overlap" in activation_reasons:
        buckets.append("label-value phrase")
    if "paraphrase" in tags or "question_paraphrase_overlap" in activation_reasons:
        buckets.append("paraphrase")
    if "layout_structure" in tags:
        buckets.append("layout")
    if "hard_negative" in tags or "ui_family_disambiguation" in tags:
        buckets.append("same-family UI confusion")
    return buckets or ["other"]


def _primary_bucket(row: Mapping[str, Any]) -> str:
    """Return the most useful bucket label for table display."""
    if not row.get("top1_correct") and row.get("failure_bucket"):
        return str(row["failure_bucket"])
    buckets = _row_buckets(row)
    return humanize_key(buckets[0]) if buckets else "Correct"


def _detail_option_label(rows: Sequence[Mapping[str, Any]], query_id: str) -> str:
    """Format query detail selector labels."""
    row = next(item for item in rows if item["query_id"] == query_id)
    return f"{query_id} · {truncate_text(str(row.get('query', '')), 92)}"
