# 2026-04-09 Caption Indexing Baseline

## Objective
Implement the first clean baseline caption indexing flow.

## Why This Mattered
Caption generation is the first working vertical slice in the project and exercises the core separation between service logic, orchestration, and persistence.

## Plan
1. Finalize core schemas.
2. Implement image discovery.
3. Wire the vision caption service to the OpenAI API.
4. Persist caption records via a JSONL store.
5. Update docs to reflect the new project state.

## What Was Implemented
- `CaptionRecord`, `EmbeddingRecord`, and `RetrievalResult` schemas were formalized.
- Recursive image discovery and stable `image_id` generation were added.
- `VisionCaptionService` was wired to a real OpenAI multimodal call.
- `CaptionStore` gained clean JSONL save and load behavior.
- The caption pipeline now orchestrates discovery, generation, persistence, and summary reporting.

## What Changed
- The caption stage moved from scaffold to working implementation.
- `index_images.py` now prints structured stage summaries.
- Status, experiment, and handoff documents were updated around the caption milestone.

## Validation
- Code compiled successfully.
- The caption CLI returned a valid `no_images_found` summary against the empty local dataset.
- A fake client smoke test verified service and store boundaries.

## Remaining Issues
- The local dataset is still empty, so no real caption artifacts have been generated.
- The pipeline still depends on a valid OpenAI key and local images.

## Next Task
Implement caption embedding generation and storage.
