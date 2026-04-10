"""Small photo gallery helpers for the simplified app."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Mapping, Sequence

import streamlit as st

from src.core.schemas import RetrievalResult
from ui.utils.formatters import format_list, format_score, truncate_text
from ui.utils.formatters import to_badge_html
from ui.utils.photo_library import PhotoEntry, get_photo_by_image_id


def render_photo_grid(photos: Sequence[PhotoEntry], columns: int = 2) -> None:
    """Render a responsive grid of photo cards."""
    if not photos:
        st.info("No photos match this view.")
        return

    for start in range(0, len(photos), columns):
        row = photos[start : start + columns]
        for photo, column in zip(row, st.columns(len(row))):
            with column:
                _render_photo_card(photo)


def render_photo_spotlight(photo: PhotoEntry) -> None:
    """Render one featured photo with short metadata."""
    image_col, detail_col = st.columns([1.35, 0.95], gap="large")
    with image_col:
        if Path(photo.path).is_file():
            st.image(photo.path, use_container_width=True)
        else:
            st.warning("Photo file is missing.")

    with detail_col:
        st.markdown(
            (
                "<div class=\"portfolio-card prose-card\">"
                f"<h3>{escape(photo.title)}</h3>"
                f"<p>{escape(photo.caption)}</p>"
                f"<p><strong>Theme:</strong> {escape(photo.theme)}</p>"
                f"<div class=\"badge-row\">{to_badge_html(photo.tags)}</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )


def render_search_results(
    results: Sequence[RetrievalResult],
    caption_lookup: Mapping[str, object],
) -> None:
    """Render compact search results for the local model demo."""
    if not results:
        st.info("No results yet. Try one short descriptive query.")
        return

    for result, column in zip(results, st.columns(len(results))):
        with column:
            with st.container(border=True):
                photo = get_photo_by_image_id(result.image_id)
                image_path = result.image_path or (photo.path if photo else None)
                if image_path and Path(str(image_path)).is_file():
                    st.image(str(image_path), use_container_width=True)
                else:
                    st.caption("Photo missing.")

                title = photo.title if photo else result.image_id
                st.markdown(f"**#{result.rank} {title}**")
                st.caption(f"score {format_score(result.similarity_score)}")

                caption_record = caption_lookup.get(result.image_id)
                if caption_record:
                    st.write(truncate_text(caption_record.caption_text, 130))
                    cues = list(getattr(caption_record, "distinctive_cues", []) or [])
                    if cues:
                        st.caption(f"cue: {format_list(cues, max_items=3)}")


def _render_photo_card(photo: PhotoEntry) -> None:
    """Render one compact photo card."""
    with st.container(border=True):
        if Path(photo.path).is_file():
            st.image(photo.path, use_container_width=True)
        else:
            st.caption("Photo missing.")
        st.markdown(f"**{photo.title}**")
        st.caption(photo.caption)
        st.markdown(f"<div class=\"badge-row\">{to_badge_html(photo.tags)}</div>", unsafe_allow_html=True)
