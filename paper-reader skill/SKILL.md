---
name: paper-reader
description: Public skill for installing, running, debugging, improving, and handing off a Paper Reader style product built with Next.js and FastAPI. Use when the user wants to work on a paper discovery and recommendation app with ranking cards, detail pages, and reproducibility evidence.
---

# Paper Reader

## Overview

Use this skill for a Paper Reader style product: a research-paper discovery and recommendation app that helps users decide what to read first, whether a paper is reproducible, and whether it is practical to follow or reimplement.

This is a public-facing skill meant for collaborators, adopters, and maintainers. It is optimized for:
- installing or running the project locally
- debugging frontend/backend linkage
- improving ranking, topic filtering, and paper detail presentation
- packaging the product for demos, collaboration, or further reuse
- continuing work from a handoff without losing product intent

## Quick Start

### When this skill should trigger

Use it when the user asks to:
- run or repair a paper recommendation app
- debug homepage, detail page, or API linkage
- improve paper ranking, topic matching, or reproducibility analysis
- prepare the product for another user, teammate, or public sharing
- continue implementation from a project handoff or transition summary

### Project shape to confirm first

Before editing, confirm the workspace includes:
- a Next.js frontend, often similar to `paper-reader-ui`
- a FastAPI backend, often similar to `paper-reader-v1`

Useful files to locate early:
- `package.json`
- `app/page.tsx`
- `app/paper/[paperId]/page.tsx`
- `app/main.py`
- `app/services/paper_repository.py`
- `app/services/light_analyzer.py`
- `app/services/topic_rules.py`

If the folder names differ, continue once the roles are clear.

## Working Rules

### 1. Preserve the product intent

Paper Reader is not just a paper fetcher. Treat it as a decision-support product.

Prefer changes that help the user answer:
- what should I read first
- why is this paper being recommended
- can I realistically reproduce or follow it
- is there code, data, appendix evidence, or a valid GitHub repo

Read `references/product-positioning.md` when making UX, ranking, or scope decisions.

### 2. Bring up the stack safely

Default environment assumptions:
- frontend: Node.js and npm
- backend: Python 3.11 preferred

If the repo already includes startup helpers such as `start_frontend.bat` or `start_backend.bat`, prefer using and fixing them rather than inventing parallel workflows.

When setup issues appear, read `references/setup-and-sharing.md`.

### 3. Debug in dependency order

For broken homepage/detail flows, inspect in this order:
1. route navigation and params
2. local fallback state in browser storage
3. recommendation list API response
4. recommendation detail API response
5. frontend/backend schema mismatches

If a URL changes but the UI looks stale, suspect fallback hydration before suspecting routing.

Read `references/handoff-notes.md` for the already-solved detail-page issue and the expected fallback pattern.

### 4. Improve recommendation quality as product logic

Do not rely only on a raw score when making the homepage useful.

Prefer:
- relative comparison within one topic
- interpretable ranking labels
- short ranking reasons
- stronger reproducibility evidence signals

Read `references/recommendation-logic.md` before touching ranking or recommendation output.

### 5. Keep homepage and detail page distinct

Homepage should act like triage.
Detail page should act like a research decision page.

Homepage should emphasize:
- rank or tier
- one-sentence summary
- reproducibility level
- short reason it surfaced

Detail page should emphasize:
- why it is recommended
- study goal
- method summary
- implementation evidence
- reproducibility signals
- GitHub, dataset, and PDF availability
- limitations

## References

Load references only when needed:
- `references/product-positioning.md`: product intent, user value, and UX framing
- `references/handoff-notes.md`: current stage, solved issues, and next priorities
- `references/recommendation-logic.md`: ranking philosophy and evidence logic
- `references/setup-and-sharing.md`: environment, local startup, and sharing rules

## Output Expectations

Using this skill should result in one of these:
- a working local setup
- a concrete code or product improvement
- a handoff-quality explanation of the current state
- a packaging or sharing improvement that helps another person use the product

Stay grounded in the actual repository. Favor the existing project conventions over generic boilerplate advice.
