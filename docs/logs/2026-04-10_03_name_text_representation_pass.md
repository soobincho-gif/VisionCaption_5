# Name/Text Representation Fidelity Pass

## 1. Objective
Improve the candidate representation for the remaining hard-benchmark failure modes, focusing only on person-name confusion and visible-text confusion.

## 2. Why This Task Mattered
The fixed control/candidate benchmark had already shown that `caption_plus_selected_structured` was the best current representation, but its remaining misses were concentrated in a small number of historical-figure and text-sensitive UI cases. The next pass needed to improve representation fidelity without touching ranking logic, benchmark labels, or the caption store.

## 3. Plan
1. Inspect the 7 remaining candidate failures and their top-k outputs.
2. Identify which candidate fields were missing or too weak.
3. Revise only the candidate representation-building layer.
4. Rebuild candidate embeddings and rerun the fixed control/candidate benchmark.
5. Record updated metrics, failure buckets, and before/after examples.

## 4. What Was Implemented
- Kept `caption_only` unchanged as the control.
- Revised `caption_plus_selected_structured` in `src/core/representation.py` only.
- Added candidate-only `component cue:` lines from `visible_objects` for interface-like records.
- Added candidate-only `named entity cue:` lines from `caption_text` and `main_subject`, with lightweight aliases:
  - `Albert Einstein` -> `Einstein`
  - `Cleopatra VII Philopator` -> `Cleopatra VII`, `Cleopatra`
- Added candidate-only `exact text cue:` lines from `visible_text`.
- Added splitting logic for overlong OCR-like `visible_text` items so short headers and question strings survive as separate retrieval anchors.
- Added regression coverage in `tests/test_representation.py` for:
  - component cue inclusion,
  - named entity extraction,
  - long visible-text splitting.

## 5. What Changed
The candidate representation is still built from the same stored caption record, but it now makes the following weak points explicit:
- interface components that had been missing from the selected-field candidate,
- historical figure names and aliases,
- exact or near-exact visible text recovered from collapsed long text blocks.

This kept the change minimal and auditable:
- no reranker,
- no benchmark label edits,
- no architecture refactor,
- no caption regeneration.

## 6. Validation
Unit tests:

```bash
python -m pytest tests/test_representation.py tests/test_evaluate_caption_representations.py
```

Compile check:

```bash
python -m compileall src
```

Evaluation command:

```bash
python -m src.pipelines.evaluate_caption_representations \
  --comparison-scope control_candidate \
  --caption-path outputs/eval/structured_representation/captions.jsonl \
  --reuse-captions \
  --experiment-dir outputs/eval/control_candidate_name_text_fidelity \
  --top-k 3
```

Outputs:
- `outputs/eval/control_candidate_name_text_fidelity/comparison.json`
- `outputs/eval/control_candidate_name_text_fidelity/caption_only/results.json`
- `outputs/eval/control_candidate_name_text_fidelity/caption_plus_selected_structured/results.json`
- `outputs/eval/control_candidate_name_text_fidelity/caption_only/embeddings.jsonl`
- `outputs/eval/control_candidate_name_text_fidelity/caption_plus_selected_structured/embeddings.jsonl`

## 7. Results
Control:
- `caption_only`: Recall@1 = 0.6786, Recall@3 = 1.0000, hard-negative confusions = 9

Candidate before this pass:
- `caption_plus_selected_structured`: Recall@1 = 0.7500, Recall@3 = 1.0000, hard-negative confusions = 7
- failure buckets:
  - person-name confusion = 5
  - visible-text confusion = 2

Candidate after this pass:
- `caption_plus_selected_structured`: Recall@1 = 0.8571, Recall@3 = 1.0000, hard-negative confusions = 4
- family-confusion Recall@1 = 0.7895
- failure buckets:
  - same-family UI confusion = 0
  - person-name confusion = 2
  - visible-text confusion = 2
  - OCR/stylized text failure = 0
  - layout confusion = 0

Candidate delta versus the previous fixed-caption run:
- Recall@1: +0.1071
- hard-negative confusions: -3
- person-name confusion: -3
- visible-text confusion: no change

Recovered queries:
- `q016_einstein_ai_today`
- `q017_einstein_posthumous_current_events`
- `q018_einstein_ai_question_text`
- `q022_cleopatra_landing_empty_transcript`

New regression:
- `q020_einstein_reflective_opinion`

Remaining misses:
- `q010_dashboard_dark_panels`
- `q012_dashboard_slider_file_sizes`
- `q020_einstein_reflective_opinion`
- `q021_einstein_discovery_paraphrase`

## 8. Before/After Examples
Improved person-name case: `q017_einstein_posthumous_current_events`
- Before:
  - rank 1 `history_chat_einstein_philosophical` (0.588619)
  - rank 2 `history_chat_einstein_ai` (0.581342)
- After:
  - rank 1 `history_chat_einstein_ai` (0.553150)
  - rank 2 `history_chat_einstein_philosophical` (0.531970)
- Helpful new cues on the correct candidate:
  - `named entity cue: Albert Einstein`
  - `exact text cue: "What do you think about AI today?"`
  - `exact text cue: "posthumous current events"`
  - `exact text cue: "cautious historical projection"`

Improved person-name case: `q022_cleopatra_landing_empty_transcript`
- Before:
  - rank 1 `history_chat_cleopatra_diplomacy` (0.628486)
  - rank 2 `history_chat_cleopatra_landing` (0.623127)
- After:
  - rank 1 `history_chat_cleopatra_landing` (0.596849)
  - rank 2 `history_chat_cleopatra_diplomacy` (0.585194)
- Helpful new cues on the correct candidate:
  - `named entity cue: Cleopatra VII Philopator`
  - `named entity cue: Cleopatra VII`
  - `component cue: pipeline snapshot box`
  - `exact text cue: "Converse with a historical mind, not a costume."`

Unchanged visible-text case: `q012_dashboard_slider_file_sizes`
- Before:
  - rank 1 `visual_storytelling_mobile` (0.688406)
  - rank 2 `visual_storytelling_dashboard` (0.645572)
- After:
  - rank 1 `visual_storytelling_mobile` (0.692531)
  - rank 2 `visual_storytelling_dashboard` (0.674317)
- The representation gained useful dashboard cues such as `component cue: max sentences slider` and `component cue: scene observations panel`, but the mobile sibling still dominates the exact shared labels.

## 9. Remaining Issues
- The dashboard visible-text pair (`q010`, `q012`) still misses top-1.
- The Einstein philosophical screen still needs better label-value extraction for text like:
  - `question type philosophical`
  - `answer mode reflective opinion`
- All remaining candidate misses still have the expected image inside top-3.

## 10. Next Task
Run one more narrow representation pass for label-value text extraction on the remaining dashboard and Einstein philosophical screens, or explicitly test a lightweight reranker now that the remaining misses are all top-3 rescues.
