# Broader Default Promotion Summary

## Promotion
- Status: broader_default
- Note: Promoted as the broader evaluation default on 2026-04-10 after the trusted frozen-artifact replay validated caption_plus_selected_structured plus deterministic top-3 rerank with question_paraphrase_overlap=0.25 and the singleton low-signal container guard enabled.
- Default configuration: caption_plus_selected_structured + deterministic_top3_rerank (top-3), question_paraphrase_overlap=0.25, singleton low-signal container guard enabled

## Results
| System | Role | Hard R@1 | Hard R@3 | Mixed R@1 | Mixed R@3 |
| --- | --- | ---: | ---: | ---: | ---: |
| caption_only | baseline | 0.6786 | 1.0000 | 0.6750 | 1.0000 |
| caption_plus_selected_structured | candidate | 0.8571 | 1.0000 | 0.8750 | 1.0000 |
| caption_plus_selected_structured + deterministic_top3_rerank + question_paraphrase_overlap=0.25 | final_default | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## Validation Caveat
- Frozen-artifact replay over the trusted mixed-sanity control/candidate artifacts validated the broader default at Recall@1 = 1.0000 and Recall@3 = 1.0000 with no regressions. A full end-to-end rebuild is still pending because a network Connection error interrupted the embedding rebuild.
