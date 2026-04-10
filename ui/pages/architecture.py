"""Method and architecture page for the VisionCaption portfolio app."""

from __future__ import annotations

import streamlit as st

from ui.components.metric_cards import MetricCard, render_metric_cards
from ui.components.query_panels import render_callout, render_section_heading, render_status_badges
from ui.utils.formatters import format_percent
from ui.utils.load_artifacts import ArtifactLoadError, load_portfolio_artifacts


def render() -> None:
    """Render the method and architecture page."""
    try:
        artifacts = load_portfolio_artifacts()
    except ArtifactLoadError as exc:
        st.error(str(exc))
        return

    report = artifacts.mixed_validation_report
    experiment_setting = dict(report.get("experiment_setting", {}))
    default_config = dict(artifacts.promotion_summary.get("default_configuration", {}))

    render_section_heading(
        "Method & Architecture",
        "Prompt-fidelity retrieval pipeline",
        "The app demonstrates a frozen, reproducible retrieval stack for UI screenshots, historical chat screens, and mixed visual queries.",
    )

    render_metric_cards(
        [
            MetricCard(
                label="Benchmark Queries",
                value=str(report.get("query_count", 0)),
                help_text="Frozen mixed-sanity replay queries available in Benchmark Explorer.",
            ),
            MetricCard(
                label="Hard UI Slice",
                value=str(dict(report.get("slice_counts", {})).get("hard_ui", 0)),
                help_text="UI-heavy hard-negative prompts in the broader validation set.",
            ),
            MetricCard(
                label="Default Recall@1",
                value=format_percent(
                    float(
                        dict(report.get("systems", {}))
                        .get("best_hard_config", {})
                        .get("recall_at_1", 0.0)
                    )
                ),
                help_text="Promoted default result on trusted frozen replay.",
            ),
            MetricCard(
                label="Artifact Mode",
                value=str(report.get("artifact_mode", "frozen")).capitalize(),
                help_text="Demo avoids live rebuilds unless explicitly requested by upload actions.",
            ),
        ]
    )

    render_status_badges(
        [
            f"Representation: {default_config.get('representation_mode', 'caption_plus_selected_structured')}",
            f"Rerank top-n: {default_config.get('rerank_top_n', 3)}",
            f"Question paraphrase weight: {default_config.get('question_paraphrase_overlap', 0.25)}",
            f"Promotion: {experiment_setting.get('promotion_status', 'broader_default')}",
        ]
    )

    render_callout(
        "Pipeline summary",
        (
            "Images are captioned into structured retrieval text, embedded once, replayed from frozen artifacts, "
            "and optionally reranked with deterministic feature contributions for UI-specific disambiguation."
        ),
        tone="success",
    )

    st.markdown(
        """
        <div class="flow-grid">
          <div class="portfolio-card flow-card">
            <div class="flow-step">1. Structured representation</div>
            <p>Caption text is augmented with selected structured fields, exact text cues, named entity cues, and component cues.</p>
          </div>
          <div class="portfolio-card flow-card">
            <div class="flow-step">2. Frozen embedding artifacts</div>
            <p>Baseline and candidate embeddings are stored as JSONL artifacts so evaluation can be replayed offline.</p>
          </div>
          <div class="portfolio-card flow-card">
            <div class="flow-step">3. Deterministic top-3 rerank</div>
            <p>The reranker uses visible text, label-value phrases, component overlap, entity matches, and question paraphrase overlap.</p>
          </div>
          <div class="portfolio-card flow-card">
            <div class="flow-step">4. Evidence UI</div>
            <p>Live Demo shows one query decision, while Benchmark Explorer exposes slice metrics and query-level traces.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    detail_col, artifact_col = st.columns([1.05, 0.95], gap="large")
    with detail_col:
        st.markdown(
            """
            <div class="portfolio-card prose-card">
              <h3>Why this architecture is portfolio-ready</h3>
              <p>The UI does not simply claim the model improved. It shows the representation contract, the rerank features, and before/after query evidence.</p>
              <p>That makes the system explainable as an engineering project rather than a one-off demo.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with artifact_col:
        st.markdown(
            """
            <div class="portfolio-card prose-card">
              <h3>Primary artifacts</h3>
              <p><code>data/samples/prompt_fidelity/benchmark_mixed_sanity_v1.json</code></p>
              <p><code>outputs/eval/.../candidate_rerank_with_paraphrase/results.json</code></p>
              <p><code>outputs/eval/.../candidate_rerank_with_paraphrase/query_logs.jsonl</code></p>
              <p><code>outputs/eval/.../default_promotion_summary.json</code></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
