# Control/Candidate Baseline Fixation

## Objective
Make the control/candidate retrieval experiment repeatable by rerunning `caption_only` and `caption_plus_selected_structured` on the same hard benchmark and fixed caption store.

## Why This Task Mattered
The previous CLI work made both representations indexable, but only one query had been spot-checked outside the broader evaluation run. The project needed a dedicated artifact proving that the control and candidate can be regenerated side by side through retrieval.

## Plan
1. Add a control/candidate comparison scope to the representation evaluation pipeline.
2. Reuse a fixed caption store so the comparison changes only the embedded representation.
3. Regenerate both embedding files and retrieval results.
4. Collapse failures into the five report-facing buckets.
5. Record the rerank decision as a judgment, not an implementation.

## What Was Implemented
- Added a CLI entrypoint to `src/pipelines/evaluate_caption_representations.py`.
- Added `control_candidate` mode with:
  - `caption_only`
  - `caption_plus_selected_structured`
- Added `--caption-path` and `--reuse-captions` support.
- Added fixed failure buckets:
  - same-family UI confusion
  - person-name confusion
  - visible-text confusion
  - OCR/stylized text failure
  - layout confusion
- Added `rerank_judgment` output for each mode.
- Added regression tests for failure buckets and rerank judgment.

## Validation
Command:

```bash
python -m src.pipelines.evaluate_caption_representations \
  --comparison-scope control_candidate \
  --caption-path outputs/eval/structured_representation/captions.jsonl \
  --reuse-captions \
  --experiment-dir outputs/eval/control_candidate_baseline \
  --top-k 3
```

Test command:

```bash
python -m pytest
```

Test result:
- 7 passed.

## Results
Outputs:
- `outputs/eval/control_candidate_baseline/comparison.json`
- `outputs/eval/control_candidate_baseline/caption_only/embeddings.jsonl`
- `outputs/eval/control_candidate_baseline/caption_only/results.json`
- `outputs/eval/control_candidate_baseline/caption_plus_selected_structured/embeddings.jsonl`
- `outputs/eval/control_candidate_baseline/caption_plus_selected_structured/results.json`

Metrics:
- `caption_only`: Recall@1 = 0.6786, Recall@3 = 1.0000, hard-negative confusions = 9.
- `caption_plus_selected_structured`: Recall@1 = 0.7500, Recall@3 = 1.0000, hard-negative confusions = 7.
- Candidate delta: Recall@1 +0.0714, family Recall@1 +0.1053, hard-negative confusions -2.

Candidate failure buckets:
- same-family UI confusion = 0
- person-name confusion = 5
- visible-text confusion = 2
- OCR/stylized text failure = 0
- layout confusion = 0

## Interpretation
The candidate baseline is now reproducible as a full retrieval experiment. Because the ranking logic stayed unchanged, the candidate improvement should be reported as evidence that selected structured representation improves hard-case separation.

The remaining bottleneck still looks closer to representation fidelity than pure ranking. The top-3 signal suggests a lightweight reranker may be useful later, but implementation should wait until after another representation-fidelity pass.

## Next Task
Improve the representation of person names, exact visible UI text, and UI state. Rerun this fixed comparison afterward; only then decide whether lightweight reranking is justified.
