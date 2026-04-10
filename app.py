"""Entrypoint for the VisionCaption Streamlit portfolio app."""

from __future__ import annotations

import streamlit as st

from ui.pages.architecture import render as render_architecture
from ui.pages.benchmark_explorer import render as render_benchmark_explorer
from ui.pages.live_demo import render as render_live_demo
from ui.pages.overview import render as render_overview


def inject_global_styles() -> None:
    """Apply small portfolio-oriented styles on top of Streamlit."""
    st.markdown(
        """
        <style>
          .stApp {
            background:
              radial-gradient(circle at top left, rgba(15, 118, 110, 0.08), transparent 30%),
              linear-gradient(180deg, #f8fafc 0%, #f4f7f9 100%);
          }
          .block-container {
            max-width: 1180px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
          }
          h1, h2, h3 {
            font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
            letter-spacing: -0.02em;
            color: #102a43;
          }
          p, li, [data-testid="stMarkdownContainer"] {
            font-family: "SF Pro Text", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
          }
          .hero-shell {
            padding: 1.4rem 1.5rem 1.6rem 1.5rem;
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(232,245,242,0.96));
            box-shadow: 0 18px 50px rgba(15, 23, 42, 0.06);
            margin-bottom: 1.2rem;
          }
          .product-hero {
            position: relative;
            overflow: hidden;
            padding: 1.25rem 1.35rem;
            border: 1px solid rgba(15, 23, 42, 0.075);
            border-radius: 26px;
            background:
              radial-gradient(circle at 82% 12%, rgba(255, 177, 73, 0.22), transparent 26%),
              radial-gradient(circle at 14% 16%, rgba(15, 118, 110, 0.14), transparent 30%),
              linear-gradient(135deg, #ffffff 0%, #eef8f5 55%, #fff7ed 100%);
            box-shadow: 0 24px 70px rgba(15, 23, 42, 0.09);
            margin-bottom: 1rem;
          }
          .product-hero h1 {
            margin: 0;
            max-width: 720px;
            font-size: clamp(1.75rem, 2.7vw, 2.55rem);
            line-height: 1.07;
            text-wrap: balance;
          }
          .product-hero .hero-body {
            max-width: 620px;
          }
          .hero-preview-panel {
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 26px;
            background: rgba(255, 255, 255, 0.74);
            backdrop-filter: blur(12px);
            padding: 1rem;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.8), 0 18px 38px rgba(15, 23, 42, 0.08);
            height: 100%;
          }
          .preview-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
            margin: 0.75rem 0;
          }
          .preview-card {
            border-radius: 18px;
            padding: 0.8rem;
            background: #f8fafc;
            border: 1px solid rgba(15, 23, 42, 0.08);
          }
          .preview-card.after {
            background: #ecfdf5;
            border-color: rgba(15, 118, 110, 0.18);
          }
          .preview-label {
            color: #486581;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
          }
          .preview-value {
            color: #102a43;
            font-size: 0.96rem;
            font-weight: 850;
            line-height: 1.25;
            margin-top: 0.25rem;
            overflow-wrap: anywhere;
          }
          .preview-note {
            color: #486581;
            font-size: 0.86rem;
            line-height: 1.5;
          }
          .eyebrow {
            font-size: 0.78rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: #0f766e;
            font-weight: 700;
            margin-bottom: 0.45rem;
          }
          .hero-title {
            margin: 0;
            font-size: clamp(2rem, 4vw, 3.25rem);
            line-height: 1.02;
          }
          .hero-body, .section-body, .metric-help, .callout-body, .query-meta, .prose-card p {
            color: #486581;
            line-height: 1.6;
          }
          .section-heading {
            margin: 0.3rem 0 0.9rem 0;
          }
          .section-title {
            margin: 0.15rem 0 0.35rem 0;
            font-size: 1.7rem;
          }
          .portfolio-card {
            border: 1px solid rgba(15, 23, 42, 0.08);
            background: rgba(255, 255, 255, 0.92);
            border-radius: 22px;
            padding: 1rem 1rem 1.05rem 1rem;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.05);
            margin-bottom: 0.85rem;
          }
          .metric-card {
            min-height: 148px;
          }
          .metric-card-primary {
            border-color: rgba(15, 118, 110, 0.22);
            background:
              radial-gradient(circle at 100% 0%, rgba(15, 118, 110, 0.16), transparent 35%),
              linear-gradient(135deg, #0f766e, #102a43);
            color: white;
            transform: translateY(-3px);
            box-shadow: 0 24px 58px rgba(15, 118, 110, 0.2);
          }
          .metric-card-primary .metric-label,
          .metric-card-primary .metric-help,
          .metric-card-primary .metric-delta {
            color: rgba(255, 255, 255, 0.78);
          }
          .metric-card-primary .metric-value {
            color: #ffffff;
            font-size: 2.35rem;
          }
          .metric-label {
            color: #486581;
            font-size: 0.92rem;
            font-weight: 600;
            margin-bottom: 0.45rem;
          }
          .metric-value {
            color: #102a43;
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.25rem;
          }
          .metric-delta {
            color: #0f766e;
            font-size: 0.9rem;
            font-weight: 700;
          }
          .query-summary .query-text {
            font-size: 1.12rem;
            line-height: 1.5;
            color: #102a43;
            font-weight: 600;
            margin-bottom: 0.55rem;
          }
          .badge-row, .query-summary span {
            margin-top: 0.5rem;
          }
          .query-chip {
            display: inline-block;
            margin: 0.4rem 0.4rem 0 0;
            padding: 0.26rem 0.62rem;
            border-radius: 999px;
            background: #e3f4f1;
            color: #0f766e;
            font-size: 0.78rem;
            font-weight: 700;
          }
          .query-chip.tone-muted, .status-chip.tone-muted {
            background: #edf2f7;
            color: #486581;
          }
          .query-chip.tone-warning, .status-chip.tone-warning {
            background: #fff7ed;
            color: #c2410c;
          }
          .status-chip {
            display: inline-block;
            margin: 0.28rem 0.32rem 0.28rem 0;
            padding: 0.32rem 0.68rem;
            border-radius: 999px;
            background: #e3f4f1;
            color: #0f766e;
            font-size: 0.78rem;
            font-weight: 800;
            border: 1px solid rgba(15, 118, 110, 0.12);
          }
          .mini-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 0.9rem;
            margin: 0.75rem 0 1rem 0;
          }
          .mini-card {
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 20px;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.045);
          }
          .mini-card h3, .result-hero h3 {
            color: #102a43;
            font-size: 1.02rem;
            font-weight: 850;
            margin: 0 0 0.35rem 0;
          }
          .mini-card p, .mini-card li {
            color: #486581;
            line-height: 1.55;
          }
          .mini-card ul {
            padding-left: 1.05rem;
            margin-bottom: 0;
          }
          .stage-flow {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 0.9rem;
            margin: 0.75rem 0 1rem 0;
          }
          .stage-card {
            position: relative;
            min-height: 178px;
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 24px;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.94);
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.05);
          }
          .stage-number {
            width: 2rem;
            height: 2rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            background: #0f766e;
            color: white;
            font-weight: 900;
            margin-bottom: 0.75rem;
          }
          .stage-title {
            color: #102a43;
            font-weight: 900;
            font-size: 1.02rem;
            margin-bottom: 0.35rem;
          }
          .stage-card p {
            color: #486581;
            line-height: 1.55;
            margin: 0;
          }
          .demo-console {
            border: 1px solid rgba(15, 118, 110, 0.14);
            border-radius: 30px;
            padding: 1rem;
            background:
              radial-gradient(circle at 12% 0%, rgba(20, 133, 120, 0.12), transparent 30%),
              rgba(255, 255, 255, 0.95);
            box-shadow: 0 20px 58px rgba(15, 23, 42, 0.07);
            margin-bottom: 1rem;
          }
          .query-playground {
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 24px;
            padding: 1rem;
            background: rgba(248, 250, 252, 0.8);
          }
          .result-hero {
            border: 1px solid rgba(15, 118, 110, 0.16);
            border-radius: 26px;
            padding: 1.05rem;
            background:
              radial-gradient(circle at top right, rgba(20, 133, 120, 0.12), transparent 34%),
              rgba(255, 255, 255, 0.95);
            box-shadow: 0 18px 48px rgba(15, 23, 42, 0.06);
            margin: 0.8rem 0 1rem 0;
          }
          .result-meta {
            color: #486581;
            font-size: 0.92rem;
            line-height: 1.55;
          }
          .result-score-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.55rem;
            margin-top: 0.9rem;
          }
          .score-pill {
            border-radius: 16px;
            background: rgba(15, 118, 110, 0.08);
            padding: 0.62rem;
          }
          .score-pill strong {
            display: block;
            color: #102a43;
            font-size: 1.05rem;
          }
          .score-pill span {
            color: #486581;
            font-size: 0.76rem;
            font-weight: 700;
          }
          .upload-card {
            border: 1px dashed rgba(15, 118, 110, 0.32);
            border-radius: 26px;
            background: rgba(236, 253, 245, 0.44);
            padding: 1rem;
          }
          .metadata-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.6rem;
            margin-top: 0.75rem;
          }
          .metadata-item {
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.82);
            padding: 0.7rem;
            border: 1px solid rgba(15, 23, 42, 0.06);
          }
          .metadata-item span {
            display: block;
            color: #486581;
            font-size: 0.73rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.06em;
          }
          .metadata-item strong {
            color: #102a43;
            font-size: 0.95rem;
          }
          .evidence-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 0.85rem;
            margin: 0.8rem 0;
          }
          .evidence-card {
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 22px;
            padding: 0.95rem;
            background: rgba(255, 255, 255, 0.94);
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.045);
          }
          .evidence-card h3 {
            font-size: 1rem;
            margin: 0 0 0.45rem 0;
          }
          .evidence-card p {
            color: #486581;
            margin: 0.2rem 0;
            line-height: 1.5;
          }
          .status-badge {
            display: inline-block;
            border-radius: 999px;
            padding: 0.24rem 0.58rem;
            font-size: 0.72rem;
            font-weight: 850;
          }
          .status-badge.corrected {
            background: #dcfce7;
            color: #166534;
          }
          .status-badge.unchanged {
            background: #e0f2fe;
            color: #075985;
          }
          .status-badge.regressed {
            background: #fee2e2;
            color: #991b1b;
          }
          .feature-bar-row {
            margin: 0.55rem 0;
          }
          .feature-bar-label {
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            color: #102a43;
            font-weight: 800;
            font-size: 0.86rem;
            margin-bottom: 0.25rem;
          }
          .feature-bar-track {
            height: 0.64rem;
            border-radius: 999px;
            background: #e2e8f0;
            overflow: hidden;
          }
          .feature-bar-fill {
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, #0f766e, #f59e0b);
          }
          .bucket-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.8rem;
            margin-top: 0.8rem;
          }
          .bucket-card {
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.94);
            padding: 0.9rem;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.045);
          }
          .bucket-count {
            color: #102a43;
            font-size: 2rem;
            font-weight: 900;
            letter-spacing: -0.04em;
          }
          .bucket-label {
            color: #486581;
            font-size: 0.85rem;
            font-weight: 800;
          }
          .artifact-strip {
            margin: 0.4rem 0 1rem 0;
          }
          .callout.tone-warning {
            border-color: rgba(194, 65, 12, 0.18);
            background: rgba(255, 247, 237, 0.98);
          }
          .callout.tone-success {
            border-color: rgba(15, 118, 110, 0.18);
            background: rgba(236, 253, 245, 0.98);
          }
          .callout-title, .flow-step, .prose-card h3 {
            color: #102a43;
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
          }
          .flow-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.9rem;
            margin-bottom: 1rem;
          }
          .flow-card p {
            margin: 0;
            color: #486581;
          }
          .stButton > button, .stDownloadButton > button {
            border-radius: 18px;
            border: 1px solid rgba(15, 118, 110, 0.2);
            background: linear-gradient(135deg, #0f766e, #148578);
            color: white;
            font-weight: 700;
            min-height: 2.72rem;
            padding: 0.55rem 1rem;
            line-height: 1.2;
            white-space: normal;
          }
          [data-testid="stLinkButton"] a {
            border-radius: 18px;
            border: 1px solid rgba(15, 118, 110, 0.18);
            background: linear-gradient(135deg, #0f766e, #148578);
            color: white;
            font-weight: 800;
          }
          [data-testid="stImage"] img {
            border-radius: 18px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
          }
          [data-testid="stDataFrame"] {
            border-radius: 18px;
            overflow: hidden;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Configure and run the multipage Streamlit app."""
    st.set_page_config(
        page_title="VisionCaption | Prompt-Fidelity Retrieval",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_global_styles()
    navigation = st.navigation(
        [
            # All page callables are named `render`, so we provide explicit URL slugs.
            st.Page(render_overview, title="Overview", url_path="overview", default=True),
            st.Page(render_live_demo, title="Live Demo", url_path="live-demo"),
            st.Page(
                render_benchmark_explorer,
                title="Benchmark Explorer",
                url_path="benchmark-explorer",
            ),
            st.Page(
                render_architecture,
                title="Method & Architecture",
                url_path="method-architecture",
            ),
        ]
    )
    navigation.run()


if __name__ == "__main__":
    main()
