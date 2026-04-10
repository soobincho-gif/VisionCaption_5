# Structured Representation Experiment

## 1. Objective
Add structured metadata extraction to the caption pipeline and evaluate whether structured representations improve retrieval beyond free-form captions alone.

## 2. Why This Task Mattered
The prompt-fidelity experiment already showed that ranking was not the active bottleneck. The next high-value question was whether a richer representation layer could improve retrieval further by preserving image type, visible text, and layout explicitly.

## 3. Plan
1. Extend the caption schema with structured metadata fields.
2. Add deterministic `retrieval_text` built from those fields.
3. Keep free-form caption text and structured fields separate in storage.
4. Compare `caption_only`, `structured_only`, and `caption_plus_structured` on the existing benchmark.
5. Record both recall metrics and UI-family separation details.

## 4. What Was Implemented
- Extended `CaptionRecord` with:
  - `image_type`
  - `main_subject`
  - `visible_objects`
  - `visible_text`
  - `layout_blocks`
  - `distinctive_cues`
  - `retrieval_text`
- Added `CaptionContent` as a normalized service-facing schema.
- Added `src/core/representation.py` to:
  - flatten structured fields deterministically,
  - build embedding source text for multiple representation modes.
- Added representation-mode support to `run_embedding_pipeline()`.
- Added `src/pipelines/evaluate_caption_representations.py`.
- Switched structured caption extraction to SDK-backed parsed responses so JSON parsing is more reliable.

## 5. What Changed
New representation modes:
- `caption_only`
- `structured_only`
- `caption_plus_structured`

`retrieval_text` construction order:
1. `image_type`
2. `main_subject`
3. `visible_objects`
4. `visible_text`
5. `layout_blocks`
6. `distinctive_cues`

The flattened text uses stable field labels such as:
- `image type: ...`
- `main subject: ...`
- `visible objects: ...`
- `visible text: ...`
- `layout blocks: ...`
- `distinctive cues: ...`

## 6. Validation
Artifacts written to:
- `outputs/eval/structured_representation/captions.jsonl`
- `outputs/eval/structured_representation/caption_only/`
- `outputs/eval/structured_representation/structured_only/`
- `outputs/eval/structured_representation/caption_plus_structured/`
- `outputs/eval/structured_representation/comparison.json`

Important implementation note:
- The first run exposed one structured parsing failure on `history_chat_einstein_ai`.
- The service was then upgraded to use SDK-backed parsed responses.
- The final rerun completed with 10 captions and no errors.

Final benchmark result:
- `caption_only`: Recall@1 = 1.00, Recall@3 = 1.00
- `structured_only`: Recall@1 = 1.00, Recall@3 = 1.00
- `caption_plus_structured`: Recall@1 = 1.00, Recall@3 = 1.00

UI-family top-1 margin:
- `caption_only`: 0.1358 average
- `structured_only`: 0.1134 average
- `caption_plus_structured`: 0.1325 average

## 7. Remaining Issues
- The benchmark is now saturated and too easy for choosing a default representation.
- `retrieval_text` may be too exhaustive, especially when concatenated with an already-strong caption.
- Handwritten or stylized text is still not perfectly preserved.

## 8. Next Task
Add harder sibling-screen queries and compare more selective `retrieval_text` variants before promoting structured representation to the default baseline.
