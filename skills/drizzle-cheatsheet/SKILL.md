---
name: "@tank/drizzle-cheatsheet"
description: |
  Fast Drizzle ORM syntax and workflow reference. Covers schema definition,
  columns and relations, query builder basics (`select`, `insert`, `update`,
  `delete`, joins), drizzle-kit commands (`generate`, `push`, `migrate`,
  `studio`), type inference, and common Drizzle usage patterns.

  Synthesizes Drizzle ORM official documentation, drizzle-kit docs, and common
  TypeScript/SQL workflow patterns.

  Trigger phrases: "drizzle cheat sheet", "drizzle orm cheat sheet",
  "drizzle schema", "drizzle query", "drizzle commands", "drizzle-kit",
  "drizzle relations", "drizzle select"
---

# Drizzle Cheat Sheet

## Core Philosophy

1. **Optimize for syntax recall** — Cheat sheets should help you write the right schema or query shape quickly.
2. **Keep schema and query sections distinct** — Engineers often need one or the other fast.
3. **Include workflow commands** — Drizzle use is not only code syntax; `drizzle-kit` commands matter too.
4. **Prefer concise examples over explanation** — This is reference material, not ORM theory.
5. **Show TypeScript-friendly patterns** — Drizzle’s value comes from explicit schema and strong typing.

## Quick-Start: Common Problems

### "How do I define a table?"

1. import table/column helpers
2. define columns
3. add indexes/relations as needed
-> See `references/syntax.md`

### "What are the core drizzle-kit commands?"

| Need | Command |
|------|---------|
| generate migration | `drizzle-kit generate` |
| push schema | `drizzle-kit push` |
| run studio | `drizzle-kit studio` |
-> See `references/syntax.md`

## Decision Trees

| Signal | Focus area |
|--------|------------|
| defining schema | tables, columns, relations, indexes |
| writing queries | select/insert/update/delete/joins |
| changing schema | drizzle-kit workflow |
| working with types | inferred select/insert models |

## Reference Index

| File | Contents |
|------|----------|
| `references/syntax.md` | Drizzle schema syntax, relation patterns, query builder examples, drizzle-kit commands, type inference, and common ORM snippets |
