# VisionCaption Portfolio UI

VisionCaption is an explainable image-retrieval project that compares three retrieval stages over frozen benchmark artifacts:

- `baseline`: caption-only retrieval
- `candidate`: caption + selected structured fields
- `final default`: deterministic top-3 rerank with `question_paraphrase_overlap = 0.25`

The Streamlit app in this repo is built for portfolio demos and Streamlit Community Cloud deployment. It replays validated frozen artifacts instead of rebuilding embeddings during UI interactions, so the demo remains deterministic and offline-safe.

## Pages

- `Overview`
- `Live Demo`
- `Benchmark Explorer`
- `Method / Architecture`

## Local Run

Install dependencies, then run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app entrypoint is:

```text
app.py
```

## Deployment Notes

- Streamlit Community Cloud entrypoint: `app.py`
- The UI expects the frozen artifacts already committed in `outputs/eval/`
- Demo interactions do not require a network embedding rebuild
- `.streamlit/config.toml` includes the app theme and server defaults
- `.streamlit/secrets.toml` is optional for this portfolio UI because the app does not call the embedding API during replay mode

## Current Validated Default Configuration

Validated on April 10, 2026 from the trusted frozen mixed-sanity replay:

- representation mode: `caption_plus_selected_structured`
- rerank: deterministic top-3 rerank
- `question_paraphrase_overlap = 0.25`
- singleton low-signal container guard: enabled
- mixed-sanity replay result: `Recall@1 = 1.0000`, `Recall@3 = 1.0000`, regressions `= 0`

Validation caveat:

- the broader default is evidence-backed from frozen artifact replay
- a full end-to-end rebuild is still pending because a network connection error interrupted embedding rebuild

## Repo Structure

```text
app.py
ui/
  pages/
  components/
  utils/
.streamlit/
  config.toml
requirements.txt
```

## Streamlit Community Cloud Setup

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, create a new app from the repo.
3. Set the main file path to `app.py`.
4. Deploy without enabling any live rebuild path.

The portfolio app will boot directly from the checked-in frozen artifacts.
