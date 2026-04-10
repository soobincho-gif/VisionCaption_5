# 01 Problem Definition

## 1. Problem Statement
This project addresses the problem of retrieving the most relevant image from a prepared image collection using a user's natural-language text query.

Traditional image retrieval often depends on:
- filenames,
- manual tags,
- folder structure,
- or simple keyword metadata.

These methods break down when images are unlabeled, poorly organized, or described differently from how users think about them.

The core problem is therefore:

**How can we retrieve the most semantically relevant image when the user's description and the stored image information are not directly aligned?**

---

## 2. Why This Problem Matters
Image collections are often difficult to search in a meaningful way.
This is especially true when:
- file names are auto-generated,
- there is no manual labeling,
- users search by meaning rather than exact words,
- visual concepts are richer than simple tags.

A retrieval system that matches meaning rather than literal keywords improves usability, discoverability, and scalability.

---

## 3. Target User Situation
The target user has a set of prepared images and wants to find the image that best matches a text description.

Example queries:
- "a beautiful sunset over mountains"
- "a cute dog playing outside"
- "a busy city skyline at night"
- "a calm natural scene with warm colors"

The user may not know:
- the image filename,
- the folder structure,
- the exact words stored in metadata.

The user only knows the concept they want.

---

## 4. Core User Pain Points

### 4.1 Image Collections Are Hard to Search
Images are not inherently searchable unless they are paired with useful text.

### 4.2 Filenames Usually Carry No Meaning
Auto-generated filenames such as `IMG_1032.jpg` do not help retrieval.

### 4.3 Manual Tagging Is Expensive and Inconsistent
Even when tags exist, they are often incomplete, subjective, or inconsistent across images.

### 4.4 User Language Is Flexible, Metadata Is Rigid
A user may search for "nature sunset", while stored metadata might say "orange sky over mountain ridge".

### 4.5 Visual Meaning Exceeds Simple Labels
Important visual qualities such as:
- mood,
- composition,
- context,
- atmosphere,
- style,
- relative object position

are difficult to capture with a few keywords.

---

## 5. Existing Baseline Limitation
A naive keyword-based image search system has major weaknesses:
- it depends on exact matches,
- it fails when no metadata exists,
- it cannot handle semantic variation,
- it does not understand visual meaning.

This makes traditional search insufficient for flexible natural-language retrieval.

---

## 6. Proposed Problem Framing
The retrieval problem should be framed as a semantic matching problem, not a filename or tag lookup problem.

We want to transform both:
- image meaning,
- query meaning

into a shared comparable representation.

The project therefore treats image retrieval as a semantic similarity problem.

---

## 7. Project-Level Objective
The immediate objective is to create a Python program that:
1. generates text descriptions for images using a vision-capable model,
2. stores those descriptions,
3. converts them into embeddings,
4. embeds the user's query,
5. compares similarity,
6. returns the top matching image or top-k images.

This provides a practical semantic retrieval baseline.

---

## 8. Why a Caption-Based Baseline Makes Sense
The caption-based baseline is the most appropriate first implementation because it:
- directly satisfies the assignment requirement,
- is easy to inspect and debug,
- creates human-readable intermediate outputs,
- establishes a clean reference point for future improvements.

It is not the strongest possible system, but it is the most stable first step.

---

## 9. Known Problem With the Baseline
Although useful, caption-only retrieval introduces a compression problem:
- images contain rich visual information,
- captions reduce that information into text,
- some fine-grained signals may be lost.

This means the baseline solves the core problem partially, but not perfectly.

This is acceptable for the first version, as long as the limitation is clearly documented.

---

## 10. Success Criteria for the Problem
This problem is considered meaningfully addressed if the system can:
- retrieve the correct image for clearly phrased natural-language queries,
- return relevant top-k results when exact top-1 is difficult,
- outperform simple keyword lookup on realistic examples,
- remain understandable and extensible.

---

## 11. What This Project Is Not Trying to Solve Yet
This project is not initially trying to solve:
- internet-scale image search,
- large distributed retrieval infrastructure,
- learned fine-tuning of a custom multimodal model,
- real-time user feedback optimization,
- production-grade recommendation systems.

The current scope is a clean semantic retrieval system over a prepared image set.

---

## 12. Final Problem Definition
This project solves the following practical problem:

**Given a collection of prepared images and a user's natural-language query, build a system that can identify and return the most semantically relevant image by converting image meaning and query meaning into comparable embeddings.**

The project begins with a caption-based retrieval baseline and is intentionally designed to support later expansion into richer multimodal retrieval.
