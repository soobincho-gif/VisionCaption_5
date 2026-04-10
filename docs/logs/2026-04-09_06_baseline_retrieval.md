# 2026-04-09 Baseline Retrieval

## Objective
Implement the first simple query-time retrieval path for the semantic image retrieval baseline.

## Why This Mattered
The project already had caption and embedding preparation stages, but the user still could not issue a query and obtain ranked results. Retrieval is the smallest online slice that turns the project into an actual search system.

## Pre-Check
- Inspected `data/raw` before coding.
- Result: no local image files were present.
- Consequence: real caption and embedding artifacts could not be generated during this session.

## Plan
1. Inspect the current retrieval-related modules.
2. If sample images exist, generate fresh caption and embedding artifacts first.
3. Implement query embedding plus brute-force cosine ranking over stored caption embeddings.
4. Keep CLI output readable and keep empty-artifact handling clean.
5. Update logs and status docs.

## What Was Implemented
- `search_images.py`
  - loads stored embedding records,
  - embeds the input query,
  - filters candidate vectors to the correct dimensionality,
  - ranks candidates via brute-force cosine similarity,
  - returns ordered `RetrievalResult` objects with `image_path` when available.
- `query_images.py`
  - accepts query text,
  - accepts `--top-k`,
  - validates the `top-k` value,
  - prints ranked results in a human-readable format.

## What Changed
- Retrieval moved from scaffold status to implemented baseline code.
- Status, handoff, experiment, and log documents now reflect that retrieval exists but still lacks real sample-artifact validation.

## Validation
- `data/raw` inspection confirmed there are currently no real sample images.
- `python -m src.cli.index_images --stage all --limit 3` confirmed the repository still has no captions or embeddings locally.
- Retrieval code was validated against:
  - empty-artifact behavior,
  - synthetic temporary records and vectors,
  - CLI formatting checks.

## Remaining Issues
- The repository still lacks real indexed images.
- Retrieval quality has not been observed on real image queries yet.
- Search-result persistence remains optional and is not integrated into the baseline path.

## Next Task
Populate `data/raw`, run indexing end to end, and perform the first qualitative retrieval review on real sample images.
