# 2026-04-09 Embedding Indexing Baseline

## Objective
Implement the embedding stage cleanly for the semantic retrieval baseline.

## Why This Mattered
Embeddings are the retrieval-ready artifact that connects offline captioning to future online search.

## Plan
1. Implement a reusable embedding service using the OpenAI embeddings API.
2. Add a JSONL embedding store with explicit persistence-only responsibilities.
3. Build a pipeline that reads captions, skips existing embeddings, writes embedding records, and returns summary stats.
4. Update CLI and docs.

## What Was Implemented
- `EmbeddingService` now validates configuration and calls the OpenAI embeddings endpoint.
- `EmbeddingStore` now supports `save()`, `load_all()`, and `list_image_ids()`.
- `build_embedding_index.py` now reads caption records, skips existing IDs, generates vectors, persists `EmbeddingRecord` items, and collects error summaries.
- CLI support for the embedding stage was preserved and aligned with `--limit`.

## What Changed
- The project now has both offline baseline stages implemented.
- Summary output now distinguishes:
  - available captions,
  - already embedded captions,
  - captions selected for the current run,
  - vectors written.

## Validation
- Relevant code files compiled successfully.
- The embedding CLI returned `no_captions_found` against the current empty project outputs.
- Temporary-record and fake-client smoke tests verified service and pipeline behavior.

## Remaining Issues
- The repository still has no real caption or embedding artifacts because the local dataset is empty.
- Retrieval remains intentionally stubbed.

## Next Task
Implement baseline query retrieval with query embedding plus brute-force cosine similarity.
