# 2026-04-09 Real Sample Retrieval Run

## Objective
Run the full baseline pipeline on real local sample images and inspect the first actual retrieval outcomes.

## Why This Mattered
The retrieval path had been implemented, but until real images, captions, embeddings, and queries existed together, the project still lacked an end-to-end baseline run.

## Sample Images Used
- `data/raw/raccoon_business.png`
- `data/raw/student_dog.png`
- `data/raw/dashboard_storytelling.png`

These were copied from outside the project after explicit user approval to use local images beyond the project docs or repository assets.

## Pipeline Execution
1. Ran caption indexing on the three sample images.
2. Ran embedding indexing on the resulting caption records.
3. Ran qualitative retrieval queries through the baseline CLI.

## Artifact Summary
- Caption indexing:
  - images discovered: 3
  - captions written: 3
- Embedding indexing:
  - captions available: 3
  - embeddings written: 3
  - embedding dimensions: 1536

## Retrieval Queries And Outcomes

### Query
`animal in a business suit with briefcase`

### Top Result
`raccoon_business`

### Interpretation
Strong match. The stored caption preserved the important retrieval cues.

---

### Query
`cute dog student with backpack and books`

### Top Result
`student_dog`

### Interpretation
Strong match. The baseline works well for simple object-centric character images.

---

### Query
`dark dashboard showing storytelling or sentiment analysis summary`

### Top Result
`raccoon_business`

### Interpretation
Failure case. The screenshot-like image was captioned incorrectly, so retrieval followed the stored caption rather than the underlying image content.

---

### Query
`cats indoors and a child lying outside with blanket`

### Top Result
`dashboard_storytelling`

### Interpretation
This confirms the retrieval path is mathematically consistent with the stored representations. The problem is the caption bottleneck, not the cosine ranking logic.

## What Changed
- The project now has a true local end-to-end baseline run.
- The first meaningful failure mode is now explicit and documented.

## Remaining Issues
- The sample set is tiny.
- Caption quality is not robust for every image type.
- Retrieval quality should not yet be generalized from this run.

## Next Task
Refine the caption prompt for difficult image categories and expand the handwritten query set for a larger qualitative review.
