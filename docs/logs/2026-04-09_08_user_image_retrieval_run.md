# 2026-04-09 User Image Retrieval Run

## Objective
Run the full baseline pipeline on the four local images explicitly provided by the user and verify whether the baseline retrieval path works on those images.

## Why This Mattered
The previous real-sample run used temporary stand-in images. This run is more meaningful because it uses the user's intended local examples.

## Dataset Used
- `data/raw/cafe_phone_person.jpeg`
- `data/raw/indoor_many_cats.jpeg`
- `data/raw/outdoor_blanket_rest.jpeg`
- `data/raw/night_riverside_person.jpeg`

## Pipeline Execution
1. Cleared the earlier temporary sample files and prior generated caption/embedding JSONL outputs.
2. Copied the four user-provided images into `data/raw`.
3. Ran caption indexing.
4. Ran embedding indexing.
5. Queried the stored embeddings through the baseline retrieval CLI.

## Artifact Summary
- Images discovered: 4
- Captions written: 4
- Captions available for embedding: 4
- Embeddings written: 4
- Embedding dimension: 1536

## Captions Observed
- `cafe_phone_person`: a person in a cozy cafe looking at a phone
- `indoor_many_cats`: multiple cats gathered indoors on a wooden floor
- `outdoor_blanket_rest`: a person lying on a mat outdoors under a blanket
- `night_riverside_person`: a person standing outside at twilight with lights in the background

These baseline captions were sufficiently faithful for straightforward semantic retrieval.

## Retrieval Queries And Top Results

### Query
`man sitting in a cafe looking at his phone`

### Top Result
`cafe_phone_person`

---

### Query
`many cats gathered indoors on a wooden floor`

### Top Result
`indoor_many_cats`

---

### Query
`person lying on a mat covered with a blanket outdoors`

### Top Result
`outdoor_blanket_rest`

---

### Query
`person standing outside at night near lights`

### Top Result
`night_riverside_person`

## Interpretation
The current caption-plus-embedding baseline is working correctly for the current user-image set. For these simple representative queries, the correct image was ranked first in each case.

## What Changed
- The project now has a successful end-to-end run on user-provided local images.
- The baseline is no longer only code-complete; it has now been verified against a small relevant dataset.

## Remaining Issues
- Only one obvious query per image was tested so far.
- The dataset is still too small to support stronger claims.
- Search results are not yet persisted automatically.

## Next Task
Create a broader handwritten query set for the same four images and log how stable the rankings remain across phrasing variations.
