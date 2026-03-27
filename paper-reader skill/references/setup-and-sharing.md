# Setup And Sharing

## Local environment expectations

Recommended baseline:
- frontend: Node.js v24 range with npm
- backend: Python 3.11

Python 3.11 is preferred because newer Python versions may cause dependency friction for packages such as `tokenizers`.

## Project shape

A common Paper Reader workspace looks like:
- `paper-reader-ui`: Next.js frontend
- `paper-reader-v1`: FastAPI backend

## Typical local startup flow

Frontend:
- install dependencies
- run the Next.js dev server

Backend:
- create and activate a Python 3.11 environment if needed
- install from `requirements.txt`
- run FastAPI with uvicorn

If the repo already contains startup scripts or `.env.example`, prefer reusing them.

## Sharing and packaging rules

When preparing a shareable copy, do not package large local dependency directories such as:
- `paper-reader-ui/node_modules`
- `paper-reader-v1/.venv`

Instead, include reproducible setup files such as:
- `README.md`
- `.env.example`
- `requirements.txt`
- startup scripts

## Public-use mindset

When helping another person use the project:
- prefer explicit setup steps over tacit local assumptions
- preserve existing project conventions
- keep startup commands deterministic
- call out version-sensitive dependencies early
