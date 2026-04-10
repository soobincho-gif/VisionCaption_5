# Hard Benchmark Representation

## 1. Objective
Build a harder retrieval benchmark that can separate representation quality across caption-only and structured representations.

## 2. Why This Task Mattered
The previous benchmark was saturated. All tested representation modes achieved perfect recall, so it could not answer whether structured metadata actually improved retrieval. A harder benchmark was needed before changing the baseline representation.

## 3. Plan
1. Add same-family UI sibling images.
2. Expand query types to cover visible text, layout structure, paraphrases, partial cues, and hard negatives.
3. Add query-level tags for tag-specific evaluation.
4. Compare four representation modes.
5. Add metrics beyond Recall@1 and Recall@3.

## 4. What Was Implemented
- Added two historical-salon UI images:
  - `history_chat_cleopatra_landing`
  - `history_chat_einstein_philosophical`
- Expanded `data/samples/prompt_fidelity/benchmark.json` to `prompt_fidelity_mixed_v2_hard`.
- Added 28 tagged queries.
- Added hard-negative image IDs for same-family UI disambiguation queries.
- Added representation modes:
  - `caption_only`
  - `structured_all_fields`
  - `structured_selected_fields`
  - `caption_plus_selected_structured`
- Added metrics:
  - mean top-1 margin,
  - tag-specific accuracy,
  - family-confusion accuracy,
  - qualitative error buckets.

## 5. Query Tag Taxonomy
- `ui_family_disambiguation`
- `visible_text`
- `layout_structure`
- `person_name`
- `paraphrase`
- `photo_scene`
- `illustration_style`
- `partial_cue`
- `hard_negative`

## 6. Validation
Final clean run:
- benchmark = `prompt_fidelity_mixed_v2_hard`
- images = 12
- queries = 28
- captions written = 12
- caption errors = 0

Artifacts:
- `outputs/eval/structured_representation/captions.jsonl`
- `outputs/eval/structured_representation/comparison.json`
- `outputs/eval/structured_representation/caption_only/`
- `outputs/eval/structured_representation/structured_all_fields/`
- `outputs/eval/structured_representation/structured_selected_fields/`
- `outputs/eval/structured_representation/caption_plus_selected_structured/`

## 7. Results
Overall:
- `caption_only`: Recall@1 = 0.6786, Recall@3 = 1.0000
- `structured_all_fields`: Recall@1 = 0.6786, Recall@3 = 1.0000
- `structured_selected_fields`: Recall@1 = 0.7143, Recall@3 = 1.0000
- `caption_plus_selected_structured`: Recall@1 = 0.7500, Recall@3 = 1.0000

Family-confusion Recall@1:
- `caption_only`: 0.5263
- `structured_all_fields`: 0.5263
- `structured_selected_fields`: 0.5789
- `caption_plus_selected_structured`: 0.6316

Hard-negative confusions:
- `caption_only`: 9
- `structured_all_fields`: 9
- `structured_selected_fields`: 8
- `caption_plus_selected_structured`: 7

## 8. Interpretation
The harder benchmark successfully separated representation quality. Selected structured fields outperform caption-only on hard cases, and the mixed representation is strongest overall.

The improvement is not perfect:
- Recall@3 is still saturated at 1.0000.
- Mean top-1 margin does not clearly improve.
- Remaining errors are mostly same-family visible-text and person-name confusions.

## 9. Decision
Treat `caption_plus_selected_structured` as the candidate baseline for the next stage, while keeping `caption_only` as the control.

## 10. Next Task
Expose `representation_mode` through the CLI/config, regenerate embeddings with `caption_plus_selected_structured`, and rerun the hard benchmark plus a broader real-photo sanity set before making it permanent.
