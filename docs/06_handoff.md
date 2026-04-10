# 06 Handoff

## 1. Current Project State
The project has moved out of the pure scaffolding stage and now has:
- a working caption -> embedding -> retrieval baseline,
- a successful user-image baseline run,
- a small controlled prompt-fidelity benchmark for comparing caption changes,
- a structured metadata layer with deterministic `retrieval_text`,
- and a harder tagged benchmark that can separate representation quality.
- a configurable embedding/indexing path where `caption_plus_selected_structured` is the candidate baseline and `caption_only` remains the control.
- a fixed control/candidate retrieval comparison under `outputs/eval/control_candidate_baseline/`.

The conceptual design is already defined:
- the project goal is semantic image retrieval from a natural-language query,
- the initial system will use vision-generated captions plus text embeddings,
- the repository is being prepared to support modular implementation and long-term iteration,
- the project now has a stronger root-level `DESIGN.md` and a centralized milestone log archive.

The project is still early and deliberately avoids advanced retrieval features.
The immediate priority is now to improve representation fidelity for the remaining person-name and visible-text failures before making any reranking decision.

---

## 2. What Is Already Defined
The following major points are already decided:

- We are starting with a caption-based retrieval baseline.
- The codebase must remain modular from day one.
- Documentation and logs are part of the implementation process.
- Report-ready context should be preserved continuously.
- The work style should follow a loop:
  plan -> implement -> evaluate -> redesign -> patch -> log

Key core files already planned:
- `GLOBAL.md`
- `docs/00_project_planning.md`
- `docs/01_problem_definition.md`
- `docs/02_architecture.md`
- status and handoff files

---

## 3. What Was Just Completed
Recently completed conceptual work includes:
- project planning,
- problem framing,
- architecture direction,
- documentation hierarchy definition,
- logging strategy definition,
- anti-spaghetti operating rules,
- report-aware development policy,
- baseline caption indexing implementation,
- baseline embedding indexing implementation,
- baseline retrieval implementation,
- first real local sample retrieval run,
- first successful user-image retrieval run,
- first controlled prompt-fidelity comparison on a mixed photo/UI benchmark,
- first structured-representation comparison on the same benchmark,
- first hard tagged benchmark with same-family UI disambiguation and hard negatives,
- first CLI-level candidate-baseline embedding flow with mode-specific output artifacts,
- first fixed control/candidate retrieval rerun with stable failure buckets and rerank judgment,
- design-system consolidation using a `DESIGN.md` workflow,
- centralized milestone logging in `docs/logs/`.

This means the project now has a stable conceptual foundation, two offline implementation slices, one simple online retrieval slice, multiple real local qualitative runs, one repeatable evaluation loop for prompt changes, a richer representation layer, and a benchmark strong enough to expose representation differences.

---

## 4. What Still Needs Work
The following still needs to be done next:

### Repository setup work
- keep status and handoff docs current as implementation progresses.
- keep the milestone archive in `docs/logs/` current as major tasks finish.

### Baseline implementation work
- use the new representation-mode CLI path for repeatable comparisons,
- validate `caption_plus_selected_structured` as the candidate baseline on a broader mixed set,
- preserve visible text and layout structure more reliably.
- improve person-name and exact visible-text fidelity before adding reranking.

### Evaluation setup work
- keep the new prompt benchmark current as caption changes land,
- expand it carefully when new failure modes or sibling-screen ambiguities need coverage,
- persist experiment outputs clearly for later reporting.

---

## 5. Most Important Next Task
The single highest-value next task is:

**Improve representation fidelity for the remaining `caption_plus_selected_structured` failures.**

This task matters most because the fixed hard-benchmark rerun already confirmed the candidate beats the caption-only control. The remaining misses are concentrated in person-name and visible-text confusion, so the next improvement should target representation quality before any reranker is added.

---

## 6. Recommended Immediate Sequence
Recommended next sequence:

1. read `outputs/eval/control_candidate_baseline/comparison.json`,
2. inspect the seven candidate failures in `outputs/eval/control_candidate_baseline/caption_plus_selected_structured/results.json`,
3. compare those failures against `outputs/eval/structured_representation/captions.jsonl`,
4. improve person-name, exact visible-text, and UI-state representation fidelity,
5. rerun the fixed control/candidate comparison,
6. decide whether lightweight reranking is still justified.

---

## 7. Files To Read First In The Next Session
Read in this order:

1. `GLOBAL.md`
2. `docs/00_project_planning.md`
3. `docs/01_problem_definition.md`
4. `docs/02_architecture.md`
5. `docs/status/now.md`
6. `docs/status/just_finished.md`
7. `docs/logs/README.md`

Then inspect:
- `docs/03_design_decisions.md` if it exists
- `docs/05_report_context.md` if it exists
- relevant `docs/skills/*.md`

---

## 8. Current Constraints
Important current constraints:

- do not overengineer before the baseline exists,
- do not mix services, storage, and orchestration logic,
- do not lose report-writing context,
- do not skip logging updates,
- do not place secrets into docs or logs,
- do not let implementation outrun project structure,
- keep one immediate task in focus at a time.

---

## 9. Current Risks
Main current risks:

### Risk 1: Jumping Into Coding Too Early
If code starts before repository structure is stabilized, the project may grow messily.

### Risk 2: Losing Context Between Sessions
If status/handoff files are not updated, future work will slow down and repeat prior thinking.

### Risk 3: Baseline Without Evaluation
If the baseline is built without evaluation planning, later improvement will become vague.

### Risk 4: Premature Advanced Features
Adding hybrid retrieval or vector indexing too early may reduce clarity.

---

## 10. Can Be Ignored For Now
The following can be ignored for now:
- large-scale vector database infrastructure,
- advanced UI,
- production deployment,
- user accounts,
- distributed serving,
- full reranking pipeline,
- direct image embeddings if they complicate the baseline too early.

These are future-improvement topics, not immediate blockers.

---

## 11. Handoff Summary
The project is well planned but still early in implementation.
The next session should not rethink the project from scratch.

The next session should:
- trust the existing planning,
- use the established document hierarchy,
- build on the completed caption, embedding, and retrieval baselines,
- build on the successful user-image run,
- use the prompt-fidelity benchmark before redesigning retrieval,
- prioritize representation-side improvements over ranking changes,
- keep `caption_only` as a control while testing `caption_plus_selected_structured` as the candidate default,
- treat lightweight reranking as deferred until after another representation-fidelity pass,
- use explicit embedding paths or `--representation-mode` when comparing retrieval modes,
- use the root `DESIGN.md` for future UI work,
- preserve milestone history in `docs/logs/`,
- keep logs updated throughout.

The project should now move from configurable candidate baseline toward broader validation.
