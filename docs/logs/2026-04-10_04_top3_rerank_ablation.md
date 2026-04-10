# Deterministic Top-3 Rerank Ablation

## 1. Objective
Test whether the remaining hard-benchmark errors are primarily top-1 ordering problems by reranking only the frozen candidate top-3 results with a lightweight deterministic scorer.

## 2. Why This Task Mattered
After the representation-fidelity pass, the candidate had only four remaining misses and all four already contained the correct image in the top-3. That made reranking the next clean ablation: if a tiny deterministic reranker could fix most of the misses without regressions, the residual ceiling would look more like ordering than representation.

## 3. Plan
1. Keep `caption_only` unchanged as the control reference.
2. Keep the current `caption_plus_selected_structured` candidate frozen.
3. Rerank only the existing top-3 candidate outputs.
4. Use explicit features and weights:
   - exact visible-text overlap
   - named-entity match
   - label-value phrase overlap
   - component cue overlap
   - small original-similarity tie-break
5. Write a separate ablation output directory and log per-query feature contributions.

## 4. What Was Implemented
- Added deterministic rerank logic in `src/core/rerank.py`.
- Added a dedicated ablation pipeline in `src/pipelines/evaluate_top3_rerank_ablation.py`.
- Added regression tests in `tests/test_rerank.py`.
- Kept rerank weights explicit and small:
  - `exact_visible_text_overlap = 1.2`
  - `named_entity_match = 1.5`
  - `label_value_phrase_overlap = 2.0`
  - `component_cue_overlap = 1.3`
  - `original_similarity = 0.25`
- Added query-level activation gating so reranking only applies when at least one supported rerank signal is present:
  - label-value phrase overlap
  - component cue overlap
  - strong exact visible-text overlap
- Preserved the original frozen candidate outputs and wrote all rerank artifacts under a new directory.

## 5. What Changed
This pass did not regenerate captions or embeddings and did not modify the frozen candidate representation. It only reordered the existing top-3 results when the query exposed a clear deterministic rerank signal.

The reranker logs, for every query:
- whether reranking activated,
- which features activated it,
- per-candidate raw feature scores,
- matched terms or phrases,
- weighted contributions,
- final reranked rank.

## 6. Validation
Tests:

```bash
python -m pytest tests/test_rerank.py tests/test_evaluate_caption_representations.py tests/test_representation.py
```

Compile:

```bash
python -m compileall src
```

Ablation run:

```bash
python -m src.pipelines.evaluate_top3_rerank_ablation \
  --caption-path outputs/eval/structured_representation/captions.jsonl \
  --source-candidate-results-path outputs/eval/control_candidate_name_text_fidelity/caption_plus_selected_structured/results.json \
  --source-control-results-path outputs/eval/control_candidate_name_text_fidelity/caption_only/results.json \
  --output-dir outputs/eval/deterministic_top3_rerank_ablation
```

Outputs:
- `outputs/eval/deterministic_top3_rerank_ablation/comparison.json`
- `outputs/eval/deterministic_top3_rerank_ablation/results.json`
- `outputs/eval/deterministic_top3_rerank_ablation/query_logs.jsonl`

## 7. Results
Control reference:
- `caption_only`: Recall@1 = 0.6786, Recall@3 = 1.0000, hard-negative confusions = 9

Frozen candidate before rerank:
- Recall@1 = 0.8571
- Recall@3 = 1.0000
- hard-negative confusions = 4
- failure buckets:
  - person-name confusion = 2
  - visible-text confusion = 2

Candidate after deterministic top-3 rerank:
- Recall@1 = 0.9643
- Recall@3 = 1.0000
- hard-negative confusions = 1
- failure buckets:
  - same-family UI confusion = 0
  - person-name confusion = 1
  - visible-text confusion = 0
  - OCR/stylized text failure = 0
  - layout confusion = 0

Delta versus the frozen candidate:
- Recall@1: +0.1071
- Recall@3: no change
- hard-negative confusions: -3

Corrected queries:
- `q010_dashboard_dark_panels`
- `q012_dashboard_slider_file_sizes`
- `q020_einstein_reflective_opinion`

Still unresolved:
- `q021_einstein_discovery_paraphrase`

Regressions:
- none

## 8. Feature Attribution
Compact failure analysis:
- corrected by visible-text overlap = 0
- corrected by label-value phrase overlap = 2
- corrected by entity cue overlap = 0
- corrected by component cue overlap = 1
- still unresolved = 1

Per-query outcomes for the four residual misses:
- `q010_dashboard_dark_panels`
  - before top-1: `visual_storytelling_mobile`
  - after top-1: `visual_storytelling_dashboard`
  - primary driver: `label_value_phrase_overlap`
  - decisive matched phrase: `pipeline refinement status`
- `q012_dashboard_slider_file_sizes`
  - before top-1: `visual_storytelling_mobile`
  - after top-1: `visual_storytelling_dashboard`
  - primary driver: `component_cue_overlap`
  - decisive matched cues included `max sentences slider`
- `q020_einstein_reflective_opinion`
  - before top-1: `history_chat_einstein_ai`
  - after top-1: `history_chat_einstein_philosophical`
  - primary driver: `label_value_phrase_overlap`
  - decisive matched phrases:
    - `question type philosophical`
    - `answer mode reflective opinion`
- `q021_einstein_discovery_paraphrase`
  - rerank did not activate
  - no supported deterministic signal separated the top-3

## 9. Interpretation
The residual errors are mostly ranking-driven rather than broad-representation failures:
- 3 of the 4 remaining misses were corrected by reranking the frozen top-3 only,
- no regressions were introduced on the current hard benchmark,
- the remaining unresolved miss is a paraphrase case that does not expose a strong exact-text, label-value, or component signal.

This means the benchmark now supports a nuanced claim:
- representation work was necessary to reach the current candidate,
- but the remaining ceiling is largely a top-1 ordering problem among already-retrieved candidates.

## 10. Decision
Keep the deterministic reranker as an optional ablation or feature flag for now. Do not make it the default retrieval path yet, because:
- the rule set is tuned to the current benchmark failure shape,
- one miss still remains unresolved,
- broader validation is still needed.

## 11. Next Task
Either:
1. validate the deterministic reranker on a broader sanity set and consider promoting it to the default top-1 refinement step, or
2. run one more representation pass focused on the unresolved Einstein paraphrase miss before deciding on a default rerank policy.
