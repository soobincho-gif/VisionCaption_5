# Next Up

## Next recommended task
Run a focused representation-fidelity pass on the remaining candidate failures.

## Why this is next
The fixed control/candidate rerun showed that the selected-structured candidate is stronger than caption-only, but the remaining failures are not random. They cluster around person-name disambiguation and exact visible UI text. That makes representation fidelity the next best lever before reranking.

## Suggested substeps
1. Inspect the seven `caption_plus_selected_structured` failures in `outputs/eval/control_candidate_baseline/caption_plus_selected_structured/results.json`.
2. Compare each failed query against the stored caption fields in `outputs/eval/structured_representation/captions.jsonl`.
3. Identify whether the missing cue is:
   - absent from the caption,
   - present in a structured field but underweighted in the source text,
   - present but too vague for same-family disambiguation.
4. Improve the representation or prompt only where it targets those failure modes.
5. Rerun:
   - `python -m pytest`
   - the fixed control/candidate comparison under `outputs/eval/control_candidate_baseline/`
6. Decide whether lightweight reranking is justified only if top-3 remains correct while top-1 remains frequently wrong after the representation pass.
