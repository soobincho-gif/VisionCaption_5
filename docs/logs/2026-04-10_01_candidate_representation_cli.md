# Candidate Representation CLI

## Objective
Promote `caption_plus_selected_structured` to a candidate-baseline embedding representation while keeping `caption_only` as a clean control.

## Why This Task Mattered
The hard benchmark showed that `caption_plus_selected_structured` improved hard-case Recall@1, family-confusion Recall@1, and hard-negative behavior compared with `caption_only`. The next step was to make representation selection explicit and reproducible in the normal indexing flow, rather than leaving it only inside evaluation code.

## Plan
1. Keep representation-building logic centralized in `src/core/representation.py`.
2. Add a CLI-level `--representation-mode` option for embedding/indexing.
3. Store the chosen mode in each `EmbeddingRecord`.
4. Separate embedding outputs by representation mode or by explicit output path.
5. Validate both modes on the current hard benchmark artifacts.

## What Was Implemented
- Added indexing representation constants:
  - `caption_only`
  - `caption_plus_selected_structured`
- Added mode normalization for legacy representation names.
- Added `Settings.embedding_output_path_for_mode()` for convention-based mode-specific embedding paths.
- Updated `run_embedding_pipeline()` to normalize and log representation mode, and to default to mode-specific output paths when no store is injected.
- Updated `src/cli/index_images.py` with:
  - `--representation-mode`
  - `--caption-path`
  - `--embedding-output-path`
  - `--image-dir`
- Updated `src/cli/query_images.py` with:
  - `--representation-mode`
  - `--caption-path`
  - `--embedding-path`
- Added `tests/test_representation.py` to protect the control representation, candidate representation, legacy mode normalization, and unsupported-mode errors.

## What Changed
The candidate representation is now available through the same embedding pipeline as the control. The CLI rejects unsupported representation values cleanly, and embedding summaries include:
- representation mode,
- number of caption records available,
- number skipped,
- number selected,
- number written,
- output path,
- errors.

## Validation
Compilation:
- `python -m compileall src`

Unit tests:
- `python -m pytest`: 4 passed

CLI checks:
- `python -m src.cli.index_images --help`
- `python -m src.cli.query_images --help`
- `python -m src.cli.index_images --stage embeddings --representation-mode not_a_mode`

Regenerated hard-benchmark embeddings:
- `outputs/embeddings/benchmark.caption_only.jsonl`
- `outputs/embeddings/benchmark.caption_plus_selected_structured.jsonl`

Run summaries:
- `caption_only`: 12 available, 0 skipped, 12 written, 0 errors, 1536 dimensions
- `caption_plus_selected_structured`: 12 available, 0 skipped, 12 written, 0 errors, 1536 dimensions

Record-level check:
- Both output files contain 12 JSONL rows.
- Records include the expected `representation_mode`.
- Candidate records use a combined source text beginning with `caption:` followed by selected structured fields.

Retrieval sanity query:
`vertical beige interface with AWAITING IMAGE SEQUENCE and Your story will appear here`

Result:
- `caption_only` ranked `visual_storytelling_dashboard` first and `visual_storytelling_mobile` second.
- `caption_plus_selected_structured` ranked `visual_storytelling_mobile` first and `visual_storytelling_dashboard` second.

## Remaining Issues
- The candidate mode is not yet a permanent production default.
- The current validation still depends on a small curated hard benchmark.
- The plain query command without explicit mode/path still preserves the legacy default embedding store for backward compatibility.

## Next Task
Run a broader mixed real-photo/UI sanity evaluation using both representation modes, then decide whether `caption_plus_selected_structured` should become the normal default retrieval representation.
