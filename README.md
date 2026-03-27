# Paper Reader

> A productized paper recommendation tool that helps researchers decide what to read first, why it matters, and whether it is worth reproducing.

[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Deploy-Docker-blue)](https://www.docker.com/)
[![Bring Your Own API](https://img.shields.io/badge/LLM-BYO%20API-111827)](#quick-start)

Paper Reader is built for a very practical research question:

- Which paper should I read first?
- Which one is actually worth deeper attention?
- Which one is more realistic to reproduce or track?

Instead of dumping a list of papers on the screen, it turns a topic into:

- ranked recommendation cards
- one-sentence takeaways
- clean detail pages
- comparison views for decision making
- lightweight follow-up lists

## Why People Star It

- It feels like a product, not just a crawler.
- It turns paper discovery into reading decisions.
- It is easy to try with Docker and your own API key.
- It supports both lightweight public usage and local-model workflows.

## Core Features

### 1. Daily Topic-Based Recommendations

- search by research topic such as `LLM`, `RAG`, `Multimodal`, or `Reasoning`
- get ranked paper cards instead of a raw feed
- each card shows a one-sentence takeaway and compact tags

### 2. Decision-Friendly Detail Pages

- recommendation conclusion
- background and goal
- summary and method notes
- reproducibility evidence
- normalized PDF download naming

### 3. Paper Comparison

- compare 2 to 3 papers under the same topic
- quickly judge which one deserves time first
- useful for reading, reproduction, inspiration, and related work decisions

### 4. My Follow-Ups

- save papers into reading list
- save papers into reproduction list
- save papers into topic candidate list
- persist follow-up items in the backend database

## Quick Start

This repo is optimized for the lightest onboarding path first.

### Recommended path: Docker + your own API key

You do **not** need Ollama, a local model download, Node.js, or Python just to try the product.

Run:

```bash
docker compose up --build
```

Then open:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Inside the app:

1. Open `Model Settings`
2. Choose `DeepSeek`, `Kimi`, `Qwen`, or another OpenAI-compatible API
3. Paste your own API key
4. Enter a topic like `LLM`, `RAG`, `Reasoning`, or `Multimodal`
5. Start using the product

This is the default public onboarding path.

## Deployment Modes

### Public / lightweight mode

Best for first-time users.

- Docker
- your own API key
- no Ollama required
- no local model download required

### Advanced local mode

Best for users who explicitly want local inference.

Optional:

```bash
ollama pull qwen2.5:7b
```

Then use:

- provider: `ollama`
- model: `qwen2.5:7b`
- base URL: `http://localhost:11434`

### Development mode

Use this only if you want to edit the code.

Frontend:

```bash
cd paper-reader-ui
npm install
npm run dev
```

Backend:

```bash
cd paper-reader-v1
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Screenshots To Add

For a stronger GitHub page, add these screenshots to the README later:

1. Homepage recommendations
2. Paper detail page
3. Compare page
4. Research toolbox / follow-up view

If you add screenshots, place them under `docs/` or `docs/assets/` and link them here.

## Tech Stack

### Frontend

- Next.js
- TypeScript

### Backend

- FastAPI
- SQLite

### Model Layer

- OpenAI-compatible API providers
- optional Ollama local inference

## Why SQLite First

This project is intentionally kept lightweight for:

- demos
- GitHub sharing
- local product showcase
- fast first deployment

Advanced users can later replace it with an external database if they want larger-scale persistence.

See:

- [`paper-reader-v1/.env.example.txt`](./paper-reader-v1/.env.example.txt)

## Repo Structure

```text
paper-project/
|- README.md
|- LICENSE
|- .gitignore
|- docker-compose.yml
|- docs/
|- paper-reader-ui/
|- paper-reader-v1/
`- paper-reader skill/
```

## Open Source Goal

This repo is not just a code dump. It is intended to show product thinking:

- ranking instead of raw listing
- decision support instead of paper collection
- follow-up workflow instead of one-time browsing
- deployability instead of environment-heavy prototypes

## License

MIT
