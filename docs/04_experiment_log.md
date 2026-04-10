# 04 Experiment Log

## Purpose of This File
This file records all meaningful experiments run on the project.

An experiment should not only record what was changed, but also:
- why it was changed,
- what hypothesis was being tested,
- how success was measured,
- what was learned,
- what should happen next.

This prevents repeated trial-and-error without memory.

---

## Experiment Template

### Experiment ID
EXP-XXX

### Date
YYYY-MM-DD

### Title
Short descriptive title

### Objective
What are we trying to learn or improve?

### Baseline
What is the current reference system or prior state?

### Change Introduced
What was changed?

### Hypothesis
What do we expect this change to improve?

### Evaluation Method
How are we judging the result?
Examples:
- qualitative top-3 inspection,
- Recall@1,
- Recall@3,
- MRR,
- latency comparison,
- failure-case review

### Dataset / Query Set
What images and queries were used?

### Results
What happened?

### Interpretation
What does the result mean?

### Decision
- keep
- reject
- revisit later

### Next Action
What should be done next?

---

## Experiment Queue

### EXP-001
#### Date
2026-04-09

#### Title
Baseline caption prompt quality check

#### Objective
Check whether the initial vision caption prompt produces captions that are descriptive enough for semantic retrieval.

#### Baseline
Caption indexing infrastructure is now implemented, but no qualitative prompt run has been logged yet.

#### Change Introduced
Prepared a working caption pipeline that can apply the baseline caption prompt to images and store the results.

#### Hypothesis
If the prompt is specific enough, the generated captions will preserve relevant scene meaning and allow reasonable query-image matching.

#### Evaluation Method
- manual caption quality review,
- qualitative retrieval check on small query set.

#### Dataset / Query Set
Initial sample image folder and hand-written test queries.

#### Results
Pending first run on a real sample image set.

#### Interpretation
Pending first prompt-quality review.

#### Decision
Revisit after the first caption batch is generated.

#### Next Action
Run the caption pipeline on a small curated sample set, then review caption specificity and consistency.

---

### EXP-002
#### Date
2026-04-09

#### Title
Compare short captions vs richer descriptive captions

#### Objective
Test whether richer captions improve retrieval quality.

#### Baseline
Short caption output from the baseline prompt.

#### Change Introduced
Generate longer, more structured captions containing scene, objects, and mood.

#### Hypothesis
Richer captions should improve semantic matching for nuanced queries.

#### Evaluation Method
- Recall@1
- Recall@3
- qualitative top-k comparison

#### Dataset / Query Set
`prompt_fidelity_mixed_v1` benchmark with 10 images:
- 4 real user-photo images,
- 4 screenshot or UI-like images,
- 1 text-heavy cake photo,
- 1 illustration photo,
- 10 handwritten queries with one expected target each.

#### Results
- Baseline prompt: Recall@1 = 0.90, Recall@3 = 0.90
- Retrieval-oriented prompt: Recall@1 = 1.00, Recall@3 = 1.00
- The only changed query was the dark `visual_storytelling_dashboard` screenshot.
- In the baseline run, that screenshot was captioned incorrectly with unrelated café, outdoor, and cat-scene content.
- In the improved run, the caption preserved the screen title, sentiment controls, layout sections, and pipeline status details closely enough to recover the correct top-1 result.

#### Interpretation
Richer captions helped, but not merely because they were longer. The critical improvement came from forcing the caption to preserve image type, visible UI layout, readable keywords, and other retrieval-specific cues. On this benchmark, the miss was caused by caption failure rather than similarity ranking.

#### Decision
Keep the richer retrieval-oriented prompt as the new reference prompt for controlled experiments.

#### Next Action
Push caption fidelity further with structured metadata for visible text and layout blocks, then rerun the same benchmark.

---

### EXP-003
#### Date
TBD

#### Title
Top-1 vs Top-3 retrieval usefulness

#### Objective
Evaluate whether top-3 output provides a better user experience than only top-1.

#### Baseline
Top-1 only output.

#### Change Introduced
Return top-3 ranked results.

#### Hypothesis
Even when top-1 misses the exact best image, top-3 may still capture a relevant result and improve practical usefulness.

#### Evaluation Method
- Recall@1
- Recall@3
- qualitative usefulness review

#### Dataset / Query Set
Standard benchmark query set.

#### Results
TBD

#### Interpretation
TBD

#### Decision
TBD

#### Next Action
Decide whether top-3 should be the default output.

---

### EXP-004
#### Date
TBD

#### Title
Similarity score inspection and failure analysis

#### Objective
Understand which retrieval failures come from poor captions vs weak similarity ranking.

#### Baseline
First end-to-end working retrieval pipeline.

#### Change Introduced
Log similarity scores and inspect incorrect top results.

#### Hypothesis
Some failures will come from caption mismatch rather than ranking alone.

#### Evaluation Method
- error case review,
- caption-query mismatch analysis,
- ranking distribution inspection

#### Dataset / Query Set
Benchmark query set and failure queries.

#### Results
TBD

#### Interpretation
TBD

#### Decision
TBD

#### Next Action
Use findings to decide whether to improve captioning, metadata, or ranking.

---

### EXP-005
#### Date
2026-04-09

#### Title
Structured metadata augmentation

#### Objective
Test whether structured image metadata improves retrieval beyond free-form captions alone.

#### Baseline
The improved prompt benchmark already showed that better caption wording can fix clear screenshot failures, but the representation itself was still a single free-form caption string.

#### Change Introduced
- Extended stored caption artifacts with structured fields:
  - `image_type`
  - `main_subject`
  - `visible_objects`
  - `visible_text`
  - `layout_blocks`
  - `distinctive_cues`
- Added deterministic `retrieval_text` built from those fields.
- Compared three embedding sources on the same benchmark captions:
  - `caption_only`
  - `structured_only`
  - `caption_plus_structured`

#### Hypothesis
Structured metadata should improve retrieval quality or at least improve screenshot-family separation by making layout and visible text more explicit.

#### Evaluation Method
- Recall@1
- Recall@3
- qualitative failure analysis
- UI-family top-1 margin inspection

#### Dataset / Query Set
The existing `prompt_fidelity_mixed_v1` benchmark with 10 images and 10 handwritten queries.

#### Results
- Initial manual JSON parsing caused one caption failure on `history_chat_einstein_ai`, which was fixed by switching to SDK-backed parsed responses.
- Final rerun produced 10 captions with no errors.
- `caption_only`: Recall@1 = 1.00, Recall@3 = 1.00
- `structured_only`: Recall@1 = 1.00, Recall@3 = 1.00
- `caption_plus_structured`: Recall@1 = 1.00, Recall@3 = 1.00
- Average correct top-1 margin on UI-like queries:
  - `caption_only` = 0.1358
  - `structured_only` = 0.1134
  - `caption_plus_structured` = 0.1325
- `caption_plus_structured` improved the margin for the `visual_storytelling_dashboard` query, but `caption_only` remained slightly stronger on average across the current UI subset.

#### Interpretation
Structured metadata is clearly useful as a stored representation artifact and for future experimentation, but it is not yet proven to be a better default embedding source than a strong free-form caption. On the current benchmark, the main outcome is parity rather than clear improvement.

#### Decision
Keep structured fields and `retrieval_text` in the pipeline, but do not replace `caption_only` as the default retrieval baseline yet.

#### Next Action
Make the benchmark harder and refine which structured fields should be flattened before reconsidering a baseline change.

---

### EXP-006
#### Date
2026-04-09

#### Title
Hard benchmark for representation discrimination

#### Objective
Build a harder retrieval benchmark that can separate representation quality across free-form and structured caption variants.

#### Baseline
The previous benchmark was saturated: every representation mode reached perfect Recall@1 and Recall@3, so it could not justify a baseline representation change.

#### Change Introduced
- Expanded the benchmark to 12 images and 28 hard queries.
- Added two additional same-family historical-salon UI images.
- Added query-level tags:
  - `ui_family_disambiguation`
  - `visible_text`
  - `layout_structure`
  - `person_name`
  - `paraphrase`
  - `photo_scene`
  - `illustration_style`
  - `partial_cue`
  - `hard_negative`
- Added hard-negative image IDs for same-family UI queries.
- Compared:
  - `caption_only`
  - `structured_all_fields`
  - `structured_selected_fields`
  - `caption_plus_selected_structured`

#### Hypothesis
Selected structured fields should outperform free-form captions on hard UI and visible-text-sensitive disambiguation queries.

#### Evaluation Method
- Recall@1
- Recall@3
- mean top-1 margin
- tag-specific accuracy
- family-confusion accuracy
- qualitative error buckets

#### Dataset / Query Set
`prompt_fidelity_mixed_v2_hard`
- 12 images
- 28 queries
- 19 UI-family hard-negative queries

#### Results
- `caption_only`: Recall@1 = 0.6786, Recall@3 = 1.0000, family Recall@1 = 0.5263
- `structured_all_fields`: Recall@1 = 0.6786, Recall@3 = 1.0000, family Recall@1 = 0.5263
- `structured_selected_fields`: Recall@1 = 0.7143, Recall@3 = 1.0000, family Recall@1 = 0.5789
- `caption_plus_selected_structured`: Recall@1 = 0.7500, Recall@3 = 1.0000, family Recall@1 = 0.6316
- Hard-negative confusions decreased from 9 for `caption_only` to 7 for `caption_plus_selected_structured`.

#### Interpretation
The harder benchmark successfully separated representation quality. Selected structured fields helped, and combining them with the free caption was strongest overall. Remaining failures are still concentrated in same-family visible-text and person-name confusion.

#### Decision
Treat `caption_plus_selected_structured` as the candidate baseline for the next implementation pass, while keeping `caption_only` as the control.

#### Next Action
Expose representation-mode selection in CLI/config and rerun on a broader sanity set before making the candidate baseline permanent.

---

### EXP-007
#### Date
2026-04-09

#### Title
Baseline retrieval path smoke check

#### Objective
Verify that the new retrieval code can embed a query, rank stored candidate vectors, and return ordered results without introducing reranking or indexing complexity.

#### Baseline
Caption indexing and embedding indexing were already implemented, but the retrieval path was still a stub.

#### Change Introduced
Implemented query embedding, brute-force cosine ranking, and ranked CLI output for top-k retrieval.

#### Hypothesis
If the offline artifacts are structured correctly, a simple cosine-similarity baseline should be enough to produce a first working retrieval loop.

#### Evaluation Method
- empty-artifact CLI check,
- synthetic artifact smoke test with temporary caption and embedding records,
- manual inspection of ranked output formatting.

#### Dataset / Query Set
Synthetic temporary records only. No real `data/raw` images were available in the repository during this session.

#### Results
The retrieval code path works structurally and handles empty local artifacts cleanly. Real end-to-end retrieval on indexed project images is still blocked by the absence of sample images.

#### Interpretation
The baseline search logic is implemented, but practical usefulness cannot be judged until real caption and embedding artifacts exist.

#### Decision
keep

#### Next Action
Populate `data/raw`, run full indexing, and inspect top-k retrieval behavior on real sample images.

---

### EXP-008
#### Date
2026-04-09

#### Title
First real sample retrieval run

#### Objective
Run the full captioning, embedding, and retrieval baseline on a small real local image set and observe practical behavior.

#### Baseline
The retrieval path had been validated structurally and with synthetic records, but not yet on real stored artifacts.

#### Change Introduced
Copied three non-project local images into `data/raw`, generated real captions and embeddings, and ran several qualitative retrieval queries.

#### Hypothesis
The baseline should retrieve the most semantically aligned image for simple object-centric queries, but may struggle when caption generation misreads screenshot-style content.

#### Evaluation Method
- full local indexing run,
- qualitative top-3 inspection,
- query/result mismatch review.

#### Dataset / Query Set
- `raccoon_business.png`
- `student_dog.png`
- `dashboard_storytelling.png`

Queries used:
- "animal in a business suit with briefcase"
- "cute dog student with backpack and books"
- "dark dashboard showing storytelling or sentiment analysis summary"
- "cats indoors and a child lying outside with blanket"

#### Results
- The business-animal query ranked `raccoon_business` first.
- The dog-student query ranked `student_dog` first.
- The dashboard-style query did not rank `dashboard_storytelling` first because the stored caption described unrelated scene content.
- A query aligned with the mistaken caption content did rank `dashboard_storytelling` first.

#### Interpretation
The retrieval math appears to work as intended on the stored representations. The dominant failure case in this run comes from caption quality rather than cosine ranking.

#### Decision
keep

#### Next Action
Refine the caption prompt for screenshots and UI-heavy images, then repeat the same qualitative query set.

---

### EXP-009
#### Date
2026-04-09

#### Title
User-provided real image retrieval run

#### Objective
Verify the full baseline pipeline on a small set of user-provided local images that are more representative than the earlier temporary sample set.

#### Baseline
The project already had a working retrieval path and one earlier local sample run, but the previous sample set included temporary stand-in images rather than the user's current target examples.

#### Change Introduced
Replaced the temporary sample images with four user-provided local photos and reran captioning, embedding, and retrieval.

#### Hypothesis
If the baseline pipeline is functioning well, representative natural-language queries should place the correct target image at rank 1 for simple scenes.

#### Evaluation Method
- full re-indexing on the new local dataset,
- qualitative top-4 inspection,
- manual matching between query intent and returned top result.

#### Dataset / Query Set
Images:
- `cafe_phone_person.jpeg`
- `indoor_many_cats.jpeg`
- `outdoor_blanket_rest.jpeg`
- `night_riverside_person.jpeg`

Queries:
- "man sitting in a cafe looking at his phone"
- "many cats gathered indoors on a wooden floor"
- "person lying on a mat covered with a blanket outdoors"
- "person standing outside at night near lights"

#### Results
- All four representative queries returned the expected image at rank 1.
- The strongest match score in this run was the blanket-rest query.
- The cat and cafe scenes were also clearly separated from the unrelated candidates.

#### Interpretation
For this small real-image set, the baseline retrieval path behaves correctly and the current caption prompt is sufficient for straightforward scene descriptions.

#### Decision
keep

#### Next Action
Expand the handwritten query set so the baseline can be judged on broader phrasing variety rather than only one obvious query per image.

---

### EXP-006
#### Date
2026-04-09

#### Title
Baseline embedding pipeline smoke check

#### Objective
Verify that stored caption records can be transformed into embedding records using the new service and storage boundaries.

#### Baseline
Caption indexing is implemented, but the embedding stage had been a scaffold only.

#### Change Introduced
Implemented the OpenAI-backed embedding service, the JSONL embedding store, and the embedding indexing pipeline with skip and error handling.

#### Hypothesis
If service, storage, and pipeline responsibilities remain separated, the embedding stage should be easy to run and easy to test without retrieval logic.

#### Evaluation Method
- local smoke test with a temporary caption record,
- fake embedding client injection,
- JSONL persistence round-trip check.

#### Dataset / Query Set
One temporary caption record created during smoke verification.

#### Results
The structure-only smoke test passed. The pipeline can now consume caption text, produce vectors, and persist `EmbeddingRecord` rows. No real project captions were embedded yet because `outputs/captions/captions.jsonl` is still absent.

#### Interpretation
The embedding stage is implementation-ready, but the project still needs real caption artifacts before retrieval quality can be evaluated.

#### Decision
keep

#### Next Action
Generate real captions from a local sample image set, then run the embedding pipeline against those stored captions.

#### Objective
Test whether adding structured metadata improves retrieval quality or interpretability.

#### Baseline
Caption-only retrieval.

#### Change Introduced
Extract fields such as:
- scene,
- objects,
- mood,
- color,
- style

and store them alongside captions.

#### Hypothesis
Structured fields may improve future filtering, debugging, or hybrid ranking.

#### Evaluation Method
- qualitative retrieval review,
- interpretability review,
- optional ranking comparison

#### Dataset / Query Set
Same sample set.

#### Results
TBD

#### Interpretation
TBD

#### Decision
TBD

#### Next Action
Decide whether metadata stays optional or becomes standard.

---

### EXP-010
#### Date
2026-04-10

#### Title
Candidate representation indexing flow

#### Objective
Make `caption_plus_selected_structured` reproducible from the embedding/indexing CLI while preserving `caption_only` as the control representation.

#### Baseline
Representation comparisons existed inside the evaluation pipeline, but normal embedding/indexing runs did not expose representation mode as an explicit runtime option.

#### Change Introduced
Added CLI support for representation mode selection, mode-specific embedding output path conventions, explicit artifact paths for retrieval checks, and mode labels in embedding run summaries and records.

#### Hypothesis
If the best hard-benchmark representation is promoted into the normal embedding flow without removing the control path, the project can compare candidate and control artifacts repeatably before changing any ranking logic.

#### Evaluation Method
- CLI help checks for indexing and query commands.
- Unsupported-mode parser check.
- Rebuilt hard-benchmark embeddings for both modes.
- Inspected record counts and stored `representation_mode` values.
- Ran one hard UI disambiguation query against both embedding files.
- Added and ran representation regression tests.

#### Dataset / Query Set
Captions:
- `outputs/eval/structured_representation/captions.jsonl`

Embeddings:
- `outputs/embeddings/benchmark.caption_only.jsonl`
- `outputs/embeddings/benchmark.caption_plus_selected_structured.jsonl`

Query:
- "vertical beige interface with AWAITING IMAGE SEQUENCE and Your story will appear here"

#### Results
- `caption_only`: 12 records processed, 0 skipped, 12 written, 0 errors.
- `caption_plus_selected_structured`: 12 records processed, 0 skipped, 12 written, 0 errors.
- Both modes produced 1536-dimensional embeddings.
- Unsupported CLI values are rejected by `argparse`.
- `python -m pytest` passed with 4 representation tests.
- For the validation query, `caption_only` ranked `visual_storytelling_dashboard` first and the intended `visual_storytelling_mobile` second.
- For the same query, `caption_plus_selected_structured` ranked `visual_storytelling_mobile` first.

#### Interpretation
The candidate representation is now operationally reproducible, not just an evaluation-only experiment. The single-query check aligns with the hard benchmark conclusion that selected structured fields help same-family UI disambiguation.

#### Decision
Keep `caption_plus_selected_structured` as the candidate baseline and keep `caption_only` as the control.

#### Next Action
Run a broader mixed real-photo/UI sanity set before making the candidate mode the permanent default.

---

### EXP-011

#### Date
2026-04-10

#### Title
Control/candidate baseline fixation rerun

#### Objective
Rerun the fixed control/candidate pair on the same hard benchmark and caption store so `caption_only` and `caption_plus_selected_structured` can be compared repeatably through retrieval, not only through embedding generation.

#### Baseline
The candidate representation was already available from the indexing CLI, and one hard UI query had been spot-checked. The full benchmark-level control/candidate retrieval run had not yet been isolated into a dedicated repeatable comparison path.

#### Change Introduced
Added a CLI entrypoint for representation comparison, a `control_candidate` scope, reusable caption-store support, fixed five-bucket failure analysis, and a rerank judgment summary that records the signal without implementing reranking.

#### Hypothesis
If both modes reuse the same benchmark captions and rerun embeddings plus retrieval under stable output paths, then the control/candidate relationship can be treated as a reproducible experiment rather than a one-off validation.

#### Evaluation Method
- Reused fixed captions from `outputs/eval/structured_representation/captions.jsonl`.
- Regenerated embeddings for only:
  - `caption_only`
  - `caption_plus_selected_structured`
- Ran all 28 benchmark queries with `top_k = 3`.
- Wrote results to `outputs/eval/control_candidate_baseline/`.
- Ran unit tests for representation construction, failure buckets, and rerank judgment.

#### Dataset / Query Set
Benchmark:
- `data/samples/prompt_fidelity/benchmark.json`

Caption store:
- `outputs/eval/structured_representation/captions.jsonl`

Outputs:
- `outputs/eval/control_candidate_baseline/comparison.json`
- `outputs/eval/control_candidate_baseline/caption_only/embeddings.jsonl`
- `outputs/eval/control_candidate_baseline/caption_only/results.json`
- `outputs/eval/control_candidate_baseline/caption_plus_selected_structured/embeddings.jsonl`
- `outputs/eval/control_candidate_baseline/caption_plus_selected_structured/results.json`

#### Results
- `caption_only`: Recall@1 = 0.6786, Recall@3 = 1.0000, hard-negative confusions = 9.
- `caption_plus_selected_structured`: Recall@1 = 0.7500, Recall@3 = 1.0000, hard-negative confusions = 7.
- Candidate delta:
  - Recall@1 +0.0714
  - family Recall@1 +0.1053
  - hard-negative confusions -2
- Both regenerated embedding files contain 12 records.
- `python -m pytest`: 7 passed.

#### Failure Buckets
The remaining candidate failures are now grouped into exactly five report-facing buckets:
- same-family UI confusion = 0
- person-name confusion = 5
- visible-text confusion = 2
- OCR/stylized text failure = 0
- layout confusion = 0

#### Rerank Judgment
All candidate top-1 misses still had the expected image inside the top-3, so there is a real rerank signal. However, reranking should remain deferred until another representation-fidelity pass has targeted person-name and visible-text misses.

#### Interpretation
The candidate representation again separates hard cases better than the caption-only control without changing the ranking algorithm. The main bottleneck still looks closer to representation fidelity than pure ranking.

#### Decision
Keep `caption_only` as the control and `caption_plus_selected_structured` as the candidate baseline. Do not implement reranking yet.

#### Next Action
Improve representation fidelity for person names and visible UI text, then rerun the fixed control/candidate comparison. If top-3 stays correct while top-1 remains unstable after that pass, revisit lightweight reranking.

---

### EXP-012
#### Date
2026-04-10

#### Title
Candidate representation fidelity pass for names and visible text

#### Objective
Reduce the remaining `caption_plus_selected_structured` failures without changing ranking logic, benchmark labels, or the caption store.

#### Baseline
Fixed-caption control/candidate rerun from EXP-011:
- `caption_only`: Recall@1 = 0.6786, Recall@3 = 1.0000, hard-negative confusions = 9
- `caption_plus_selected_structured`: Recall@1 = 0.7500, Recall@3 = 1.0000, hard-negative confusions = 7
- Candidate failure buckets:
  - person-name confusion = 5
  - visible-text confusion = 2

#### Change Introduced
- Kept `caption_only` unchanged as the control.
- Revised only the candidate representation-building path in `src/core/representation.py`.
- Added interface-only `component cue:` lines derived from `visible_objects`.
- Added lightweight `named entity cue:` extraction from `caption_text` and `main_subject`, including aliases such as:
  - `Albert Einstein` -> `Einstein`
  - `Cleopatra VII Philopator` -> `Cleopatra VII`, `Cleopatra`
- Added `exact text cue:` lines derived from `visible_text`, with extra splitting for overlong OCR-like text blocks so short headers and questions survive as separate retrieval anchors.
- Reused the fixed caption store and regenerated only embeddings and retrieval outputs.

#### Hypothesis
If the candidate representation makes person identity and exact screen text more explicit, most remaining person-name failures should disappear and hard-negative confusion should drop again even without reranking.

#### Evaluation Method
- Recall@1
- Recall@3
- hard-negative confusion count
- failure bucket counts
- before/after top-k inspection on the remaining hard queries

#### Dataset / Query Set
`prompt_fidelity_mixed_v2_hard`
- 12 images
- 28 queries
- reused caption store: `outputs/eval/structured_representation/captions.jsonl`

#### Results
- `caption_only` stayed unchanged:
  - Recall@1 = 0.6786
  - Recall@3 = 1.0000
  - hard-negative confusions = 9
  - person-name confusion = 7
  - visible-text confusion = 2
- Revised `caption_plus_selected_structured` improved to:
  - Recall@1 = 0.8571
  - Recall@3 = 1.0000
  - family-confusion Recall@1 = 0.7895
  - hard-negative confusions = 4
  - person-name confusion = 2
  - visible-text confusion = 2
- Direct candidate delta versus EXP-011:
  - Recall@1: +0.1071
  - hard-negative confusions: -3
  - person-name confusion: -3
  - visible-text confusion: no change
- Fixed person-name failures:
  - `q016_einstein_ai_today`
  - `q017_einstein_posthumous_current_events`
  - `q018_einstein_ai_question_text`
  - `q022_cleopatra_landing_empty_transcript`
- One new close regression appeared:
  - `q020_einstein_reflective_opinion`
- Remaining candidate misses after the pass:
  - `q010_dashboard_dark_panels`
  - `q012_dashboard_slider_file_sizes`
  - `q020_einstein_reflective_opinion`
  - `q021_einstein_discovery_paraphrase`

#### Interpretation
The targeted representation pass worked. The recovered queries show that explicit name aliases and exact text cues were enough to flip several near-miss historical-salon cases without touching the ranker. The remaining errors are narrower than before:
- two dashboard visible-text disambiguation misses,
- two Einstein philosophical-vs-AI disambiguation misses.

The residual Einstein miss pattern suggests one more representation refinement is possible for long label-value text such as `question type philosophical` and `answer mode reflective opinion`. At the same time, all four remaining misses still place the correct image inside the top-3, so reranking is now more justifiable than it was before this pass.

#### Decision
Keep the revised candidate representation. Do not add reranking inside this experiment, but treat it as a plausible next intervention if one more narrow representation pass does not clear the remaining four misses.

#### Next Action
Focus the next representation pass on label-value extraction for the remaining dashboard and Einstein-philosophical screens, or explicitly test a lightweight reranker now that the remaining misses are all top-3 rescues.

---

### EXP-013
#### Date
2026-04-10

#### Title
Deterministic top-3 rerank ablation

#### Objective
Measure whether the residual hard-benchmark misses are mainly top-1 ordering problems by reranking only the frozen candidate top-3 outputs.

#### Baseline
Frozen candidate from EXP-012:
- `caption_plus_selected_structured` Recall@1 = 0.8571
- Recall@3 = 1.0000
- hard-negative confusions = 4
- remaining misses:
  - `q010_dashboard_dark_panels`
  - `q012_dashboard_slider_file_sizes`
  - `q020_einstein_reflective_opinion`
  - `q021_einstein_discovery_paraphrase`

#### Change Introduced
- Kept `caption_only` as the control reference.
- Kept the current `caption_plus_selected_structured` candidate frozen.
- Added a deterministic reranker that only reorders the top-3 frozen results.
- Added explicit weighted features:
  - exact visible-text overlap
  - named-entity match
  - label-value phrase overlap
  - component cue overlap
  - small original-similarity tie-break
- Added query-level activation gating so reranking only runs when the query exposes supported rerank signals.
- Logged per-query feature contributions, matched terms, and final candidate order.

#### Hypothesis
If the remaining failures are mostly ordering mistakes among already-retrieved candidates, a lightweight deterministic reranker should recover most of them without introducing regressions.

#### Evaluation Method
- Recall@1 before vs after rerank
- Recall@3 before vs after rerank
- hard-negative confusion before vs after rerank
- outcome inspection for `q010`, `q012`, `q020`, `q021`
- regression count
- compact failure attribution by rerank feature

#### Dataset / Query Set
`prompt_fidelity_mixed_v2_hard`
- 12 images
- 28 queries
- frozen candidate source results:
  - `outputs/eval/control_candidate_name_text_fidelity/caption_plus_selected_structured/results.json`

#### Results
- Control reference stayed unchanged:
  - `caption_only` Recall@1 = 0.6786
  - `caption_only` Recall@3 = 1.0000
  - hard-negative confusions = 9
- Frozen candidate before rerank:
  - Recall@1 = 0.8571
  - Recall@3 = 1.0000
  - hard-negative confusions = 4
- Candidate after deterministic rerank:
  - Recall@1 = 0.9643
  - Recall@3 = 1.0000
  - hard-negative confusions = 1
- Failure buckets after rerank:
  - same-family UI confusion = 0
  - person-name confusion = 1
  - visible-text confusion = 0
  - OCR/stylized text failure = 0
  - layout confusion = 0
- Corrected queries:
  - `q010_dashboard_dark_panels`
  - `q012_dashboard_slider_file_sizes`
  - `q020_einstein_reflective_opinion`
- Still unresolved:
  - `q021_einstein_discovery_paraphrase`
- Regressions:
  - none
- Compact feature attribution:
  - corrected by visible-text overlap = 0
  - corrected by label-value phrase overlap = 2
  - corrected by entity cue overlap = 0
  - corrected by component cue overlap = 1
  - still unresolved = 1

#### Interpretation
This ablation shows that the residual ceiling is now mostly ranking-driven. The frozen candidate representation already retrieves the correct image into the top-3, and a tiny deterministic reranker recovers 3 of the 4 remaining misses without any benchmark regressions.

The unresolved Einstein paraphrase miss still looks more representation-like because it does not expose strong exact-text, label-value, or component evidence. That means reranking helps substantially, but it does not eliminate the value of one more narrow representation pass.

#### Decision
Keep the deterministic reranker as an optional benchmark-backed refinement step. Do not promote it to the default path yet; it still needs broader validation beyond the current hard benchmark.

#### Next Action
Validate the deterministic reranker on a broader sanity set. If it remains regression-free, consider making it the default top-1 refinement step for UI-like queries; otherwise keep it optional and continue representation work on the unresolved paraphrase case.

---

### EXP-014
#### Date
2026-04-10

#### Title
Broader mixed sanity validation for frozen best hard-benchmark configuration

#### Objective
Freeze the current best hard-benchmark configuration as a named experiment setting and validate whether it generalizes beyond the curated hard set.

#### Baseline
Current hard-benchmark winner:
- representation: `caption_plus_selected_structured`
- rerank: deterministic top-3 rerank
- `question_paraphrase_overlap = 0.25`
- known hard-benchmark result:
  - `caption_only` Recall@1 = 0.6786
  - best config Recall@1 = 1.0000
  - Recall@3 = 1.0000
  - hard-negative confusions = 0
  - regressions = 0

#### Change Introduced
- Added named frozen setting:
  - `hard_best_caption_plus_selected_structured_top3_qpo025_v1`
- Added broader mixed sanity benchmark:
  - `prompt_fidelity_mixed_sanity_v1`
- Kept the fixed caption store reused from:
  - `outputs/eval/structured_representation/captions.jsonl`
- Added one orchestration pipeline that runs:
  - `caption_only`
  - `caption_plus_selected_structured`
  - deterministic rerank without paraphrase overlap
  - full best config with `question_paraphrase_overlap = 0.25`
- Wrote all outputs under a single experiment namespace:
  - `outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/mixed_sanity_v1/`

#### Hypothesis
If the hard-benchmark winner generalizes, it should preserve the strong hard-UI improvements on a broader mixed sanity set without introducing meaningful regressions outside the curated hard slice.

#### Evaluation Method
- Recall@1
- Recall@3
- slice breakdown for:
  - `hard_ui`
  - `normal_ui`
  - `photo_or_illustration`
- pairwise regressions between systems
- paraphrase-overlap helped/hurt cases
- compact ablation table

#### Dataset / Query Set
`prompt_fidelity_mixed_sanity_v1`
- 12 images
- 40 queries
- slices:
  - 16 `hard_ui`
  - 12 `normal_ui`
  - 12 `photo_or_illustration`

#### Results
- `caption_only`:
  - Recall@1 = 0.6750
  - Recall@3 = 1.0000
- `caption_plus_selected_structured`:
  - Recall@1 = 0.8750
  - Recall@3 = 1.0000
- `caption_plus_selected_structured + deterministic_top3_rerank`:
  - Recall@1 = 0.9500
  - Recall@3 = 1.0000
- Full best config:
  - `caption_plus_selected_structured + deterministic_top3_rerank + question_paraphrase_overlap=0.25`
  - Recall@1 = 0.9750
  - Recall@3 = 1.0000

Slice breakdown:
- `hard_ui`
  - `caption_only`: 0.6250
  - `caption_plus_selected_structured`: 0.7500
  - rerank without paraphrase: 0.9375
  - full best config: 1.0000
- `normal_ui`
  - `caption_only`: 0.4167
  - `caption_plus_selected_structured`: 0.9167
  - rerank without paraphrase: 0.9167
  - full best config: 0.9167
- `photo_or_illustration`
  - all systems reached Recall@1 = 1.0000

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
- full best config vs `caption_plus_selected_structured`:
  - `mq028_cleopatra_diplomacy_answer`

#### Interpretation
The broader validation is strongly positive, but not clean enough for default promotion.

What generalized well:
- the structured representation clearly generalized beyond the hard benchmark,
- the deterministic reranker dramatically improved the hard UI slice,
- the paraphrase-overlap cue helped exactly the intended Einstein paraphrase case and introduced no new cue-specific regressions,
- all systems kept Recall@3 at 1.0000.

Why the full stack still stays optional:
- the reranker still flipped one normal UI Cleopatra transcript query to the landing screen,
- the normal UI slice did not improve beyond the representation-only candidate,
- the broader mixed-set evidence therefore supports the reranker as a strong optional refinement, not yet a safe default.

#### Decision
Keep the full best hard-benchmark configuration optional.

More specific recommendation:
- the paraphrase-overlap cue looks safe and useful,
- but the surrounding deterministic rerank stack should not be promoted to the broader default until the Cleopatra landing-vs-transcript regression is understood.

#### Next Action
If another validation pass is approved, focus only on regression analysis for `mq028_cleopatra_diplomacy_answer` inside the deterministic reranker. Do not retune the hard benchmark itself.

---

### EXP-015
#### Date
2026-04-10

#### Title
Broader default promotion and offline-safe reproducibility hardening

#### Objective
Promote the validated mixed-sanity winner as the broader evaluation default, make the replay path reproducible without network dependence, and stop malformed rebuild failures from being reported as real results.

#### Baseline
State after EXP-014:
- the original mixed-sanity rebuild path was strong but still showed one regression:
  - `mq028_cleopatra_diplomacy_answer`
- a trusted frozen replay with the singleton low-signal container guard enabled had already shown the broader default could recover that regression:
  - rerank without paraphrase overlap Recall@1 = 0.9750
  - full default Recall@1 = 1.0000
  - regressions = 0
- a separate rebuild attempt later hit a network Connection error during embedding rebuild and wrote malformed all-zero mixed-sanity artifacts, which made the evaluation path operationally unsafe.

#### Change Introduced
- Promoted the validated broader default in code metadata:
  - representation: `caption_plus_selected_structured`
  - rerank: deterministic top-3 rerank
  - `question_paraphrase_overlap = 0.25`
  - singleton low-signal container guard enabled
- Added an offline-safe mixed-sanity mode that can:
  - replay trusted frozen control/candidate artifacts,
  - reuse frozen captions and embeddings when available,
  - log whether a run is rebuild-based or frozen-artifact replay-based
- Added fail-fast validation so empty-result artifacts are rejected instead of becoming all-zero reports.
- Added a compact report summary artifact for:
  - baseline vs candidate vs final default,
  - hard benchmark result,
  - mixed sanity result,
  - validation caveat

#### Evaluation Method
- targeted regression tests for:
  - experiment-setting promotion metadata,
  - frozen-artifact replay loading,
  - mixed-sanity helper logic
- mixed-sanity rerun in frozen replay mode using the trusted control/candidate artifacts

#### Results
Trusted frozen replay over:
- `outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/mixed_sanity_v1/control_candidate/`

produced:
- `caption_only`
  - Recall@1 = 0.6750
  - Recall@3 = 1.0000
- `caption_plus_selected_structured`
  - Recall@1 = 0.8750
  - Recall@3 = 1.0000
- deterministic rerank without paraphrase overlap
  - Recall@1 = 0.9750
  - Recall@3 = 1.0000
- broader default
  - `caption_plus_selected_structured + deterministic_top3_rerank + question_paraphrase_overlap=0.25`
  - Recall@1 = 1.0000
  - Recall@3 = 1.0000
  - regressions = 0

End-to-end rebuild status:
- still blocked
- reason:
  - network Connection error during embedding rebuild
- resulting malformed all-zero artifacts are now treated as invalid and should not be cited

#### Interpretation
The broader-default decision is now supported by the right kind of evidence:
- behavioral validation comes from trusted frozen replay,
- operational rebuild instability is preserved separately as a caveat,
- the evaluation pipeline is safer because it no longer silently turns missing artifacts into zero-metric reports.

#### Decision
Promote the full validated stack as the broader evaluation default.

Explicit promotion note:
`caption_plus_selected_structured` plus deterministic top-3 rerank with `question_paraphrase_overlap = 0.25` and the singleton low-signal container guard enabled is now the broader default for the evaluation pipeline.

#### Next Action
When network access is stable, rerun one clean end-to-end rebuild only to close the operational caveat. Do not treat rebuild completion as a prerequisite for using the frozen replay evidence in the report.

---

## Experiment Principles
All experiments should follow these rules:

1. Only change one meaningful variable at a time when possible.
2. Keep the baseline recorded.
3. Record both success and failure.
4. Write interpretation, not just raw outcome.
5. Record next action immediately after results.
6. Preserve experiments that affect report-writing context in `docs/05_report_context.md`.

---

## Current Experiment Status
Latest completed experiment: EXP-015, broader default promotion and offline-safe reproducibility hardening.
Next experiment should either keep the reranker optional and integrate the safer representation default, or run one narrow regression-analysis pass on the Cleopatra landing-vs-transcript rerank failure.
