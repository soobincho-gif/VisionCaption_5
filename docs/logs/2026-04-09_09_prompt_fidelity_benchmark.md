# Prompt Fidelity Benchmark

## 1. Objective
Improve caption fidelity for screenshot- and UI-like images, then measure whether retrieval improves on a small controlled benchmark.

## 2. Why This Task Mattered
The first successful real-image retrieval run suggested that cosine ranking was already serviceable for the baseline. The larger uncertainty was whether poor captions, especially on screenshot-like images, were the main reason some retrieval results felt weak or fragile.

## 3. Plan
1. Refine the caption prompt so it explicitly preserves image type, visible text, layout structure, and distinctive retrieval cues.
2. Keep prompt design in `src/config/prompts.py` and use a clean prompt-variant hook from `VisionCaptionService`.
3. Build a small mixed benchmark with ordinary photos plus UI or dashboard screenshots.
4. Regenerate captions, embeddings, and retrieval outputs for baseline vs improved prompt variants.
5. Record both qualitative findings and small Recall@1 / Recall@3 numbers.

## 4. What Was Implemented
- Added prompt variants in `src/config/prompts.py`:
  - `baseline`
  - `retrieval_oriented_v2`
- Updated `VisionCaptionService` to accept a `prompt_variant` without mixing prompt text into pipeline logic.
- Updated `run_caption_pipeline()` so experiments can inject:
  - a custom image directory,
  - a custom caption store,
  - a prompt variant.
- Updated `run_embedding_pipeline()` so experiments can inject caption and embedding stores.
- Updated `search()` so experiments can inject caption and embedding stores cleanly.
- Added `src/pipelines/evaluate_caption_prompts.py` to run a reusable prompt comparison experiment.
- Created `data/samples/prompt_fidelity/benchmark.json` and `data/samples/prompt_fidelity/images/`.

## 5. Benchmark Setup
Benchmark name:
- `prompt_fidelity_mixed_v1`

Image mix:
- 4 user-photo images already used in the baseline.
- 4 screenshot or UI-like images:
  - `visual_storytelling_dashboard`
  - `visual_storytelling_mobile`
  - `history_chat_einstein_ai`
  - `history_chat_cleopatra_diplomacy`
- 1 text-heavy cake photo:
  - `cake_korean_message`
- 1 illustration photo:
  - `illustrated_couple_sofa`

Query setup:
- 10 handwritten queries
- 1 expected target image per query

## 6. What Changed
Key prompt changes in `retrieval_oriented_v2`:
- explicitly name the image type when visible,
- preserve main subject and surrounding context,
- preserve readable keywords or short visible text,
- describe layout structure for UI-like images,
- include distinctive cues useful for retrieval,
- avoid inventing hidden or unreadable content.

## 7. Validation
Artifacts written to:
- `outputs/eval/prompt_fidelity/baseline/`
- `outputs/eval/prompt_fidelity/retrieval_oriented_v2/`
- `outputs/eval/prompt_fidelity/comparison.json`

Quantitative result:
- baseline Recall@1 = 0.90
- baseline Recall@3 = 0.90
- improved Recall@1 = 1.00
- improved Recall@3 = 1.00

Most important qualitative change:
- `visual_storytelling_dashboard`

Baseline failure:
- The baseline caption for that screenshot was severely wrong and mixed unrelated photo scenes such as a café, outdoor standing figure, cats, and a resting person under a blanket.

Improved behavior:
- The improved caption correctly identified:
  - the interface title,
  - sentiment controls,
  - upload panel,
  - story generation section,
  - analysis and evaluation panels,
  - dark dashboard-like layout.

Retrieval effect:
- Query for the dark visual-storytelling dashboard changed from:
  - baseline top-1 = `visual_storytelling_mobile`
  - improved top-1 = `visual_storytelling_dashboard`

## 8. Remaining Issues
- Visible text capture is still imperfect for stylized or handwritten text.
- UI screens from the same product family still sit close together in similarity score.
- The benchmark is intentionally small, so conclusions are directional rather than final.

## 9. Interpretation
This experiment strengthens the claim that caption fidelity, not ranking, is the main current bottleneck. The retrieval algorithm did not change, but retrieval improved anyway once the caption preserved screen-specific details more faithfully.

## 10. Next Task
Add structured caption-side metadata for:
- image type,
- visible text,
- layout blocks,
- UI section names,

then rerun the same benchmark to see whether screenshot-like separation improves further.
