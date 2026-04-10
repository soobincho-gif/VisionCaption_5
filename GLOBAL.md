# GLOBAL

## 1. Purpose of This Repository
This repository is operated as a clean, extensible, report-ready project system.

The immediate project is a semantic image retrieval system that finds the most relevant image from a prepared image collection based on a user's natural-language query.

This repository must support:
- clean implementation,
- iterative experimentation,
- context continuity across sessions,
- future reporting and presentation,
- smooth handoff to future AI or human collaborators.

---

## 2. Repository Philosophy
This repository is not just a place to store code.
It is a working system with four equally important layers:

1. Code
2. Documentation
3. Logs / status memory
4. Report-ready design context

A task is not complete unless all relevant layers remain coherent.

---

## 3. Non-Negotiable Rules

### 3.1 Separation of Concerns
Do not mix unrelated responsibilities.

Keep these concerns separate:
- configuration,
- prompt design,
- API calling,
- business logic,
- orchestration,
- storage,
- evaluation,
- CLI entrypoints.

Preferred structure:
- `src/config`: settings and prompts
- `src/core`: schemas, types, shared utilities
- `src/services`: isolated logic units
- `src/pipelines`: orchestration flows
- `src/storage`: persistence and file/database access
- `src/cli`: runnable entrypoints
- `docs/`: planning, design memory, reporting context
- `tests/`: validation

### 3.2 No Spaghetti Code
The following are prohibited:
- god files,
- oversized functions with multiple responsibilities,
- hidden global state,
- hardcoded paths or magic values scattered across files,
- silent architecture drift,
- duplicated logic,
- experimental code mixed into stable code paths without boundaries,
- undocumented shortcuts.

### 3.3 Small, Clean Steps
Always prefer a small, modular, testable change over a large unclear change.

Baseline first.
Then evaluate.
Then redesign if needed.
Then patch.
Then document what was learned.

### 3.4 Documentation Is Part of the Work
Documentation is not optional cleanup at the end.
If implementation changes, documentation and logs must also change.

### 3.5 Report-Aware Development
Whenever a meaningful decision is made, preserve context that may later be needed for:
- reports,
- presentations,
- architecture explanations,
- experiment comparisons,
- limitations,
- future work discussions.

That context belongs in `docs/05_report_context.md`.

---

## 4. Working Loop
Every meaningful task should follow this loop:

1. Read current context.
2. Identify exactly one immediate task.
3. Explain why this task is next.
4. Implement or revise.
5. Evaluate the result.
6. Patch or redesign if necessary.
7. Update docs and logs.
8. Define the next best task.

Do not stop at “done”.
Always leave the repository in a handoff-ready state.

---

## 5. Required Reading Order Before Meaningful Work
Before making substantial changes, read these files in order:

1. `GLOBAL.md`
2. `docs/06_handoff.md`
3. `docs/status/now.md`
4. `docs/status/just_finished.md`
5. relevant files in `docs/skills/`
6. relevant files in `docs/02_architecture.md`, `docs/03_design_decisions.md`, and `docs/05_report_context.md`

If required context files do not exist, create them first before doing major implementation work.

---

## 6. Documentation Hierarchy

### `docs/00_project_planning.md`
Stores project planning, scope, roadmap, and high-level solution strategy.

### `docs/01_problem_definition.md`
Stores the problem framing, user pain points, and why the project matters.

### `docs/02_architecture.md`
Stores architecture, data flow, module boundaries, and system responsibilities.

### `docs/03_design_decisions.md`
Stores major design choices, alternatives considered, tradeoffs, and revisit notes.

### `docs/04_experiment_log.md`
Stores experiments, what changed, how it was evaluated, and what was learned.

### `docs/05_report_context.md`
Stores report-ready context such as:
- why this architecture was chosen,
- what limitations were discovered,
- what improvements are justified,
- how to explain results later.

### `docs/06_handoff.md`
Stores the current project state, what was just completed, and what should happen next.

### `docs/07_backlog.md`
Stores prioritized future work.

### `docs/status/now.md`
Stores only what is actively in progress now.

### `docs/status/just_finished.md`
Stores work that was recently completed and still matters.

### `docs/status/next_up.md`
Stores the next recommended tasks.

### `docs/status/archived_or_ignore.md`
Stores outdated, rejected, replaced, or currently irrelevant context.

### `docs/skills/*.md`
Stores reusable operational knowledge for subsystem-specific work.

---

## 7. Context Classification Rules
Continuously classify project context into three buckets:

### Currently Active
Use `docs/status/now.md`
- tasks in progress,
- current blockers,
- the immediate focus.

### Just Finished
Use `docs/status/just_finished.md`
- recently completed changes,
- recently learned insights,
- still-relevant outcomes.

### Archived / Ignore
Use `docs/status/archived_or_ignore.md`
- replaced ideas,
- discarded experiments,
- outdated assumptions,
- things that no longer require active attention.

This classification must be maintained to reduce context clutter.

---

## 8. Logging Rules
Every meaningful task must update:
- `docs/status/now.md`
- `docs/status/just_finished.md`
- `docs/06_handoff.md`

Update additional files when needed:
- `docs/03_design_decisions.md` if design direction changed
- `docs/04_experiment_log.md` if an experiment was run
- `docs/05_report_context.md` if reporting context was created or changed
- `docs/status/archived_or_ignore.md` if something became obsolete

---

## 9. Code Quality Rules

### 9.1 Config
All adjustable values should live in config, not be scattered through code.

Examples:
- model names,
- thresholds,
- file paths,
- prompt parameters,
- output locations.

### 9.2 Interfaces
Each module should have explicit inputs and outputs.
Where helpful, use schemas or typed structures.

### 9.3 Reuse
Before creating a new file or function, inspect whether existing structure can be extended cleanly.

### 9.4 Testability
Prefer code that can be unit tested without running the full pipeline.

### 9.5 Reproducibility
Important pipeline outputs should be stored in stable locations and be reproducible from source inputs and config.

---

## 10. First-Time Setup Policy
If the repository is still immature or incomplete, first stabilize:
1. folder structure,
2. documentation hierarchy,
3. logging structure,
4. project context,
5. baseline architecture notes.

Only then proceed to larger implementation steps.

---

## 11. Project-Specific Development Principle
For the image retrieval project, prefer this sequence:

1. clean baseline,
2. evaluation,
3. redesign based on evidence,
4. improved version,
5. report-ready interpretation.

Do not jump into advanced architecture before the baseline is working and understandable.

---

## 12. Definition of a Successful Work Session
A successful work session does not only produce working code.
It must also:
- fit the current architecture,
- avoid technical clutter,
- preserve project memory,
- reduce ambiguity for the next session,
- make reporting easier later.

If code works but context is lost, the task is incomplete.
