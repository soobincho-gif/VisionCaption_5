"""Shared query context panels and badge helpers."""

from __future__ import annotations

from html import escape
from typing import Sequence

import streamlit as st

from ui.utils.formatters import format_list, humanize_key, to_badge_html


def render_section_heading(eyebrow: str, title: str, body: str) -> None:
    """Render a lightweight section header with consistent spacing."""
    st.markdown(
        (
            "<div class=\"section-heading\">"
            f"<div class=\"eyebrow\">{escape(eyebrow)}</div>"
            f"<h2 class=\"section-title\">{escape(title)}</h2>"
            f"<p class=\"section-body\">{escape(body)}</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_tag_badges(tags: Sequence[str]) -> None:
    """Render query tags as compact badges."""
    if not tags:
        return
    st.markdown(f"<div class=\"badge-row\">{to_badge_html(tags)}</div>", unsafe_allow_html=True)


def render_status_badges(items: Sequence[str], tone: str = "default") -> None:
    """Render compact status chips for config and artifact state."""
    if not items:
        return
    chip_class = f"status-chip tone-{tone}" if tone != "default" else "status-chip"
    html = "".join(f"<span class=\"{chip_class}\">{escape(item)}</span>" for item in items)
    st.markdown(f"<div class=\"artifact-strip\">{html}</div>", unsafe_allow_html=True)


def render_query_summary(
    query_text: str,
    query_id: str,
    expected_image_ids: Sequence[str],
    tags: Sequence[str],
    subtitle: str | None = None,
    slice_label: str | None = None,
) -> None:
    """Render a compact query summary panel."""
    metadata_bits = [f"Query ID: {query_id}"]
    if slice_label:
        metadata_bits.append(f"Slice: {humanize_key(slice_label)}")
    metadata_bits.append(f"Expected: {format_list(expected_image_ids, max_items=3)}")
    if subtitle:
        metadata_bits.append(subtitle)

    st.markdown(
        (
            "<div class=\"portfolio-card query-summary\">"
            f"<div class=\"query-text\">{escape(query_text)}</div>"
            f"<div class=\"query-meta\">{' | '.join(escape(bit) for bit in metadata_bits)}</div>"
            f"{to_badge_html(tags)}</div>"
        ),
        unsafe_allow_html=True,
    )


def render_callout(title: str, body: str, tone: str = "info") -> None:
    """Render a styled callout box."""
    st.markdown(
        (
            f"<div class=\"portfolio-card callout tone-{escape(tone)}\">"
            f"<div class=\"callout-title\">{escape(title)}</div>"
            f"<p class=\"callout-body\">{escape(body)}</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
