# 02 Architecture

## 1. Architecture Overview
This project is designed as a modular semantic image retrieval system.

The core system has two main flows:

1. Offline indexing flow
2. Online query flow

The offline flow prepares the searchable representation of the image set.
The online flow uses that prepared representation to answer user queries.

---

## 2. High-Level Architecture

### 2.1 Offline Indexing Flow
`Image files -> Vision caption generation -> Caption storage -> Caption embedding generation -> Embedding storage`

### 2.2 Online Query Flow
`User text query -> Query embedding generation -> Similarity computation -> Ranking -> Top-k image results`

This separation keeps indexing work and search work cleanly decoupled.

---

## 3. Design Goals
The architecture is designed to satisfy the following goals:

- modularity,
- readability,
- easy debugging,
- easy replacement of components,
- clean future extensibility,
- report-friendly structure,
- avoidance of spaghetti code.

---

## 4. Main Architectural Layers

### 4.1 Config Layer
Location:
- `src/config/`

Responsibility:
- centralize model names,
- prompt settings,
- file paths,
- thresholds,
- runtime options.

This prevents hardcoded values from spreading across the codebase.

---

### 4.2 Core Layer
Location:
- `src/core/`

Responsibility:
- shared schemas,
- types,
- small reusable utilities,
- core data structures.

This layer defines the project's internal contracts.

Examples:
- caption record schema,
- embedding record schema,
- retrieval result schema.

---

### 4.3 Service Layer
Location:
- `src/services/`

Responsibility:
- isolated functional logic.

Expected services:
- `vision_caption_service.py`
- `embedding_service.py`
- `similarity_service.py`
- `rerank_service.py`
- `metadata_service.py`

Each service should do one well-defined job.

Examples:
- generate caption from image,
- generate embedding from text,
- compute cosine similarity,
- optional rerank logic,
- optional metadata extraction.

---

### 4.4 Pipeline Layer
Location:
- `src/pipelines/`

Responsibility:
- orchestrate multiple services into complete workflows.

Expected pipelines:
- `build_caption_index.py`
- `build_embedding_index.py`
- `search_images.py`
- `evaluate_retrieval.py`

Pipelines should not contain low-level business logic.
They should coordinate steps using services.

---

### 4.5 Storage Layer
Location:
- `src/storage/`

Responsibility:
- save and load structured outputs.

Expected stores:
- `caption_store.py`
- `embedding_store.py`
- `result_store.py`

This layer isolates persistence from logic.

---

### 4.6 CLI Layer
Location:
- `src/cli/`

Responsibility:
- provide runnable entrypoints.

Expected CLI files:
- `index_images.py`
- `query_images.py`
- `run_eval.py`

The CLI should call pipelines, not duplicate pipeline logic.

---

## 5. Data Flow

## 5.1 Offline Indexing Data Flow
1. read image files from a configured directory,
2. pass each image to the vision caption service,
3. receive caption output,
4. write caption data to storage,
5. pass caption text to the embedding service,
6. receive embedding vector,
7. write embedding data and image linkage to storage.

Outputs from this phase:
- caption records,
- embedding records,
- image metadata links.

---

## 5.2 Online Query Data Flow
1. accept a user text query,
2. pass the query to the embedding service,
3. load stored caption embeddings,
4. compute similarity between query embedding and image caption embeddings,
5. rank all candidate images,
6. return top-1 or top-k results.

Outputs from this phase:
- ranked retrieval results,
- similarity scores,
- image references.

---

## 6. Initial Baseline Architecture

### 6.1 Baseline Retrieval Logic
The first architecture version uses caption-only retrieval.

Process:
- image -> caption
- caption -> embedding
- query -> embedding
- query embedding vs caption embedding similarity
- rank and return top results

Why this baseline:
- directly aligned with assignment requirements,
- human-readable intermediate representation,
- easy to debug,
- minimal moving parts,
- stable first comparison point.

---

## 7. Planned Improved Architecture

### 7.1 Structured Metadata Extension
In addition to the caption, the system may also store:
- scene,
- objects,
- style,
- color,
- mood,
- notable attributes.

This improves explainability and future filtering.

### 7.2 Direct Image Embedding Extension
If the toolchain supports it, images may later be embedded directly instead of relying only on generated captions.

Benefit:
- reduces information loss from text compression.

### 7.3 Hybrid Ranking
Future ranking may combine:
- caption embedding similarity,
- direct image embedding similarity,
- metadata signal,
- reranker score.

### 7.4 Reranking Stage
A later-stage architecture may:
1. retrieve top-k candidates,
2. run a stronger matching pass,
3. reorder the candidates.

This improves final precision without changing the initial retrieval stage too much.

### 7.5 Vector Indexing
When data size grows, brute-force comparison may be replaced by vector indexing.

---

## 8. Storage Strategy

### 8.1 Raw Inputs
Stored in:
- `data/raw/`
- `data/samples/`

### 8.2 Intermediate Outputs
Stored in:
- `outputs/captions/`
- `outputs/embeddings/`

### 8.3 Final Results
Stored in:
- `outputs/retrieval_results/`
- `outputs/eval/`

The architecture should preserve clear separation between:
- raw input assets,
- processed intermediate artifacts,
- evaluation results.

---

## 9. Key Data Contracts

### 9.1 Caption Record
A caption record should minimally include:
- image_id,
- image_path,
- caption_text,
- timestamp or version metadata.

### 9.2 Embedding Record
An embedding record should minimally include:
- image_id,
- source_text,
- embedding_vector,
- embedding_model,
- timestamp or version metadata.

### 9.3 Retrieval Result Record
A retrieval result should minimally include:
- query_text,
- candidate_image_id,
- similarity_score,
- ranking_position.

These contracts should be implemented in `src/core/schemas.py` or equivalent.

---

## 10. Architectural Constraints

### 10.1 No Mixed Responsibilities
Do not combine:
- API requests,
- storage writes,
- ranking logic,
- command-line handling

inside the same function unless the function is purely orchestration.

### 10.2 No Hidden State
The architecture must avoid global mutable state.

### 10.3 Replaceability
A component should be replaceable without breaking the whole system.

Examples:
- swap caption prompt,
- swap embedding model,
- swap ranking logic,
- swap storage format.

### 10.4 Reproducibility
Outputs should be reproducible from:
- input images,
- config,
- code version,
- prompts.

---

## 11. Baseline Module Map

### Config
- `src/config/settings.py`
- `src/config/prompts.py`

### Core
- `src/core/schemas.py`
- `src/core/types.py`
- `src/core/utils.py`

### Services
- `src/services/vision_caption_service.py`
- `src/services/embedding_service.py`
- `src/services/similarity_service.py`

### Pipelines
- `src/pipelines/build_caption_index.py`
- `src/pipelines/build_embedding_index.py`
- `src/pipelines/search_images.py`

### Storage
- `src/storage/caption_store.py`
- `src/storage/embedding_store.py`
- `src/storage/result_store.py`

### CLI
- `src/cli/index_images.py`
- `src/cli/query_images.py`

---

## 12. Evaluation Architecture
Evaluation should be treated as a first-class subsystem, not an afterthought.

The evaluation pipeline should:
1. load a benchmark query set,
2. run retrieval,
3. compare predicted top-k results with expected targets,
4. calculate metrics,
5. log failure cases,
6. store results in a reproducible format.

This belongs in:
- `src/pipelines/evaluate_retrieval.py`
- `outputs/eval/`
- `docs/04_experiment_log.md`

---

## 13. Known Architectural Risks

### 13.1 Caption Dependence
If captions are poor, the retrieval system weakens.

### 13.2 Early Coupling Risk
If services and pipelines are not kept separate, future improvements will become expensive.

### 13.3 Evaluation Neglect
If evaluation is delayed too long, the project may become difficult to improve systematically.

### 13.4 Premature Complexity
Adding hybrid ranking or vector indexing too early may reduce clarity before the baseline stabilizes.

---

## 14. Architecture Decision Summary
Current architecture strategy:

- use a clean caption-only baseline first,
- separate config, services, pipelines, storage, and CLI,
- preserve extensibility for metadata, image embeddings, reranking, and vector indexing,
- treat evaluation and report context as part of the architecture,
- optimize for clarity first, then sophistication.

---

## 15. Immediate Architecture Priority
The current architectural priority is:

1. finalize the repository/module structure,
2. define schemas for captions, embeddings, and retrieval results,
3. implement the caption indexing pipeline cleanly,
4. ensure outputs are stored reproducibly,
5. prepare the search pipeline after indexing is stable.
