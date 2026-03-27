# Recommendation Logic

## Ranking philosophy

Do not treat the homepage as a leaderboard of fake precision.

The preferred direction is:
- weaker emphasis on exact absolute scores
- stronger emphasis on relative comparison within the same topic
- clearer ranking labels and short human-readable reasons

Examples of better homepage language:
- `TOP 1`
- `????`
- `????`
- `????`

## What relative comparison should consider

When ranking papers within one topic, prioritize:
- topic fit
- clarity of study goal
- usefulness of the conclusion
- implementation or experimental solidity
- reproducibility level
- presence of code, datasets, appendix clues, or GitHub evidence
- beginner-friendliness

## Reproducibility as a first-class signal

Paper Reader should not stop at a single reproducibility label.

It should also expose why that judgment was made, such as:
- code available
- dataset link or source available
- appendix implementation clues
- training details or hyperparameters mentioned
- model architecture or evaluation details present
- valid GitHub URL detected

Useful backend/detail fields often include:
- `reproducibility_level`
- `reproducibility_level_zh`
- `reproducibility_reason`
- `evidence_signals`
- `appendix_signals`
- `github_url`
- `dataset_links`

## Frontend expression

Homepage should show compact signals:
- rank or tier
- one-sentence summary
- reproducibility level
- one short ranking reason

Detail page can expand into:
- recommendation explanation
- evidence tags
- implementation clues
- resource links
- limitations and tradeoffs

## Guardrails

Avoid:
- ranking outputs where many items all display almost the same number
- showing fake GitHub links that were not validated
- describing a paper as easy to reproduce without evidence
- letting the detail page depend on only one fragile data source
