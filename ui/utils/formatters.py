"""Formatting helpers shared across the Streamlit portfolio app."""

from __future__ import annotations

from html import escape
import re
from typing import Iterable


WHITESPACE_PATTERN = re.compile(r"\s+")


def humanize_key(value: str) -> str:
    """Turn a snake_case or slug-like key into a clean label."""
    normalized = value.replace("-", " ").replace("_", " ").strip()
    words = [word.upper() if len(word) <= 3 else word.capitalize() for word in normalized.split()]
    return " ".join(words)


def format_percent(value: float | None, digits: int = 1) -> str:
    """Format a ratio as a percentage string."""
    if value is None:
        return "N/A"
    return f"{value * 100:.{digits}f}%"


def format_score(value: float | None, digits: int = 3) -> str:
    """Format a scalar score with a consistent decimal width."""
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}"


def format_delta(value: float | None, digits: int = 1, as_percent: bool = True) -> str:
    """Format a signed delta string."""
    if value is None:
        return "No change"
    if as_percent:
        return f"{value * 100:+.{digits}f} pts"
    return f"{value:+.{digits}f}"


def format_list(items: Iterable[str], fallback: str = "None", max_items: int = 4) -> str:
    """Format a short sequence of strings for compact UI copy."""
    cleaned = [item.strip() for item in items if item and item.strip()]
    if not cleaned:
        return fallback
    visible = cleaned[:max_items]
    suffix = "" if len(cleaned) <= max_items else f" +{len(cleaned) - max_items} more"
    return ", ".join(visible) + suffix


def normalize_text(value: str) -> str:
    """Lowercase and collapse whitespace for fuzzy comparisons."""
    return WHITESPACE_PATTERN.sub(" ", str(value).strip().lower())


def truncate_text(value: str, limit: int = 140) -> str:
    """Trim long copy without cutting words too aggressively."""
    if len(value) <= limit:
        return value
    trimmed = value[: max(0, limit - 1)].rsplit(" ", 1)[0].strip()
    return f"{trimmed or value[: limit - 1]}…"


def to_badge_html(items: Iterable[str], badge_class: str = "query-chip") -> str:
    """Render a flat list of labels as HTML badges."""
    badges = [f"<span class=\"{badge_class}\">{escape(humanize_key(item))}</span>" for item in items if item]
    return "".join(badges)
