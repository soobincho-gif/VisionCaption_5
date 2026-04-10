"""Chart helpers for benchmark and overview pages."""

from __future__ import annotations

from typing import Mapping, Sequence

import altair as alt
import pandas as pd
import streamlit as st

from ui.utils.formatters import humanize_key

ACCENT = "#0F766E"
ACCENT_SOFT = "#CBE7E4"
WARN = "#C2410C"


def render_progress_chart(rows: Sequence[dict], title: str) -> None:
    """Render a small stage-by-stage Recall@1 chart."""
    if not rows:
        return
    frame = pd.DataFrame(
        [
            {
                "Display": humanize_key(str(row.get("role") or row.get("system"))),
                "Recall@1": float(row["mixed_sanity"]["recall_at_1"] if "mixed_sanity" in row else row["recall_at_1"]),
            }
            for row in rows
        ]
    )
    frame["Order"] = range(1, len(frame) + 1)
    display_order = frame.sort_values("Order")["Display"].tolist()
    chart = (
        alt.Chart(frame)
        .mark_line(point=alt.OverlayMarkDef(filled=True, fill=ACCENT, size=110), strokeWidth=3, color=ACCENT)
        .encode(
            x=alt.X("Display:N", axis=alt.Axis(title=None, labelAngle=0), sort=display_order),
            y=alt.Y("Recall@1:Q", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0.6, 1.02])),
            tooltip=["Display:N", alt.Tooltip("Recall@1:Q", format=".1%")],
        )
        .properties(height=260, title=title)
    )
    label_layer = alt.Chart(frame).mark_text(dy=-16, color="#102A43", fontSize=12).encode(
        x=alt.X("Display:N", sort=display_order),
        y="Recall@1:Q",
        text=alt.Text("Recall@1:Q", format=".1%"),
    )
    st.altair_chart(chart + label_layer, use_container_width=True)


def render_accuracy_breakdown_chart(metric_map: Mapping[str, Mapping[str, float]], title: str) -> None:
    """Render a horizontal bar chart for tag or slice breakdowns."""
    if not metric_map:
        return
    frame = pd.DataFrame(
        [
            {
                "Bucket": humanize_key(label),
                "Recall@1": float(values.get("recall_at_1", 0.0)),
            }
            for label, values in metric_map.items()
        ]
    ).sort_values("Recall@1", ascending=True)
    chart = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6, color=ACCENT)
        .encode(
            x=alt.X("Recall@1:Q", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
            y=alt.Y("Bucket:N", sort=None, title=None),
            tooltip=["Bucket:N", alt.Tooltip("Recall@1:Q", format=".1%")],
        )
        .properties(height=max(180, len(frame) * 28), title=title)
    )
    st.altair_chart(chart, use_container_width=True)


def render_failure_bucket_chart(bucket_counts: Mapping[str, int], title: str) -> None:
    """Render a compact failure-bucket chart."""
    if not bucket_counts:
        return
    frame = pd.DataFrame(
        [{"Bucket": humanize_key(bucket), "Count": int(count)} for bucket, count in bucket_counts.items()]
    ).sort_values("Count", ascending=False)
    chart = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color=WARN)
        .encode(
            x=alt.X("Bucket:N", sort="-y", title=None, axis=alt.Axis(labelAngle=-20)),
            y=alt.Y("Count:Q", title=None),
            tooltip=["Bucket:N", "Count:Q"],
        )
        .properties(height=240, title=title)
    )
    st.altair_chart(chart, use_container_width=True)
