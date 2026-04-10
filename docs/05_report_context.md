# 05 Report Context

## Purpose of This File
This file stores report-ready reasoning and interpretation that should not be lost during implementation.

It is not just a coding memo.
It is a writing support layer for:
- final report,
- presentation,
- architecture explanation,
- discussion of limitations,
- future work sections.

Anything that may later help explain:
- why this project matters,
- why specific design choices were made,
- what was learned,
- what tradeoffs were accepted

should be preserved here.

---

## 1. Project Importance
This project matters because image collections are often difficult to search in a meaningful way.
Traditional retrieval methods rely heavily on:
- filenames,
- manually assigned tags,
- rigid keyword matching.

These methods become weak when metadata is sparse, inconsistent, or semantically distant from how users naturally describe images.

The project therefore addresses a practical retrieval problem:
how to search images by meaning rather than exact keyword overlap.

---

## 2. Why Semantic Retrieval Is the Right Framing
The core value of the project lies in reframing image retrieval as semantic matching instead of literal lookup.

The user usually does not know:
- the file name,
- the folder path,
- the exact stored label.

The user knows the concept they are looking for.

This is why embedding-based semantic comparison is more appropriate than traditional keyword matching.

Possible report wording:
> The system was designed as a semantic retrieval pipeline because the primary challenge was not simple filename lookup, but meaning alignment between free-form user queries and visually rich image content.

---

## 3. Why the Project Starts With a Caption-Based Baseline
The caption-based baseline was chosen first because it provides the cleanest and most explainable path to a working system.

Reasons:
- directly aligned with the assignment requirement,
- uses human-readable intermediate outputs,
- easier to debug than fully opaque matching,
- simpler to evaluate and present,
- forms a clear baseline for later comparison.

Possible report wording:
> A caption-based retrieval baseline was adopted as the first system because it balanced implementation simplicity, interpretability, and direct alignment with the assignment's multimodal retrieval objective.

---

## 4. Baseline Limitation That Must Be Acknowledged
The baseline is useful, but not ideal.

Important limitation:
- visual information is compressed into text,
- some fine-grained semantic or aesthetic cues may be lost,
- retrieval quality depends heavily on caption quality.

This should not be hidden.
It should be explicitly acknowledged as the main reason for future improvement.

Possible report wording:
> Although the caption-based approach provides an accessible semantic bridge between images and text queries, it also introduces an information bottleneck because rich visual content must first be compressed into textual form.

---

## 5. Why Modular Architecture Was Important
The project deliberately used a modular design with separate layers for:
- config,
- services,
- pipelines,
- storage,
- CLI,
- evaluation.

This was important for three reasons:
1. to avoid spaghetti code,
2. to make future upgrades easier,
3. to preserve clarity for evaluation and reporting.

Possible report wording:
> The repository was intentionally structured as a modular system so that caption generation, embedding creation, similarity ranking, storage, and evaluation could evolve independently without introducing excessive coupling.

---

## 6. Why Documentation Was Treated as Part of Engineering
This project did not treat documentation as an afterthought.
Documentation was part of implementation because:
- the system is iterative,
- design rationale can easily be forgotten,
- experiments need interpretation,
- reports require accurate reconstruction of technical choices.

Possible report wording:
> Documentation and structured logging were treated as core engineering assets rather than post-hoc cleanup, enabling continuity across iterations and preserving design rationale for later analysis and reporting.

---

## 7. Why Evaluation Must Be Included
A system that only runs is not enough.
The project needs to show whether retrieval quality is actually improving.

Evaluation matters because it helps answer:
- did a better caption prompt help?
- is top-3 more useful than top-1 only?
- are failures caused by poor captions or poor ranking?
- does added structure improve practical relevance?

Possible report wording:
> Evaluation was introduced early in the design process to ensure that architectural changes could be judged empirically rather than only intuitively.

---

## 8. Interpreting Possible Outcomes

### If the baseline performs reasonably well
Interpretation:
- caption-based retrieval is a viable baseline,
- semantic search can work even without manual tags,
- the modular architecture supports clean expansion.

### If the baseline performs weakly
Interpretation:
- the core retrieval framing is still valid,
- but the caption bottleneck is more severe than expected,
- this strengthens the case for structured metadata, richer caption prompts, reranking, or direct image embeddings.

### If top-3 works much better than top-1
Interpretation:
- ranking may still be useful even if exact top-1 is unstable,
- the system may benefit from reranking or user feedback.

---

## 9. Future Work Framing
Future work should not sound random.
It should be framed as a response to known baseline limitations.

Good future work directions:
- structured metadata extraction,
- direct image embeddings,
- hybrid ranking,
- reranking,
- vector indexing,
- user relevance feedback.

Possible report wording:
> Future work should focus on reducing caption-induced information loss and improving ranking quality through richer multimodal representations and more selective candidate refinement.

---

## 10. What Makes This Project More Than a Basic Script
This project should be described not merely as a script that compares embeddings, but as a retrieval system with:
- an offline indexing stage,
- an online search stage,
- modular architecture,
- evaluation potential,
- clear upgrade paths.

Possible report wording:
> Rather than being implemented as a single monolithic script, the project was developed as a modular retrieval system with distinct indexing, search, storage, and evaluation components.

---

## 11. Report Themes To Emphasize
When writing the report later, likely strong themes include:

### Theme A
Semantic retrieval as a solution to weak metadata environments

### Theme B
Caption-based retrieval as a practical and explainable multimodal baseline

### Theme C
Architecture discipline as a way to support iteration and future improvement

### Theme D
Evaluation as the bridge between implementation and evidence

### Theme E
Baseline limitations as justification for richer multimodal retrieval

---

## 12. Presentation Angle
If this becomes a presentation, the narrative should likely be:

1. Why keyword search is weak for images
2. Why semantic retrieval is needed
3. How the caption + embedding baseline works
4. Why that baseline is useful
5. Where the baseline fails
6. How the architecture supports future upgrades
7. What improvements would come next

This creates a logical story instead of just a tool demo.

---

## 13. Current Report-Relevant Claims To Preserve
These claims currently matter and should be preserved:

- The project is solving meaning mismatch, not just missing filenames.
- The baseline was chosen for interpretability and assignment alignment.
- The modular architecture is part of the engineering contribution.
- Evaluation is necessary to make redesign evidence-based.
- Future work is motivated by the caption bottleneck.

---

## 14. Notes To Update After Real Experiments
After experiments begin, update this file with:
- notable success patterns,
- common failure patterns,
- which design changes actually helped,
- whether richer captions improved retrieval,
- whether metadata improved interpretability,
- how evaluation results should be interpreted in the final report.

Real experiment update on 2026-04-09:
- A controlled prompt comparison on a 10-image mixed benchmark improved Recall@1 and Recall@3 from 0.90 to 1.00.
- The decisive recovery came from a screenshot-like dashboard image, not from ordinary photo queries.
- No ranking logic changed during that experiment, so the result is strong evidence that caption fidelity was the active bottleneck on the benchmark.
- OCR-like capture of visible text is still imperfect, especially for stylized or handwritten text, so this remains an honest limitation to preserve in the report.
- A follow-up structured-representation experiment added explicit fields for image type, main subject, visible objects, visible text, layout blocks, and distinctive cues.
- After the structured output path was stabilized, `caption_only`, `structured_only`, and `caption_plus_structured` all reached perfect recall on the same small benchmark.
- This means structured metadata improved interpretability and experiment flexibility, but did not yet prove that it should replace the free-form caption as the default embedding source.

Possible report wording:
> In the first controlled prompt experiment, retrieval quality improved without any change to the ranking algorithm. This indicates that the dominant error source was caption fidelity, particularly for screenshot-like images whose layout and visible text were not preserved well by the simpler baseline prompt.

Possible follow-up wording:
> Structured metadata extraction improved the transparency of the representation layer by separating image type, visible text, layout, and distinctive cues. However, on the current small benchmark it did not deliver a clear retrieval advantage over strong free-form captions, suggesting that representation design still requires harder evaluation and more selective field usage.

Hard benchmark update on 2026-04-09:
- The benchmark was expanded to 12 images and 28 hard queries with tags for UI-family disambiguation, visible text, layout structure, person names, paraphrases, photo scenes, illustration style, partial cues, and hard negatives.
- This benchmark did separate representation quality:
  - `caption_only` Recall@1 = 0.6786
  - `structured_selected_fields` Recall@1 = 0.7143
  - `caption_plus_selected_structured` Recall@1 = 0.7500
- Family-confusion Recall@1 improved from 0.5263 for `caption_only` to 0.6316 for `caption_plus_selected_structured`.

Candidate-baseline CLI update on 2026-04-10:
- Representation mode is now a first-class runtime option for embedding/indexing runs.
- The indexing CLI supports `caption_only` as the control and `caption_plus_selected_structured` as the candidate baseline.
- Embedding records store the selected `representation_mode`, and default pipeline output paths can be derived per mode.
- A controlled validation regenerated two hard-benchmark embedding files:
  - `outputs/embeddings/benchmark.caption_only.jsonl`
  - `outputs/embeddings/benchmark.caption_plus_selected_structured.jsonl`
- On the query "vertical beige interface with AWAITING IMAGE SEQUENCE and Your story will appear here", the control mode ranked the dashboard sibling first, while the candidate mode ranked the intended mobile UI first.
- This supports the report claim that structured selected fields are useful for UI-family disambiguation, but the project still needs a broader sanity set before calling the candidate the permanent default.

Possible report wording:
> After the hard benchmark identified `caption_plus_selected_structured` as the strongest representation, the indexing flow was updated so representation choice became an explicit runtime variable rather than a hidden experiment setting. This preserved `caption_only` as a control while making the candidate baseline reproducible from the command line.
- The result supports a candidate baseline shift toward a mixed representation, but the benchmark is still small and should be validated on a broader set before becoming permanent.

Possible report wording:
> After the initial benchmark became saturated, a harder benchmark with same-family UI screens and tagged hard-negative queries was introduced. This made representation differences measurable: combining the free caption with selected structured fields improved hard-case Recall@1 and reduced same-family confusion compared with captions alone.

Control/candidate fixation update on 2026-04-10:
- A dedicated control/candidate comparison path now reruns only `caption_only` and `caption_plus_selected_structured` on the same benchmark definition and the same fixed caption store.
- The fixed-caption run used `outputs/eval/structured_representation/captions.jsonl` and regenerated embeddings plus retrieval results under `outputs/eval/control_candidate_baseline/`.
- `caption_only` remains the control because the project began with caption-only retrieval as the simplest interpretable baseline.
- `caption_plus_selected_structured` remains the candidate baseline because it improved hard-case separation without changing the embedding model, similarity function, or ranking logic.
- Rerun results:
  - `caption_only` Recall@1 = 0.6786, Recall@3 = 1.0000, hard-negative confusions = 9
  - `caption_plus_selected_structured` Recall@1 = 0.7500, Recall@3 = 1.0000, hard-negative confusions = 7
  - candidate delta: Recall@1 +0.0714, family Recall@1 +0.1053, hard-negative confusions -2
- Remaining candidate failures are bucketed as:
  - same-family UI confusion = 0
  - person-name confusion = 5
  - visible-text confusion = 2
  - OCR/stylized text failure = 0
  - layout confusion = 0
- The rerank signal is real but not yet an implementation decision: all candidate top-1 misses still had the expected image in top-3, but the current failure shape points first to missing or underweighted representation details around person names and visible UI text.

Report-ready one-line conclusion:
> The system began with a caption-only baseline; on the hard benchmark, adding selected structured cues meaningfully separated hard cases; the remaining ceiling appears closer to representation fidelity than to pure ranking.

Useful report phrasing:
> Because ranking logic was held constant while only the text representation changed, the improvement from `caption_only` to `caption_plus_selected_structured` is best interpreted as evidence for representation quality, not as a ranking-system improvement.

Useful limitation phrasing:
> The fact that every remaining top-1 miss still placed the correct image in the top-3 suggests that a lightweight reranker may eventually help, but the next justified step is still to improve representation fidelity for person names, visible text, and exact UI state.

Representation fidelity pass update on 2026-04-10:
- A second fixed-caption control/candidate rerun targeted only the remaining candidate failure modes: person-name confusion and visible-text confusion.
- The representation revision did not alter ranking logic. It only added:
  - interface component cues from `visible_objects`,
  - named entity cues and aliases from `caption_text` and `main_subject`,
  - exact visible-text cues recovered from overlong OCR-like fields.
- The new run wrote artifacts under `outputs/eval/control_candidate_name_text_fidelity/`.
- Results:
  - `caption_only` stayed unchanged at Recall@1 = 0.6786 and Recall@3 = 1.0000
  - `caption_plus_selected_structured` improved to Recall@1 = 0.8571 and Recall@3 = 1.0000
  - candidate hard-negative confusions dropped from 7 to 4
  - candidate person-name confusion dropped from 5 to 2
  - candidate visible-text confusion stayed at 2
- The pass recovered Albert Einstein AI/current-events queries and the Cleopatra landing-page query without any reranking, which is strong evidence that representation fidelity was still the active bottleneck.
- After this pass, all 4 remaining candidate misses still place the correct image in the top-3. This makes lightweight reranking more justified than before, but it was still deferred in the reported experiment so the gain remains attributable to representation alone.

Useful report phrasing:
> A targeted representation-only revision raised hard-benchmark Recall@1 from 0.7500 to 0.8571 while leaving the ranking algorithm unchanged. This indicates that several near-miss failures were caused by under-specified candidate text rather than by the similarity function itself.

Deterministic rerank ablation update on 2026-04-10:
- A separate rerank ablation was run on the frozen candidate results from `outputs/eval/control_candidate_name_text_fidelity/caption_plus_selected_structured/results.json`.
- The reranker only reorders the existing top-3 candidates. It does not regenerate captions or embeddings and does not use an LLM or cross-encoder.
- The deterministic feature set was intentionally small and report-friendly:
  - exact visible-text overlap
  - named-entity match
  - label-value phrase overlap
  - component cue overlap
  - a small original-similarity tie-break
- On the hard benchmark, the rerank ablation improved the frozen candidate from:
  - Recall@1 = 0.8571 to 0.9643
  - hard-negative confusions = 4 to 1
- Recall@3 stayed at 1.0000, which is consistent with the hypothesis that the remaining problem was mostly top-1 ordering inside an already-correct top-3 set.
- The reranker corrected:
  - `q010_dashboard_dark_panels`
  - `q012_dashboard_slider_file_sizes`
  - `q020_einstein_reflective_opinion`
- The remaining unresolved miss was:
  - `q021_einstein_discovery_paraphrase`
- No regressions were introduced on the current hard benchmark.
- The strongest correction pattern came from label-value phrase overlap, not entity matching alone. This is important for the report because it suggests that the residual ordering errors were driven by underused structured UI state rather than by weak general semantics.

Useful report phrasing:
> After representation fidelity was improved, the remaining errors were tested with a deterministic top-3 reranker rather than a heavier cross-encoder. Because Recall@3 was already saturated, the rerank ablation served as a clean test of whether the residual failures were mainly ordering problems. The result was strongly positive: Recall@1 increased further without any change to the underlying candidate set.

Useful recommendation phrasing:
> The deterministic reranker should be described as an optional refinement rather than a fully established default. Its benchmark gains are strong, but its rule set was tuned against a small hard benchmark and still leaves one paraphrase-heavy miss unresolved.

Broader mixed sanity validation update on 2026-04-10:
- The hard-benchmark winner was frozen as a named setting:
  - `hard_best_caption_plus_selected_structured_top3_qpo025_v1`
- A broader mixed sanity benchmark was added:
  - `prompt_fidelity_mixed_sanity_v1`
  - 40 queries over the same 12 images
  - slices:
    - 16 `hard_ui`
    - 12 `normal_ui`
    - 12 `photo_or_illustration`
- Mixed-set outputs were written under:
  - `outputs/eval/hard_best_caption_plus_selected_structured_top3_qpo025_v1/mixed_sanity_v1/`
- The first rebuild-based mixed sanity run showed strong generalization but still had one normal-UI regression:
  - `mq028_cleopatra_diplomacy_answer`
  - the deterministic reranker flipped the correct diplomacy transcript screen to the Cleopatra landing screen
- A follow-up validation pass kept the same trusted frozen control/candidate artifacts and enabled the singleton low-signal container guard already present in the deterministic reranker.
- That trusted frozen-artifact replay produced the validation result that now matters for reporting:
  - `caption_only` Recall@1 = 0.6750, Recall@3 = 1.0000
  - `caption_plus_selected_structured` Recall@1 = 0.8750, Recall@3 = 1.0000
  - deterministic rerank without paraphrase overlap Recall@1 = 0.9750, Recall@3 = 1.0000
  - full broader default Recall@1 = 1.0000, Recall@3 = 1.0000
  - observed regressions in the trusted frozen replay: none
- This sharper interpretation should now be preserved in the report:
  - the structured representation generalized clearly beyond the hard benchmark,
  - the singleton low-signal container guard removed the last known mixed-sanity rerank regression,
  - the full stack is now strong enough to treat as the broader evaluation default.
- The validation caveat must remain explicit:
  - the broader-default promotion is backed by trusted frozen-artifact replay, not by a fresh full rebuild,
  - a separate end-to-end rerun that tried to rebuild embeddings hit a network Connection error and produced malformed all-zero artifacts,
  - those broken rebuild artifacts should not be cited as evidence.

Useful report phrasing:
> On a broader 40-query mixed sanity set, the promoted default preserved perfect Recall@3 and reached Recall@1 = 1.0000 in trusted frozen-artifact replay. The gain remained concentrated in the hard UI slice, while photo and illustration retrieval stayed saturated throughout.

Useful report phrasing:
> The final promotion decision was based on frozen-artifact replay over trusted control/candidate outputs, which cleanly isolated retrieval and reranking behavior from rebuild instability. This makes the evidence reproducible offline while keeping the remaining rebuild limitation explicit.

Useful recommendation phrasing:
> The broader evaluation default is now `caption_plus_selected_structured` plus deterministic top-3 rerank with `question_paraphrase_overlap = 0.25` and the singleton low-signal container guard enabled. The remaining caveat is operational rather than behavioral: a fresh end-to-end rebuild still needs to be rerun once embedding-network access is stable.

---

## 15. UI Design Framing For Reporting
The UI direction is intentionally documented in a root-level `DESIGN.md` rather than being left as an implicit taste decision.

Why this matters for reporting:
- it shows that interface work was treated as part of system design, not cosmetic polish,
- it provides a reproducible design brief for future implementation,
- it lets AI-assisted UI work stay consistent across sessions.

Useful phrasing:
> The user-facing design direction was codified in a `DESIGN.md` document so that future interface implementation could remain stylistically consistent and traceable, even when generated or iterated with AI coding assistance.

---

## 16. Why Centralized Milestone Logs Help The Report
The `docs/logs/` archive is useful because it preserves:
- task objectives,
- implementation plans,
- concrete code or document changes,
- validation evidence,
- unresolved issues,
- next-step rationale.

Useful phrasing:
> In addition to live status tracking, milestone-level logs were preserved in a dedicated archive so that implementation progress, rationale, and changes could later be reconstructed accurately for the final report.
