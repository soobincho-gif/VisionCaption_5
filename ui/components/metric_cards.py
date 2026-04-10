"""Metric-card components for the portfolio app."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Sequence

import streamlit as st


@dataclass(frozen=True)
class MetricCard:
    """Structured content for a single metric card."""

    label: str
    value: str
    delta: str | None = None
    help_text: str | None = None
    tone: str = "default"


def render_metric_cards(cards: Sequence[MetricCard], columns: int | None = None) -> None:
    """Render a responsive row of metric cards."""
    if not cards:
        return

    column_count = columns or min(4, len(cards))
    rows = [cards[index : index + column_count] for index in range(0, len(cards), column_count)]
    for row in rows:
        for card, column in zip(row, st.columns(len(row))):
            delta_html = (
                f"<div class=\"metric-delta tone-{escape(card.tone)}\">{escape(card.delta)}</div>"
                if card.delta
                else ""
            )
            help_html = f"<p class=\"metric-help\">{escape(card.help_text)}</p>" if card.help_text else ""
            card_class = (
                f"portfolio-card metric-card metric-card-{escape(card.tone)}"
                if card.tone != "default"
                else "portfolio-card metric-card"
            )
            with column:
                st.markdown(
                    (
                        f"<div class=\"{card_class}\">"
                        f"<div class=\"metric-label\">{escape(card.label)}</div>"
                        f"<div class=\"metric-value\">{escape(card.value)}</div>"
                        f"{delta_html}{help_html}</div>"
                    ),
                    unsafe_allow_html=True,
                )
