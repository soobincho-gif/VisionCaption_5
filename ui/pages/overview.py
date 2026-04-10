"""Overview page for the VisionCaption portfolio app."""

from __future__ import annotations

import streamlit as st

from ui.components.metric_cards import MetricCard, render_metric_cards
from ui.components.query_panels import render_callout, render_section_heading, render_status_badges
from ui.utils.formatters import format_score
from ui.utils.load_artifacts import ArtifactLoadError, load_portfolio_artifacts


def render() -> None:
    """Render the project overview page."""
    try:
        artifacts = load_portfolio_artifacts()
    except ArtifactLoadError as exc:
        st.error(str(exc))
        return

    promotion_summary = artifacts.promotion_summary
    default_config = dict(promotion_summary.get("default_configuration", {}))
    hard_result = dict(promotion_summary.get("hard_benchmark_result", {}))
    mixed_result = dict(promotion_summary.get("mixed_sanity_result", {}))

    hero_copy_col, hero_preview_col = st.columns([1.12, 0.88], gap="large")
    with hero_copy_col:
        st.markdown(
            """
            <div class="product-hero">
              <div class="eyebrow">VisionCaption · Prompt-Fidelity Retrieval</div>
              <h1>Prompt-Fidelity Retrieval for UI-Heavy Visual Queries</h1>
              <p class="hero-body">
                VisionCaption is a text-to-image retrieval system optimized for UI screenshots, historical chat interfaces, and mixed visual prompts.
              </p>
              <p class="hero-body">
                Validated with structured representation, deterministic reranking, and offline frozen-artifact replay.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cta_left, cta_right = st.columns(2)
        with cta_left:
            st.link_button("Try Live Demo", "/live-demo", use_container_width=True)
        with cta_right:
            st.link_button("Explore Benchmarks", "/benchmark-explorer", use_container_width=True)
    with hero_preview_col:
        st.markdown(
            """
            <div class="hero-preview-panel">
              <div class="eyebrow">Mini Demo Preview</div>
              <div class="preview-note">
                Query: beige editorial AI chat about imagination and discovery rather than AI today
              </div>
              <div class="preview-row">
                <div class="preview-card">
                  <div class="preview-label">Before</div>
                  <div class="preview-value">history_chat_einstein_ai</div>
                </div>
                <div class="preview-card after">
                  <div class="preview-label">After</div>
                  <div class="preview-value">history_chat_einstein_philosophical</div>
                </div>
              </div>
              <div class="preview-note">
                Fixed by question paraphrase overlap while keeping the frozen replay fully reproducible.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_metric_cards(
        [
            MetricCard(
                label="Hard Benchmark R@1",
                value=format_score(float(hard_result.get("recall_at_1", 0.0)), digits=4),
                delta="final default",
                help_text="Recall@1 on the curated hard UI-heavy benchmark.",
                tone="primary",
            ),
            MetricCard(
                label="Mixed Sanity R@1",
                value=format_score(float(mixed_result.get("recall_at_1", 0.0)), digits=4),
                delta=str(mixed_result.get("execution_mode", "frozen replay")).replace("_", " "),
                help_text="Broader mixed visual replay used for promotion validation.",
            ),
            MetricCard(
                label="Recall@3",
                value=format_score(float(mixed_result.get("recall_at_3", hard_result.get("recall_at_3", 0.0))), digits=4),
                help_text="Expected target is present in the top 3 across the promoted replay.",
            ),
            MetricCard(
                label="Observed Regressions",
                value=str(int(mixed_result.get("regression_count", hard_result.get("regression_count", 0)))),
                delta="0 blocking regressions",
                help_text="Regression count in the trusted frozen-artifact validation path.",
            ),
        ]
    )

    render_section_heading(
        "What changed",
        "From generic captions to prompt-fidelity retrieval",
        "The improvement is not just a higher score; it is a more explicit retrieval contract for UI screenshots and mixed prompts.",
    )
    st.markdown(
        """
        <div class="stage-flow">
          <div class="stage-card">
            <div class="stage-number">1</div>
            <div class="stage-title">Representation upgrade</div>
            <p>caption_only becomes caption_plus_selected_structured with named entity, exact text, and component cues.</p>
          </div>
          <div class="stage-card">
            <div class="stage-number">2</div>
            <div class="stage-title">Deterministic rerank</div>
            <p>Only the top-3 candidates are reranked using visible text, label-value phrases, and component overlap.</p>
          </div>
          <div class="stage-card">
            <div class="stage-number">3</div>
            <div class="stage-title">Paraphrase guardrail</div>
            <p>Question paraphrase overlap catches UI prompts where the wording differs but the intent is visible on screen.</p>
          </div>
          <div class="stage-card">
            <div class="stage-number">4</div>
            <div class="stage-title">Frozen replay</div>
            <p>Promotion is validated by offline frozen-artifact replay with zero observed regressions.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    config_col, caveat_col = st.columns([1.05, 0.95], gap="large")
    with config_col:
        render_section_heading(
            "Current default config",
            "Promoted settings",
            "The app surfaces the exact default as product configuration rather than burying it in logs.",
        )
        render_status_badges(
            [
                f"Representation: {default_config.get('representation_mode', 'caption_plus_selected_structured')}",
                f"Rerank: {default_config.get('rerank', 'deterministic_top3_rerank')}",
                f"Paraphrase cue: enabled ({default_config.get('question_paraphrase_overlap', 0.25)})",
                "Replay mode: frozen artifact validated",
            ]
        )
    with caveat_col:
        render_section_heading(
            "Validation caveat",
            "Trusted, reproducible, and honest",
            "The demo is intentionally transparent about which validation path is trusted today.",
        )
        render_callout(
            "Frozen replay is the source of truth",
            str(
                promotion_summary.get(
                    "validation_caveat",
                    "Trusted validation uses frozen-artifact replay; end-to-end rebuild is pending.",
                )
            ),
            tone="warning",
        )
        st.caption("Demo mode uses frozen artifacts for reproducibility. Uploaded images are session-only temporary records.")
