# Now

## Current task
Prepare the next representation-fidelity pass for the remaining control/candidate failures.

## Why this matters now
The fixed control/candidate rerun confirmed that `caption_plus_selected_structured` improves the hard benchmark without changing ranking logic:
- `caption_only`: Recall@1 = 0.6786, Recall@3 = 1.0000, hard-negative confusions = 9
- `caption_plus_selected_structured`: Recall@1 = 0.7500, Recall@3 = 1.0000, hard-negative confusions = 7

The remaining candidate misses are concentrated in:
- person-name confusion = 5
- visible-text confusion = 2

## Related files
- `data/samples/prompt_fidelity/benchmark.json`
- `outputs/eval/control_candidate_baseline/comparison.json`
- `outputs/eval/control_candidate_baseline/caption_only/results.json`
- `outputs/eval/control_candidate_baseline/caption_plus_selected_structured/results.json`
- `outputs/eval/structured_representation/captions.jsonl`
- `src/pipelines/evaluate_caption_representations.py`
- `src/core/representation.py`
- `docs/04_experiment_log.md`
- `docs/05_report_context.md`

## Success condition
- The next representation change targets person names, exact visible UI text, and UI state fidelity.
- The fixed control/candidate comparison can be rerun without changing the dataset or ranking logic.
- Reranking remains a deferred decision unless representation improves and top-3 still rescues frequent top-1 misses.

## Known blockers
- The hard benchmark is still small and hand-curated.
- The correct image is already in top-3 for all remaining candidate top-1 misses, so future work must distinguish representation errors from rank-ordering errors carefully.
- Some failures may require better OCR-like extraction or query/record text normalization rather than more fields.

## Immediate next move
Inspect the remaining candidate failures, then improve representation fidelity for person-name and visible-text cases before considering lightweight reranking.
