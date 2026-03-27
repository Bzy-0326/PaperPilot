# Handoff Notes

## Current confirmed stage

The project already crossed the prototype-to-usable threshold:
- frontend and backend can run locally
- homepage and detail page are linked
- detail page has been productized beyond a minimal debug view
- reproducibility evidence signals are already part of the product direction
- basic collaboration docs and startup files have been prepared

## Already solved issue: detail page looked like it did not open

Observed behavior:
- clicking into detail changed the URL
- visually, the app seemed stuck on the old page

Root cause:
- homepage and detail page used different fallback storage patterns
- homepage stored a single paper fallback item in localStorage
- detail page originally tried to reconstruct from sessionStorage home state
- route worked, but no usable detail content hydrated

Expected fix pattern:
1. detail page first tries `localStorage` key `paper_detail_fallback_${paperId}`
2. if missing, detail page falls back to `sessionStorage` key `paper_reader_home_state_v1`
3. page then requests the backend detail endpoint for fuller data

## Productized detail page direction

The detail page should feel like a research decision page, not a generic summary page.

Expected sections include:
- title and high-level recommendation state
- quick reproducibility/resource checks
- recommendation conclusion
- background and study goal
- method summary
- content summary
- innovation points
- limitations
- reproducibility evidence signals
- GitHub, datasets, PDF, and related resources

## Current next-step priorities

The project handoff identified these likely next priorities:
- Dockerization
- top-5 relative ranking instead of over-precise absolute scores
- speed optimization for popular topics
- longer-term RAG and tag-tree evolution
- feedback entry points and GitHub-facing productization

## Practical rule

When continuing work from this state, do not re-open already solved routing questions unless the current code clearly disagrees with these notes.
