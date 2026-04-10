# 00 Project Planning

## 1. Project Title
Semantic Image Retrieval from Natural-Language Query

---

## 2. Project Summary
This project aims to build a Python-based image retrieval system that returns the most relevant image from a prepared image collection based on a user's text query.

The baseline idea is simple:
1. generate a textual description for each image using a vision-capable model,
2. store those descriptions,
3. convert image descriptions into embeddings,
4. convert the user query into an embedding,
5. compare similarity between embeddings,
6. return the top matching image or top-k images.

This creates a semantic search system that does not depend on manual tagging or meaningful file names.

---

## 3. Problem Definition

### 3.1 Core Problem
Images are difficult to search when:
- they do not have meaningful filenames,
- they are not manually tagged,
- the user's language does not match the stored metadata,
- visual meaning is richer than simple keyword labels.

A user may search for:
- "sunset in nature"
- "cute dog in a park"
- "busy city skyline at night"

but the actual file may be named:
- `IMG_0193.jpg`
- `photo2.png`
- `final_image.png`

Traditional keyword matching fails in this situation.

### 3.2 Target Problem to Solve
The project solves this by mapping both:
- image meaning,
- user query meaning

into a comparable semantic space.

Instead of matching words literally, the system matches meaning.

---

## 4. User Pain Points

### 4.1 No Manual Tags
Most image collections are not consistently labeled.

### 4.2 File Names Are Useless
Auto-generated filenames are not helpful for retrieval.

### 4.3 User Language and Metadata Differ
Users describe images in their own language, style, or level of detail.

### 4.4 Visual Meaning Gets Lost Easily
Some important image properties such as mood, composition, atmosphere, and context are hard to capture with a single simple label.

### 4.5 Scalability of Manual Organization
As the number of images grows, manual tagging becomes inefficient.

---

## 5. Project Goal

### 5.1 Immediate Goal
Build a working semantic image retrieval system in Python that:
- accepts a user's text query,
- compares it against prepared image representations,
- returns the most relevant image,
- optionally returns the top 3 matches.

### 5.2 Broader Goal
Design the project so it can later evolve into a stronger multimodal retrieval system with:
- structured metadata,
- direct image embeddings,
- reranking,
- vector indexing,
- evaluation metrics,
- better explainability.

---

## 6. What We Are Building

### 6.1 Baseline System
A baseline caption-based retrieval pipeline:

`Images -> vision caption generation -> caption storage -> caption embeddings -> query embedding -> similarity search -> top result(s)`

### 6.2 Improved System Direction
A stronger hybrid system:

`Images -> caption generation + structured metadata + optional direct image embedding -> hybrid ranking -> reranking -> evaluated results`

The baseline is the submission-safe implementation.
The improved system is the architecture-aware extension path.

---

## 7. Project Scope

### 7.1 In Scope
- image collection indexing,
- automatic caption generation,
- caption storage,
- embedding generation,
- query embedding,
- similarity computation,
- top-1 or top-k retrieval,
- clean modular Python implementation,
- experiment logging,
- evaluation planning,
- report-ready documentation.

### 7.2 Out of Scope for Initial MVP
- large-scale production search engine,
- full web search,
- real-time streaming ingestion,
- advanced UI,
- user accounts,
- distributed vector infrastructure,
- training a custom vision-language model from scratch.

---

## 8. Baseline Architecture Plan

### 8.1 Offline Indexing Phase
This phase prepares the searchable representation of the image collection.

Steps:
1. read all images from a prepared folder,
2. send each image to a vision-capable model,
3. generate a descriptive caption,
4. save caption results,
5. embed each caption,
6. store embeddings and metadata for retrieval.

### 8.2 Online Query Phase
This phase handles user search.

Steps:
1. accept a user text query,
2. embed the query,
3. compare query embedding against stored image-caption embeddings,
4. rank results by similarity,
5. return top-1 or top-k image matches.

---

## 9. Why This Baseline First
The caption-based baseline is the best first step because it is:
- simple,
- easy to explain,
- directly aligned with the assignment requirement,
- fast to implement,
- easy to debug,
- modular enough for future upgrades.

It also creates a clean comparison point for later improvements.

---

## 10. Baseline Limitations
The baseline is intentionally useful but imperfect.

Main limitations:
- caption quality strongly affects retrieval quality,
- some visual details may be lost when compressed into text,
- atmosphere, layout, and fine-grained visual cues may be underrepresented,
- ranking may be shallow without reranking,
- similarity search may be brute-force at first.

These limitations justify future improvement work.

---

## 11. Planned Improvement Directions

### 11.1 Structured Metadata
Instead of storing only one caption string, also extract fields such as:
- scene,
- objects,
- style,
- color,
- mood,
- special attributes.

This improves interpretability and future filtering.

### 11.2 Direct Image Embeddings
If supported by the toolchain, represent images directly in embedding space rather than relying only on captions.

This may reduce information loss caused by text compression.

### 11.3 Hybrid Ranking
Combine multiple signals:
- caption similarity,
- direct image similarity,
- metadata matches,
- optional reranker score.

### 11.4 Reranking
Retrieve an initial top-k candidate set, then run a stronger matching pass to improve the final ranking order.

### 11.5 Vector Indexing
Move from brute-force similarity calculation toward vector indexing when dataset size grows.

### 11.6 User Feedback Loop
Allow relevance feedback such as:
- correct,
- not correct,
- similar but not exact.

This would support iterative retrieval improvement.

---

## 12. Evaluation Plan

### 12.1 Why Evaluation Matters
The system should not only “run”.
It should demonstrate retrieval quality.

### 12.2 Initial Evaluation Approach
Create a small benchmark set:
- image collection,
- test queries,
- expected correct image or acceptable top-k target set.

### 12.3 Candidate Metrics
- Recall@1
- Recall@3
- MRR
- qualitative error analysis

### 12.4 Evaluation Purpose
Evaluation will be used to compare:
- baseline caption prompt variants,
- different embedding strategies,
- whether structured metadata helps,
- whether reranking improves final relevance.

---

## 13. Implementation Roadmap

### Phase 0: Repository Setup
- set up folder structure,
- establish documentation hierarchy,
- define schemas and config structure,
- create logging/status framework.

### Phase 1: Baseline Caption Pipeline
- load images,
- generate captions,
- save caption outputs.

### Phase 2: Embedding Pipeline
- embed image captions,
- store embeddings and metadata.

### Phase 3: Search Pipeline
- accept query,
- embed query,
- compute similarity,
- return ranked results.

### Phase 4: Evaluation Layer
- prepare test queries,
- measure retrieval quality,
- record strengths and failure cases.

### Phase 5: Improvement Loop
- refine captions,
- add metadata,
- add reranking,
- test hybrid designs,
- compare results.

---

## 14. Repository Design Principles for This Project
The repository must remain clean and modular.

### Required separation:
- caption generation logic,
- embedding logic,
- retrieval logic,
- ranking logic,
- storage logic,
- evaluation logic,
- CLI / execution layer.

### Required project habits:
- keep configs centralized,
- avoid hardcoding,
- preserve design rationale,
- log meaningful experiments,
- update handoff and status files after meaningful work.

---

## 15. Deliverables

### Minimum Deliverable
A working Python program that:
- processes prepared images,
- generates image captions,
- embeds captions,
- embeds a text query,
- returns the best matching image.

### Better Deliverable
A program that:
- returns top-3 results,
- stores captions and embeddings cleanly,
- supports repeatable evaluation,
- logs experiments and design choices.

### Strong Project Deliverable
A modular retrieval system with:
- clean architecture,
- evaluation results,
- documented limitations,
- improvement roadmap,
- report-ready context.

---

## 16. Success Criteria

### Technical Success
- the program runs end-to-end,
- retrieval works for reasonable test queries,
- outputs are stored cleanly,
- modules are separated properly.

### Project Success
- the system is understandable,
- the architecture is extensible,
- the repository avoids spaghetti growth,
- context is preserved for future work,
- the project is easy to explain in a report or presentation.

---

## 17. Main Risks

### 17.1 Weak Captions
If the captions are vague or inconsistent, retrieval quality drops.

### 17.2 Overly Tight Coupling
If captioning, retrieval, storage, and execution are mixed together, future improvement becomes expensive.

### 17.3 No Evaluation Memory
Without experiment logs and evaluation benchmarks, progress becomes hard to measure.

### 17.4 Premature Overengineering
If advanced retrieval features are added too early, the project may become harder to debug and slower to stabilize.

---

## 18. Planning Decision Summary
Current planning decisions:

- Start with a caption-based retrieval baseline.
- Keep the codebase modular from day one.
- Treat documentation and logs as part of implementation.
- Preserve report-writing context continuously.
- Improve through loops: build -> evaluate -> redesign -> patch -> log.
- Use the baseline as a stable reference point for later improvements.

---

## 19. Immediate Next Step
The next best step is:

1. finalize the repository structure,
2. create the initial documentation and status files,
3. define the baseline code modules,
4. then implement the caption indexing pipeline.

This keeps the project stable before major coding begins.
