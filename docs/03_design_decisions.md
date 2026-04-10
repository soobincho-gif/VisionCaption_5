# 03 Design Decisions

## Decision 001
### Title
Start with a caption-based retrieval baseline

### Date
YYYY-MM-DD

### Status
Accepted

### Context
The project goal is to retrieve the most relevant image from a prepared image set using a user's natural-language query.

A stronger multimodal retrieval design is possible, but the first implementation must remain:
- simple,
- explainable,
- aligned with the assignment,
- easy to debug,
- easy to extend.

### Options Considered
#### Option A
Start with caption-based retrieval:
- image -> vision caption
- caption -> embedding
- query -> embedding
- similarity search

#### Option B
Start directly with a hybrid multimodal retrieval system:
- caption embeddings
- image embeddings
- metadata signals
- reranking

#### Option C
Start with keyword-based metadata retrieval only

### Chosen Option
Option A: caption-based retrieval baseline

### Why
This option best matches the current assignment requirements and gives a clear, inspectable first system.
It also provides a stable reference point for later improvement.

### Benefits
- simple implementation path,
- human-readable intermediate output,
- easy qualitative inspection,
- low initial architectural complexity,
- strong compatibility with report writing.

### Tradeoffs
- visual information is compressed into text,
- caption quality directly affects retrieval quality,
- some fine-grained image cues may be lost.

### Revisit Later?
Yes.
Revisit after the baseline retrieval and first evaluation pass are complete.

---

## Decision 002
### Title
Keep repository documentation and logs as first-class project assets

### Date
YYYY-MM-DD

### Status
Accepted

### Context
This project is expected to evolve through multiple iterations.
Without explicit project memory, future sessions may repeat reasoning, lose context, or introduce architecture drift.

### Options Considered
#### Option A
Minimal documentation, mostly code-driven workflow

#### Option B
Structured documentation hierarchy with handoff/status system

### Chosen Option
Option B: structured documentation hierarchy

### Why
This supports:
- continuity across sessions,
- report-ready context accumulation,
- design decision traceability,
- lower confusion during future iterations,
- smoother collaboration with future AI or human contributors.

### Benefits
- better long-term clarity,
- easier reporting,
- easier debugging of design changes,
- better task continuity.

### Tradeoffs
- slightly higher documentation overhead,
- requires discipline to keep updated.

### Revisit Later?
No.
This is a stable operating principle.

---

## Decision 003
### Title
Separate services, pipelines, storage, and CLI from the beginning

### Date
YYYY-MM-DD

### Status
Accepted

### Context
Small prototype projects often become hard to maintain when API calls, ranking logic, storage, and command-line handling are mixed together.

### Options Considered
#### Option A
Fast prototype with mixed responsibilities

#### Option B
Modular architecture from the start:
- services
- pipelines
- storage
- config
- CLI

### Chosen Option
Option B: modular architecture from the start

### Why
The goal is not just to make the code run once.
The goal is to preserve clarity and future extensibility.

### Benefits
- easier testing,
- easier replacement of components,
- lower risk of spaghetti code,
- easier scaling to evaluation and future upgrades.

### Tradeoffs
- slightly more setup before coding,
- more files early on.

### Revisit Later?
No.
This is a structural rule.

---

## Decision 004
### Title
Use brute-force similarity first, then consider vector indexing later

### Date
YYYY-MM-DD

### Status
Accepted

### Context
The initial image set is expected to be small enough for direct similarity comparison.
Adding vector indexing too early may create unnecessary complexity.

### Options Considered
#### Option A
Brute-force similarity over all stored embeddings

#### Option B
Introduce vector indexing immediately

### Chosen Option
Option A: brute-force similarity first

### Why
For a small or medium image collection, brute-force comparison is:
- simple,
- transparent,
- easy to debug,
- good enough for the baseline.

### Benefits
- minimal infrastructure,
- easy correctness checking,
- fewer moving parts early.

### Tradeoffs
- may become slower as dataset size grows,
- not ideal for large-scale search.

### Revisit Later?
Yes.
Revisit if image volume grows or retrieval latency becomes meaningful.

---

## Decision 005
### Title
Treat evaluation as an early subsystem, not a late add-on

### Date
YYYY-MM-DD

### Status
Accepted

### Context
Without evaluation, improvement decisions become subjective.
The project should measure whether caption changes or retrieval changes actually improve outcomes.

### Options Considered
#### Option A
Build system first, evaluate much later

#### Option B
Define evaluation structure early, even if the benchmark starts small

### Chosen Option
Option B: early evaluation structure

### Why
This allows later iterations to be evidence-based instead of intuition-only.

### Benefits
- measurable progress,
- better experiment quality,
- easier comparison of design changes,
- stronger report content.

### Tradeoffs
- some documentation overhead appears earlier in the project lifecycle,
- evaluation structure must be maintained even before the benchmark is complete.

### Revisit Later?
No.
This should remain a stable working principle.

---

## Decision 006
### Title
Adopt a `DESIGN.md` workflow inspired by `awesome-design-md`

### Date
2026-04-09

### Status
Accepted

### Context
The project will eventually need a UI, and the user explicitly requested that design direction should follow the `VoltAgent/awesome-design-md` style of root-level `DESIGN.md` guidance.

### Options Considered
#### Option A
Keep a minimal visual note with only a few color bullets

#### Option B
Maintain a project-specific `DESIGN.md` that AI agents can use directly

### Chosen Option
Option B: maintain a project-specific `DESIGN.md`

### Why
This keeps design intent readable by both humans and coding agents, preserves consistency across future UI work, and aligns with the user's requested workflow.

### Benefits
- stronger agent-readable design guidance,
- less chance of generic UI output,
- clearer visual rationale for future reporting.

### Tradeoffs
- requires occasional maintenance as the UI direction becomes more concrete,
- can drift if future implementation ignores the document.

### Revisit Later?
Yes.
Refine once the first real frontend surface exists.

---

## Decision 007
### Title
Centralize milestone logs in a dedicated report-oriented folder

### Date
2026-04-09

### Status
Accepted

### Context
The user requested that plans, solved items, and changed items be organized in one folder so the material can later support reporting.

### Options Considered
#### Option A
Rely only on `docs/status/` and handoff files

#### Option B
Keep status files for the live state and add a dedicated `docs/logs/` archive for milestone history

### Chosen Option
Option B: add `docs/logs/`

### Why
Status files are excellent for the current state, but they are not ideal as a durable milestone archive. A separate log folder makes later reconstruction easier.

### Benefits
- report-friendly milestone history,
- easier reconstruction of implementation phases,
- cleaner separation between "current status" and "historical record".

### Tradeoffs
- introduces another documentation surface that must be updated deliberately,
- risks duplication if updates become careless.

### Revisit Later?
No.
This is now part of the project's operating method.

### Tradeoffs
- requires some upfront benchmark preparation.

### Revisit Later?
No.
Evaluation should remain a first-class concern.

---

## Decision 006
### Title
Preserve report-writing context during development

### Date
YYYY-MM-DD

### Status
Accepted

### Context
Technical projects often lose the reasoning behind design choices.
Later, when writing the report, important rationale must be reconstructed from memory.

### Options Considered
#### Option A
Write the report at the end from memory

#### Option B
Continuously accumulate report-ready context during development

### Chosen Option
Option B: preserve report context continuously

### Why
This reduces information loss and makes the report more accurate, nuanced, and easier to produce.

### Benefits
- better final writeup quality,
- preserved design rationale,
- clearer explanation of tradeoffs,
- easier future presentation prep.

### Tradeoffs
- requires steady note maintenance.

### Revisit Later?
No.
This should remain part of the operating workflow.

---

## Open Decisions To Revisit Later

### Future Decision A
Whether to add structured metadata fields beyond a single caption

### Future Decision B
Whether to support direct image embeddings

### Future Decision C
Whether to add a reranking stage

Current judgment on 2026-04-10:
- Do not implement reranking yet.
- The fixed control/candidate rerun shows a rerank signal because every remaining candidate top-1 miss still has the expected image in top-3.
- The next step is still representation fidelity, because the failures cluster around person-name and visible-text cues.
- Revisit lightweight reranking only after a representation-fidelity pass, and only if top-3 remains correct while top-1 is still frequently wrong.

### Future Decision D
Whether to add user relevance feedback

### Future Decision E
Whether to move from file-based storage to a vector database or FAISS-like index
