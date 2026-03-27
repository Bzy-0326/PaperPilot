# GitHub Launch Guide

This file is the exact checklist for publishing `paper-project` as a public GitHub repo.

## Suggested Repo Names

Pick one of these:

- `paper-reader`
- `daily-paper-reader`
- `paper-reader-ai`

Recommended:

`paper-reader`

## GitHub Short Description

Use this as your GitHub repository description:

`A productized paper recommendation tool for ranking, comparing, and following up on daily research papers.`

## Suggested Topics

Add these GitHub topics:

- `paper-reader`
- `research-tool`
- `llm`
- `nextjs`
- `fastapi`
- `docker`
- `paper-recommendation`
- `product-design`

## Before You Push

Make sure these are not included in the public repo:

- `paper-reader-ui/node_modules`
- `paper-reader-ui/.next`
- `paper-reader-v1/.venv`
- `paper-reader-v1/paper_reader.db`
- `paper-reader-v1/.env`

## Exact Commands

Open terminal and run:

```bash
cd C:\Users\Administrator\Desktop\paper-project
git init
git branch -M main
git status
git add .
git commit -m "Initial public release"
```

Then go to GitHub and create a new public repository.

Use:

- repository name: `paper-reader`
- visibility: `Public`
- do not add README
- do not add .gitignore
- do not add license

After the repo is created, copy its URL and run:

```bash
git remote add origin https://github.com/YOUR_USERNAME/paper-reader.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your real GitHub username.

## After Upload

Immediately do these 5 things:

1. Add the GitHub description from this file.
2. Add the topics from this file.
3. Pin the repository on your GitHub profile.
4. Put 3 to 5 screenshots into the README.
5. Share it with a short product-first post.

## Optional: Enable GitHub Pages

If you want a product-style project page:

1. Open repository `Settings`
2. Open `Pages`
3. Choose `Deploy from a branch`
4. Branch: `main`
5. Folder: `/docs`
6. Save

GitHub will generate a public page from `docs/`.
