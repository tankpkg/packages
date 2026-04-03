# Rules Files

Sources: Cursor documentation (2026), Anthropic Claude Code docs, OpenAI AGENTS.md specification, Linux Foundation Agentic AI Foundation, vibecoding.app (Zane, 2026), Gupta (One Rulebook for All Your AI Coding Tools, 2025)

Covers: rules file authoring for every major AI coding tool, structural patterns, content guidelines, cross-tool standardization via AGENTS.md, and maintenance workflows.

## Why Rules Files Exist

LLMs have no persistent memory between sessions. Every new conversation starts blank. Without rules files, developers repeat the same context every prompt: "use TypeScript strict mode," "follow our naming conventions," "put components in /components."

Rules files provide persistent, reusable context that loads at the start of every AI interaction. The investment is 30-60 minutes for initial authoring; the return is consistent output across every session.

## Tool-Specific Formats

### Cursor: .cursor/rules/

Cursor deprecated the single `.cursorrules` file in favor of a `.cursor/rules/` directory with multiple `.mdc` files. Each file covers a separate concern.

**Directory structure:**

```
.cursor/
  rules/
    general.mdc       # Project-wide conventions
    typescript.mdc     # Language-specific rules
    react.mdc          # Framework patterns
    api.mdc            # Backend conventions
    testing.mdc        # Test patterns
```

**MDC file format:**

```markdown
---
description: TypeScript coding standards
globs: "**/*.ts,**/*.tsx"
alwaysApply: false
---

# TypeScript Standards

## Type Safety
- Enable strict mode in tsconfig.json
- No `any` types — use `unknown` and narrow
- Prefer interfaces for object shapes, types for unions
- All function parameters and returns explicitly typed

## Naming
- PascalCase for types, interfaces, classes, components
- camelCase for variables, functions, parameters
- UPPER_SNAKE for constants and env variables
```

**Application modes:**

| Mode | When Applied | Use For |
|------|-------------|---------|
| Always Apply | Every interaction | Project-wide conventions, file structure |
| Auto Apply (glob) | Files matching pattern | Language rules (`**/*.py`), framework rules |
| Agent Requested | AI decides based on description | Specialized patterns (deployment, migration) |
| Manual | Only when explicitly invoked | Rarely used, niche procedures |

### Claude Code: CLAUDE.md

Claude Code reads `CLAUDE.md` from the project root. It also reads `CLAUDE.md` files in subdirectories when working in those directories, enabling scoped rules.

```markdown
# Project: Dashboard App

## Stack
- Next.js 14 App Router
- TypeScript strict
- Tailwind CSS
- Supabase (auth + database)
- Vitest + Playwright

## Conventions
- Server components by default, client only when needed
- Database queries through /lib/db.ts only
- Error handling via custom AppError class
- Structured logging via /lib/logger.ts (no console.log)

## File Structure
- /app — routes and layouts
- /components — shared UI components
- /lib — utilities, database, auth helpers
- /types — shared TypeScript types

## Current Focus
Building the reporting module. Key files:
- /app/reports/page.tsx
- /lib/reports.ts
- /types/report.ts
```

**Scoped CLAUDE.md files:**

```
project-root/
  CLAUDE.md              # Project-wide rules
  packages/
    api/
      CLAUDE.md          # API-specific rules (inherits from root)
    web/
      CLAUDE.md          # Frontend-specific rules
```

### OpenCode and Multi-Tool: AGENTS.md

AGENTS.md originated from OpenAI's Codex CLI and is now governed by the Linux Foundation's Agentic AI Foundation as a cross-tool standard. Supported by Codex CLI, GitHub Copilot, Cursor, Windsurf, Claude Code (reads it), and OpenCode.

```markdown
# AGENTS.md

## Project Context
E-commerce platform with microservices architecture.
Monorepo managed by Turborepo.

## Stack
- Frontend: React 19, TypeScript, Tailwind
- API: Node.js, Fastify, Prisma
- Database: PostgreSQL
- Queue: BullMQ + Redis

## Coding Standards
- All functions typed — no implicit any
- Errors bubble up through Result<T, E> pattern
- Database access only through Prisma client in /lib/db
- API validation with Zod schemas

## Testing Requirements
- Unit tests for business logic (Vitest)
- Integration tests for API routes (supertest)
- E2E for critical paths (Playwright)

## Do Not
- Modify migration files after they've been applied
- Use console.log — use structured logger
- Access environment variables directly — use /lib/config
```

### Windsurf: .windsurfrules

Same concept as CLAUDE.md — a single markdown file in the project root. Windsurf's Cascade agent reads this for project context.

### GitHub Copilot: .github/copilot-instructions.md

Copilot reads instructions from `.github/copilot-instructions.md`. Same markdown format as AGENTS.md.

## What to Include

### Always Include

| Category | Examples |
|----------|---------|
| Tech stack + versions | "Next.js 14, TypeScript 5.4, Tailwind 3.4" |
| File organization | "Components in /components grouped by feature" |
| Naming conventions | "camelCase functions, PascalCase components" |
| Error handling pattern | "Custom AppError class, try/catch at API boundary" |
| Testing expectations | "Vitest for unit, Playwright for E2E" |
| Database access pattern | "All queries through /lib/db.ts" |

### Include When Relevant

| Category | Examples |
|----------|---------|
| Current sprint focus | "Working on notification system this week" |
| Known workarounds | "Supabase RLS requires service role for batch ops" |
| Security requirements | "All user input validated with Zod at API boundary" |
| Deployment constraints | "Max bundle size 200KB for landing page" |
| Third-party API patterns | "Stripe webhook verification in /api/webhooks" |

### Never Include

| Content | Why |
|---------|-----|
| "Write clean code" | Too vague — AI already tries this |
| Frequently changing data | Rules files are persistent — put volatile info in prompts |
| Personal preferences without impact | "I prefer tabs" adds noise without value |
| Entire API documentation | Too long — reference specific endpoints when needed |
| Secrets or credentials | Security risk — rules files are committed to version control |

## Structural Patterns

### Pattern 1: Layered Rules (Cursor)

Organize by specificity level:

```
.cursor/rules/
  01-project.mdc       # Always apply — project-wide
  02-typescript.mdc    # Auto apply — *.ts, *.tsx
  03-react.mdc         # Auto apply — *.tsx
  04-api.mdc           # Auto apply — /app/api/**
  05-testing.mdc       # Agent requested — test writing
  06-deployment.mdc    # Manual — deployment procedures
```

### Pattern 2: Convention-Over-Configuration

Keep rules concise. State the convention and one-line rationale:

```markdown
## Database
- Use Prisma — it's the ORM configured in this project
- Migrations in /prisma/migrations — never edit after applying
- Seed data in /prisma/seed.ts — for local dev only
```

### Pattern 3: Reference Linking

Link to existing documentation instead of duplicating:

```markdown
## Architecture
See @docs/architecture.md for full system design.

## API Contracts
See @docs/api-spec.yaml for endpoint definitions.
```

In Cursor, `@` references load linked files into context automatically.

## Cross-Tool Strategy

For teams using multiple AI tools, maintain one canonical AGENTS.md and tool-specific overrides:

```
project-root/
  AGENTS.md                        # Canonical — works with Copilot, Codex, OpenCode
  CLAUDE.md                        # Symlink or copy of AGENTS.md + Claude-specific additions
  .cursor/rules/project.mdc       # Cursor-specific format, same content
  .windsurfrules                   # Windsurf format, same content
```

Automate synchronization with a script or pre-commit hook to prevent drift between files.

## Maintenance

### When to Update Rules Files

| Trigger | Action |
|---------|--------|
| New library added | Add to stack section |
| Convention changed (e.g., new error pattern) | Update relevant section |
| AI repeatedly makes same mistake | Add explicit rule addressing it |
| Rules file > 200 lines | Split into multiple files (Cursor) or trim |
| Team member confused by AI output | Clarify the ambiguous rule |

### Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Rules file as a novel | Context window bloat, AI ignores long text | Keep under 150 lines per file |
| Contradictory rules | AI picks randomly between conflicts | Review for consistency quarterly |
| Rules without rationale | AI follows letter, not spirit | Add brief "why" for non-obvious rules |
| Never updating after initial write | Rules drift from actual practice | Review monthly or on convention changes |
| Copy-pasting from the internet | Generic rules that don't match project | Write rules from your actual conventions |

## Measuring Effectiveness

Track these signals to know if rules files are working:

| Signal | Healthy | Unhealthy |
|--------|---------|-----------|
| Repeated context in prompts | Rarely repeat stack/convention info | Frequently restating basics |
| Code style consistency | AI output matches project patterns | AI generates different styles each session |
| Onboarding friction | New team members' AI produces consistent code | Each person's AI generates differently |
| Rules file freshness | Updated within last 30 days | Last updated 6+ months ago |
