# Just Finished

## Completed task
- Added a dedicated control/candidate comparison path for `caption_only` versus `caption_plus_selected_structured`.
- Reused the fixed hard-benchmark caption store so both modes compare the same caption data.
- Regenerated embeddings and retrieval results for both modes under `outputs/eval/control_candidate_baseline/`.
- Collapsed qualitative failures into the five requested buckets:
  - same-family UI confusion
  - person-name confusion
  - visible-text confusion
  - OCR/stylized text failure
  - layout confusion
- Added a rerank judgment summary that records the top-3 rescue signal while keeping reranking unimplemented.
- Strengthened `docs/05_report_context.md` with the report-facing conclusion.

## Files changed
- `src/pipelines/evaluate_caption_representations.py`
- `tests/test_evaluate_caption_representations.py`
- `outputs/eval/control_candidate_baseline/comparison.json`
- `outputs/eval/control_candidate_baseline/caption_only/embeddings.jsonl`
- `outputs/eval/control_candidate_baseline/caption_only/results.json`
- `outputs/eval/control_candidate_baseline/caption_plus_selected_structured/embeddings.jsonl`
- `outputs/eval/control_candidate_baseline/caption_plus_selected_structured/results.json`
- `docs/04_experiment_log.md`
- `docs/05_report_context.md`
- `docs/logs/2026-04-10_02_control_candidate_baseline.md`
- `docs/logs/README.md`
- `docs/status/now.md`
- `docs/status/just_finished.md`
- `docs/status/next_up.md`
- `docs/06_handoff.md`
- `docs/03_design_decisions.md`

## Key result
Control/candidate rerun on `prompt_fidelity_mixed_v2_hard`:
- `caption_only`: Recall@1 = 0.6786, Recall@3 = 1.0000, hard-negative confusions = 9
- `caption_plus_selected_structured`: Recall@1 = 0.7500, Recall@3 = 1.0000, hard-negative confusions = 7
- Candidate delta: Recall@1 +0.0714, family Recall@1 +0.1053, hard-negative confusions -2

Candidate failure buckets:
- same-family UI confusion = 0
- person-name confusion = 5
- visible-text confusion = 2
- OCR/stylized text failure = 0
- layout confusion = 0

Test result:
- `python -m pytest`: 7 passed

## Remaining risk
- The candidate improves hard-case separation, but top-1 is still unstable for person-name and visible-text queries.
- All remaining candidate misses are top-3 recoverable, which is a rerank signal, but the current decision is to improve representation fidelity before implementing a reranker.
- The benchmark is curated and should still be broadened after the immediate representation-fidelity pass.

## Connected next task
Improve representation fidelity for person names, exact visible UI text, and UI state; then rerun the fixed control/candidate comparison.
