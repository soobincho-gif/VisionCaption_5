# Mixed Sanity Validation For Frozen Best Config

Note:
This log captures the first rebuild-based mixed-sanity validation pass. It is historical, not the final promotion record.
The promoted-default decision and the offline-safe frozen-replay validation were recorded later in:
- `docs/logs/2026-04-10_06_default_promotion_offline_repro.md`

## 1. Objective
Package the current best hard-benchmark configuration as a named frozen setting and validate it on a broader mixed sanity set instead of tuning the hard benchmark further.

## 2. Why This Task Mattered
The hard benchmark had already reached a perfect result with:
- `caption_plus_selected_structured`
- deterministic top-3 rerank
- `question_paraphrase_overlap = 0.25`

That result was strong but still too narrow to justify making the full stack the broader default. The next step needed to answer a validation question, not a tuning question: does the current winner stay strong once the query mix includes easier UI screens plus ordinary photo and illustration retrieval?

## 3. Plan
1. Freeze the hard-benchmark winner as a named experiment setting.
2. Build a broader mixed sanity benchmark over the same fixed 12-image pool.
3. Run:
   - `caption_only`
   - `caption_plus_selected_structured`
   - `caption_plus_selected_structured + deterministic rerank + question_paraphrase_overlap=0.25`
4. Add one attribution-only rerank comparison with `question_paraphrase_overlap=0.0` so the paraphrase cue can be evaluated separately without new tuning.
5. Write a compact ablation table and update the report-facing context.

## 4. What Was Implemented
- Added `src/config/experiment_settings.py` with frozen setting:
  - `hard_best_caption_plus_selected_structured_top3_qpo025_v1`
- Added broader mixed sanity benchmark:
  - `data/samples/prompt_fidelity/benchmark_mixed_sanity_v1.json`
- Added orchestration/report pipeline:
  - `src/pipelines/evaluate_mixed_sanity.py`
- Added regression tests for:
  - experiment-setting resolution,
  - mixed-sanity helper logic,
  - broader-benchmark compatibility in the rerank ablation.

## 5. What Changed
The mixed sanity benchmark uses the same 12 benchmark images but broadens the query mix to 40 queries:
- 16 `hard_ui`
- 12 `normal_ui`
- 12 `photo_or_illustration`

All outputs for this packaged run were written under one experiment namespace:
- `outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/mixed_sanity_v1/`

Main artifacts:
- `outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/mixed_sanity_v1/report.json`
- `outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/mixed_sanity_v1/ablation_table.md`
- `outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/mixed_sanity_v1/control_candidate/`
- `outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/mixed_sanity_v1/candidate_rerank_no_paraphrase/`
- `outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/mixed_sanity_v1/candidate_rerank_with_paraphrase/`

## 6. Validation
Tests:

```bash
python -m pytest tests/test_evaluate_mixed_sanity.py tests/test_evaluate_top3_rerank_ablation.py tests/test_experiment_settings.py tests/test_rerank.py tests/test_evaluate_caption_representations.py tests/test_representation.py
```

Compile:

```bash
python -m compileall src
```

Mixed sanity run:

```bash
python -m src.pipelines.evaluate_mixed_sanity \
  --benchmark-path data/samples/prompt_fidelity/benchmark_mixed_sanity_v1.json \
  --caption-path outputs/eval/structured_representation/captions.jsonl \
  --output-dir outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/mixed_sanity_v1 \
  --experiment-setting-name hard_best_caption_plus_selected_structured_top3_qpo025_v1
```

Results:
- `caption_only`: Recall@1 = 0.6750, Recall@3 = 1.0000
- `caption_plus_selected_structured`: Recall@1 = 0.8750, Recall@3 = 1.0000
- `caption_plus_selected_structured + deterministic_top3_rerank`: Recall@1 = 0.9500, Recall@3 = 1.0000
- `caption_plus_selected_structured + deterministic_top3_rerank + question_paraphrase_overlap=0.25`: Recall@1 = 0.9750, Recall@3 = 1.0000

Slice view:
- `hard_ui`
  - `caption_only`: 0.6250
  - `caption_plus_selected_structured`: 0.7500
  - rerank without paraphrase: 0.9375
  - best config: 1.0000
- `normal_ui`
  - `caption_only`: 0.4167
  - `caption_plus_selected_structured`: 0.9167
  - rerank without paraphrase: 0.9167
  - best config: 0.9167
- `photo_or_illustration`
  - all three non-control systems stayed at 1.0000 Recall@1
  - `caption_only` was also already at 1.0000 on this slice

Paraphrase-overlap attribution:
- helped:
  - `mq010_einstein_discovery_paraphrase`
- hurt:
  - none

Notable regressions:
- `caption_plus_selected_structured` vs `caption_only`:
  - `mq001_dashboard_dark_panels`
  - `mq009_einstein_reflective_opinion`
  - `mq010_einstein_discovery_paraphrase`
  - `mq017_dashboard_basic_dark_storytelling`
- full rerank stack vs `caption_plus_selected_structured`:
  - `mq028_cleopatra_diplomacy_answer`

Why the remaining rerank regression matters:
- The underlying candidate already retrieved `history_chat_cleopatra_diplomacy` correctly at rank 1.
- The deterministic reranker flipped it to `history_chat_cleopatra_landing`.
- The flip was driven by shared high-level cues such as `leadership`, `power`, `diplomacy`, plus transcript/input-area component overlap.

## 7. Remaining Issues
- The paraphrase-overlap cue looked safe on this broader set, but the deterministic rerank stack still regressed one normal UI query:
  - `mq028_cleopatra_diplomacy_answer`
- That means the full best hard-benchmark stack is stronger on hard UI cases, but it is not yet broad-default-safe.

## 8. Next Task
Keep the full best configuration optional for now.

If a future pass is approved, focus only on regression analysis for the Cleopatra landing-vs-transcript failure inside the deterministic reranker. Do not retune the hard benchmark itself.
