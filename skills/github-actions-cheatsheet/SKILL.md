---
name: "@tank/github-actions-cheatsheet"
description: |
  Fast GitHub Actions workflow syntax reference. Covers workflow structure,
  `on` triggers, jobs, matrices, steps, expressions, contexts, environment and
  secrets usage, `if:` conditionals, reusable workflows, artifacts, and common
  YAML snippets for CI/CD automation.

  Synthesizes GitHub Actions official documentation, workflow syntax docs, and
  practical CI/CD workflow patterns.

  Trigger phrases: "github actions cheat sheet", "github actions syntax",
  "github actions yaml", "github actions triggers", "github actions expressions",
  "workflow syntax", "reusable workflow", "github actions matrix"
---

# GitHub Actions Cheat Sheet

## Core Philosophy

1. **Optimize for syntax recall** — Cheat sheets are for quickly reconstructing working YAML under pressure.
2. **Group by workflow concern** — Triggers, jobs, expressions, matrices, and reusable workflows should be easy to find separately.
3. **Show the sharp edges** — Contexts, expressions, and `if:` logic are where most syntax mistakes happen.
4. **Prefer minimal working snippets** — Dense, copyable examples beat broad prose.
5. **Remember CI is a control system** — Syntax matters because release safety depends on it.

## Quick-Start: Common Problems

### "What is the basic workflow shape?"

1. `name`
2. `on`
3. `jobs`
4. `runs-on`
5. `steps`
-> See `references/syntax.md`

### "How do I add a matrix or conditional?"

| Need | Syntax area |
|------|-------------|
| matrix builds | `strategy.matrix` |
| conditional step/job | `if:` |
| expressions | `${{ ... }}` |
-> See `references/syntax.md`

## Decision Trees

| Signal | Focus area |
|--------|------------|
| need trigger syntax | `on:` |
| need job/step structure | `jobs:` / `steps:` |
| need reuse | `workflow_call` / reusable workflows |
| need dynamic logic | expressions, contexts, `if:` |

## Reference Index

| File | Contents |
|------|----------|
| `references/syntax.md` | GitHub Actions syntax, triggers, jobs, matrices, expressions, contexts, env/secrets, reusable workflows, artifacts, and common snippets |
