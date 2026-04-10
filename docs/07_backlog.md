# 07 Backlog

## Purpose of This File
This file stores prioritized future work.
It should help the project move in an ordered way rather than through random idea accumulation.

Tasks are organized by priority:
- P0 = immediate / critical
- P1 = next after baseline setup
- P2 = important but not urgent
- P3 = long-term or optional

---

## P0 — Immediate / Critical

### P0-1
Create the real repository folder structure

#### Why
Planning is complete, but implementation should not start without a stable structure.

#### Target Outputs
- `src/` subfolders
- `docs/status/` files
- starter Python files
- missing core docs

---

### P0-2
Define core schemas for:
- caption records
- embedding records
- retrieval results

#### Why
The project needs explicit internal data contracts before multiple components are implemented.

#### Target Outputs
- `src/core/schemas.py`
- optional `src/core/types.py`

---

### P0-3
Create baseline config files

#### Why
Model names, paths, prompts, and output settings should not be scattered.

#### Target Outputs
- `src/config/settings.py`
- `src/config/prompts.py`

---

### P0-4
Implement image loading + caption indexing pipeline

#### Why
This is the first true functional baseline step.

#### Target Outputs
- image loading flow
- vision caption calls
- caption storage

---

### P0-5
Implement caption embedding generation and storage

#### Why
Captions must be converted into searchable representations.

#### Target Outputs
- embedding generation
- embedding persistence
- image-to-caption-to-embedding linkage

---

### P0-6
Implement query search pipeline

#### Why
This completes the end-to-end baseline system.

#### Target Outputs
- query embedding
- similarity computation
- top-k ranking
- retrieval output

---

## P1 — Baseline Completion and First Evaluation

### P1-1
Create initial evaluation query set

#### Why
The project needs a small benchmark to measure usefulness.

---

### P1-2
Implement evaluation pipeline

#### Why
Retrieval quality must be measurable.

#### Candidate Metrics
- Recall@1
- Recall@3
- MRR
- qualitative review

---

### P1-3
Inspect caption quality failures

#### Why
Some retrieval errors will likely come from weak captioning rather than ranking.

---

### P1-4
Decide whether top-3 should be the default output

#### Why
Top-1 may be too brittle early on.

---

## P2 — Improvement Work

### P2-1
Improve caption prompt quality

### P2-2
Compare short captions vs richer captions

### P2-3
Add structured metadata extraction
Possible fields:
- scene
- objects
- mood
- color
- style

### P2-4
Add reranking stage

### P2-5
Improve result explainability
Possible outputs:
- matched caption
- similarity score
- why this result may have matched

---

## P3 — Advanced / Future Work

### P3-1
Test direct image embeddings

### P3-2
Move to hybrid ranking

### P3-3
Introduce vector indexing for scale

### P3-4
Add user relevance feedback loop

### P3-5
Build UI or demo interface

### P3-6
Package as a cleaner reusable toolkit

---

## Deferred / Optional Ideas

### Idea A
Compare multiple caption prompt styles

### Idea B
Store multiple captions per image

### Idea C
Add multilingual query support explicitly

### Idea D
Compare multiple embedding models if available

### Idea E
Generate error-analysis visualization

---

## Backlog Management Rules

1. Do not pull P2 or P3 work forward before the baseline is stable unless there is a strong reason.
2. When a task is started, reflect that in `docs/status/now.md`.
3. When a task is completed, move its result into `docs/status/just_finished.md`.
4. If a task becomes irrelevant, move it to `docs/status/archived_or_ignore.md`.
5. If a completed task leads to new report insight, update `docs/05_report_context.md`.

---

## Current Priority Summary
Current highest-priority sequence:

1. repository skeleton
2. core schemas
3. config setup
4. caption indexing pipeline
5. embedding pipeline
6. query search
7. first evaluation setup
