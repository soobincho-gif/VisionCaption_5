# Default Promotion And Offline Reproducibility

## 1. Objective
Promote the validated broader default for the evaluation pipeline and make mixed-sanity validation reproducible without network dependence.

## 2. Final Default
- representation: `caption_plus_selected_structured`
- rerank: deterministic top-3 rerank
- `question_paraphrase_overlap = 0.25`
- singleton low-signal container guard enabled

## 3. What Changed
- Added promotion metadata to `src/config/experiment_settings.py`.
- Added offline-safe mixed-sanity replay support in `src/pipelines/evaluate_mixed_sanity.py`.
- Added frozen-embedding reuse and fail-fast empty-result guards in `src/pipelines/evaluate_caption_representations.py` and `src/pipelines/build_embedding_index.py`.
- Added a compact summary artifact:
  - `default_promotion_summary.json`
  - `default_promotion_summary.md`

## 4. Validation Split
Frozen-artifact replay validation:
- source control/candidate artifacts:
  - `outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/mixed_sanity_v1/control_candidate/`
- result:
  - broader default Recall@1 = 1.0000
  - Recall@3 = 1.0000
  - regressions = 0

End-to-end rebuild status:
- not completed
- embedding rebuild hit a network Connection error
- malformed all-zero rebuild artifacts are invalid and should not be cited

## 5. Report Caveat
The promotion decision is evidence-backed, but the evidence source matters:
- use the trusted frozen replay for validation claims
- keep the blocked rebuild as an operational caveat, not as contradictory retrieval evidence
