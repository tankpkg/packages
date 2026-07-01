# AGENTS.md Specification

Sources: agents.md official site, OpenAI Codex documentation, Linux Foundation AAIF announcement (Dec 2025), GitHub Blog (Matt Nigh, 2500+ repo analysis, Nov 2025)

Covers: AGENTS.md format, discovery mechanics, governance, ecosystem adoption, FAQ, and the 60k+ repository landscape.

## What AGENTS.md Is

AGENTS.md is a Markdown file placed at the root of a repository that provides AI coding agents with project-specific operational guidance. It complements README.md (for humans) with agent-focused context: build commands, testing rules, coding conventions, and constraints the agent cannot infer from the codebase alone.

| File | Audience | Purpose |
|------|----------|---------|
| README.md | Human developers | Project overview, installation, usage |
| CONTRIBUTING.md | Human contributors | PR process, code style for humans |
| AGENTS.md | AI coding agents | Build commands, test runners, conventions, constraints |

## Format

AGENTS.md is plain Markdown. No schema. No required fields. No YAML frontmatter (unless used as a GitHub Copilot agent persona file). Write any headings; the agent parses the text directly.

### Recommended Sections

Based on GitHub's analysis of 2,500+ repositories, the most effective files cover six areas:

| Section | Purpose | Example |
|---------|---------|---------|
| Stack definition | Prevent framework/version guessing | "Next.js 15, TypeScript strict, pnpm" |
| Executable commands | Give agent runnable verification | "Run `npm test -- --coverage`" |
| Coding conventions | Show style through examples | Code snippet showing your pattern |
| Testing rules | Define verification expectations | "All new endpoints need tests in /tests/api/" |
| Boundaries | Prevent destructive actions | "Never modify /migrations/ directly" |
| Non-standard tooling | Cover training-data gaps | "Use `pixi run` not `pip install`" |

### Minimal Example

```markdown
# AGENTS.md

## Stack
- Next.js 15 (App Router), TypeScript strict, Tailwind CSS v4
- Database: Postgres via Prisma
- Package manager: pnpm (always use pnpm, never npm)

## Commands
- Install: `pnpm install`
- Dev: `pnpm dev`
- Test: `pnpm test`
- Lint: `pnpm lint`
- Typecheck: `pnpm typecheck`

## Conventions
- Named exports only, no default exports
- API routes in /app/api/
- Tests use Vitest, not Jest

## Boundaries
- Never modify files in /legacy/
- Never commit .env files
- Ask before adding new dependencies

## Before finishing
- Run `pnpm lint && pnpm test`
- Check for unused imports
```

## Discovery Mechanics

### Directory Traversal

Most tools that read AGENTS.md follow the same pattern: walk from the current working directory (or the file being edited) up to the project root, checking each directory for instruction files. The closest file to the edited file takes precedence.

```
project/
  AGENTS.md              <-- Project root (loaded always)
  apps/
    web/
      AGENTS.md          <-- Loaded when editing web/ files
    api/
      AGENTS.md          <-- Loaded when editing api/ files
  packages/
    shared/
      AGENTS.md          <-- Loaded when editing shared/ files
```

### Precedence Rules

| Rule | Behavior |
|------|----------|
| Closer file wins | Subdirectory AGENTS.md overrides root |
| User prompt overrides all | Explicit chat instructions beat any file |
| Files concatenate | Most tools merge rather than replace (root + subdirectory) |
| Override files | Codex supports `AGENTS.override.md` at each level |

### Codex-Specific Discovery

OpenAI Codex has the most detailed discovery specification:

1. Global: `~/.codex/AGENTS.override.md` or `~/.codex/AGENTS.md` (first non-empty wins)
2. Project: Walk from Git root to CWD, checking `AGENTS.override.md` > `AGENTS.md` > fallback filenames
3. Merge: Concatenate root-to-CWD with blank lines between files
4. Size limit: `project_doc_max_bytes` (default 32 KiB)
5. Fallback filenames: Configurable via `project_doc_fallback_filenames` in `config.toml`

```toml
# ~/.codex/config.toml
project_doc_fallback_filenames = ["TEAM_GUIDE.md", "CLAUDE.md", ".agents.md"]
project_doc_max_bytes = 65536
```

## Governance

AGENTS.md is stewarded by the Agentic AI Foundation (AAIF) under the Linux Foundation, announced December 2025. The AAIF also governs:

- Model Context Protocol (MCP) -- donated by Anthropic
- Goose -- donated by Block

Founding members include OpenAI, Anthropic, Google, AWS, Bloomberg, and Cloudflare.

### Origin

AGENTS.md originated from collaborative efforts across the AI software development ecosystem, including OpenAI Codex, Amp (Sourcegraph), Jules (Google), Cursor, and Factory. OpenAI helped pioneer the format for Codex, then donated it to the AAIF for neutral governance.

## Ecosystem Adoption

As of early 2026, over 60,000 public GitHub repositories contain an AGENTS.md file. The format is natively read by:

| Tool | AGENTS.md Support | Notes |
|------|-------------------|-------|
| OpenAI Codex CLI | Primary file | Originated format |
| GitHub Copilot | Native | Coding agent + .github/agents/ personas |
| Cursor | Native | Also reads .cursor/rules/ |
| Windsurf | Native | Also reads .windsurfrules |
| Amp (Sourcegraph) | Native | Falls back to CLAUDE.md |
| Devin | Native | Reads before starting tasks |
| VS Code | Native | Via Copilot integration |
| OpenCode | Native | Falls back to CLAUDE.md |
| Zed | Native | Via AI rules system |
| Warp | Native | Project-scoped rules |
| Aider | Configurable | Add to `.aider.conf.yml`: `read: AGENTS.md` |
| Roo Code | Native | -- |
| Junie (JetBrains) | Native | -- |
| Jules (Google) | Native | -- |
| Claude Code | Not native | Use `@AGENTS.md` import in CLAUDE.md |
| Gemini CLI | Not native | Uses GEMINI.md; configurable in settings.json |

## Notable Repository Examples

| Repository | What Makes It Effective |
|------------|------------------------|
| openai/codex | Comprehensive reference implementation |
| apache/airflow | Large Python project with detailed conventions |
| vercel/next.js | Monorepo with architecture guidance |
| inngest/website | Hard version constraints, "always use pnpm" |
| canonical/maas | Upper-bound example (371 lines) |

## FAQ

### Required fields?

None. AGENTS.md is plain Markdown. Write whatever headings help the agent.

### What if instructions conflict?

The closest AGENTS.md to the edited file wins. Explicit user chat prompts override everything.

### Will agents run commands from AGENTS.md?

Yes, if listed. Agents attempt to execute relevant programmatic checks and fix failures. This is advisory, not mechanically enforced.

### Can I update it later?

Treat AGENTS.md as living documentation. Version-control it, review changes like code.

### How do I migrate from another format?

Rename or symlink:

```bash
# From .cursorrules
cp .cursorrules AGENTS.md
# From CLAUDE.md (keep both, symlink)
ln -s AGENTS.md CLAUDE.md
```

### Ideal file length?

Under 200 lines for the root file. The ETH Zurich study showed that LLM-generated files over 200 lines produce diminishing returns and increase costs. Split into subdirectory files for large projects.

## Size and Cost Considerations

| Metric | Value |
|--------|-------|
| Recommended root file | Under 200 lines |
| Codex size limit | 32 KiB (configurable) |
| Inference cost overhead | ~19% for human-curated files |
| LLM-generated file risk | -3% task success, +20% cost |

Prompt caching mitigates overhead (cache reads are 90% cheaper). The cost is justified only when files contain non-inferable, human-curated content.

## GitHub Copilot Agent Personas

GitHub Copilot extends AGENTS.md with agent persona files in `.github/agents/`. These use YAML frontmatter to define specialized agents:

```markdown
---
name: test-agent
description: Writes unit tests for TypeScript functions
---

You are a QA engineer for this project.

## Boundaries
- Write to tests/ only
- Never remove failing tests
- Never modify source code
```

Invoke with `@test-agent` in the Copilot chat. This is a GitHub Copilot extension of the AGENTS.md concept, not part of the base specification.

## Monorepo Patterns

Large repositories benefit from layered AGENTS.md files. The root file covers project-wide rules; subdirectory files add context for specific packages or services.

### Monorepo Layout Example

```
monorepo/
  AGENTS.md                     # Global: linting, commit conventions, CI
  apps/
    web/
      AGENTS.md                 # Next.js-specific: App Router patterns, Tailwind
    mobile/
      AGENTS.md                 # React Native-specific: platform APIs, Expo
  packages/
    ui/
      AGENTS.md                 # Component library: export patterns, Storybook
    db/
      AGENTS.md                 # Prisma schema rules, migration workflow
  services/
    auth/
      AGENTS.md                 # Auth service: token handling, security constraints
```

### Root File for a Monorepo

```markdown
# AGENTS.md

## Monorepo Structure
- Package manager: pnpm with workspaces
- Build orchestrator: Turborepo
- Shared config in /packages/config/

## Commands (run from repo root)
- Install all: `pnpm install`
- Build all: `pnpm turbo build`
- Test all: `pnpm turbo test`
- Lint all: `pnpm turbo lint`
- Build single package: `pnpm turbo build --filter=@acme/web`

## Global Conventions
- All packages use TypeScript strict mode
- Shared types live in @acme/types -- never duplicate type definitions
- Use workspace protocol for internal deps: `"@acme/ui": "workspace:*"`

## Boundaries
- Never modify another package's source from within a different package
- Database migrations require review from @db-team
- All new packages must have a tsconfig.json extending /packages/config/tsconfig.base.json
```

### Subdirectory File for a Web App

```markdown
# AGENTS.md (apps/web)

## Stack
- Next.js 15 (App Router only, no Pages Router)
- Tailwind CSS v4 with @acme/ui components
- State: Zustand for client, TanStack Query for server

## Commands
- Dev: `pnpm dev` (port 3000)
- Test: `pnpm vitest run`
- Storybook: `pnpm storybook`

## Conventions
- Pages in app/(routes)/ use server components by default
- Add "use client" only when hooks or browser APIs are needed
- Route handlers in app/api/ return NextResponse, not plain Response
```

## Edge Cases

### Conflicting Instructions Across Levels

When a root AGENTS.md says "use Jest" and a subdirectory AGENTS.md says "use Vitest," the subdirectory file wins for files within that directory. Resolve conflicts deliberately:

| Scenario | Resolution |
|----------|------------|
| Root says Jest, subdir says Vitest | Subdir wins for its scope |
| Root says "never modify migrations," subdir says "run prisma migrate" | Subdir cannot override a root boundary -- root takes precedence for safety |
| Root says 2-space indent, subdir says 4-space | Subdir wins -- formatting is local |
| Two sibling subdirs have contradictory rules | No conflict -- each applies only to its own scope |

### Empty or Minimal Files

A zero-content AGENTS.md signals "this directory has been considered but needs no special rules." Some tools skip empty files; others treat them as intentional. Prefer a one-line file with a comment over a truly empty file:

```markdown
# No additional agent instructions for this directory.
```

### Symlinks and Aliases

Tools that discover AGENTS.md via filesystem traversal follow symlinks. Use symlinks to share a single canonical file across tool-specific names:

```bash
# Single source of truth
ln -s AGENTS.md CLAUDE.md
ln -s AGENTS.md .cursorrules
```

Verify symlink behavior with your specific tool -- some tools (notably Windows environments) do not follow symlinks reliably.

### Binary and Non-Markdown Content

AGENTS.md must be valid UTF-8 Markdown. Do not embed base64 images, binary content, or HTML `<script>` tags. Tools parse the file as plain text and may truncate or reject non-Markdown content silently.
