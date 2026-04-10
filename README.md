# VisionCaption

Prompt-fidelity image retrieval for UI screenshots, historical chat interfaces, and mixed visual queries.

## Live Links

- Live app: [visioncaption5.streamlit.app](https://visioncaption5.streamlit.app)
- GitHub: [soobincho-gif/VisionCaption_5](https://github.com/soobincho-gif/VisionCaption_5)

## Overview

VisionCaption is a Streamlit portfolio app for an explainable text-to-image retrieval system. Instead of rebuilding embeddings during demos, it replays trusted frozen evaluation artifacts so the default experience stays deterministic, reproducible, and deployment-friendly.

The project focuses on prompts that are usually awkward for generic caption retrieval:

- UI-heavy screenshots
- historical chat-style interfaces
- mixed prompts that combine visible text, entities, and layout cues

## What The App Shows

- `Overview`: the retrieval story, promoted default, and headline metrics
- `Live Demo`: frozen replay for benchmark queries, plus optional session-only image upload
- `Benchmark Explorer`: query-level and slice-level benchmark inspection
- `Method / Architecture`: representation, reranking, and artifact pipeline summary

## Retrieval Stack

The current promoted path has three stages:

1. `baseline`: caption-only retrieval
2. `candidate`: caption plus selected structured fields
3. `final default`: deterministic top-3 rerank with `question_paraphrase_overlap = 0.25`

This makes the system more faithful to UI wording and visible on-screen cues without hiding the evidence trail.

## Current Validated Default

Validated from the trusted frozen mixed-sanity replay on April 10, 2026:

- representation mode: `caption_plus_selected_structured`
- rerank: deterministic top-3 rerank
- `question_paraphrase_overlap = 0.25`
- singleton low-signal container guard: enabled
- mixed-sanity replay result: `Recall@1 = 1.0000`, `Recall@3 = 1.0000`, regressions `= 0`

Validation caveat:

- the promoted default is evidence-backed from frozen artifact replay
- a full end-to-end rebuild is still pending because a prior network error interrupted embedding rebuild

## Local Run

Install dependencies and start the app:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Entrypoint:

```text
app.py
```

## Secrets

Frozen replay mode does not require secrets.

`OPENAI_API_KEY` is only needed for features that generate new model output at runtime, such as:

- upload captioning
- temporary upload embeddings
- free-text query embedding outside frozen replay

For local testing, create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "sk-your-openai-key"
```

Do not commit `.streamlit/secrets.toml`. The repository ignores it by default. See [.streamlit/secrets.toml.example](./.streamlit/secrets.toml.example).

## Deployment

This repository is set up for Streamlit Community Cloud.

- repository: `soobincho-gif/VisionCaption_5`
- branch: `main`
- main file path: `app.py`
- recommended Python: `3.12`
- dependency file: `requirements.txt`

The deployed app currently lives at [visioncaption5.streamlit.app](https://visioncaption5.streamlit.app).

## Repo Layout

```text
app.py
src/
  services/
  storage/
  pipelines/
  core/
  config/
ui/
  pages/
  components/
  utils/
data/
outputs/
.streamlit/
requirements.txt
```
