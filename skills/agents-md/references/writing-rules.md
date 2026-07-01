# Writing Effective Agent Instructions

Sources: ETH Zurich context file study (arxiv 2602.11988, 2026), GitHub Blog (Matt Nigh, 2500+ repo analysis), Augment Code AGENTS.md guide (2026), Anthropic Claude Code documentation, OpenAI Codex best practices

Covers: evidence-based instruction writing, the six core sections, anti-patterns, context cost tradeoffs, specificity calibration, and the boundary system.

## The ETH Zurich Evidence

A 2026 ETH Zurich study evaluated multiple coding agents across two benchmarks, comparing LLM-generated and developer-written context files against no context file at all. The findings are the empirical foundation for instruction file design.

### Key Findings

| Context File Type | Cost Increase | Task Success Change | Extra Steps |
|-------------------|---------------|---------------------|-------------|
| LLM-generated (auto-init) | +20% to +23% | -0.5% to -2% | 2.45 to 3.92 |
| Developer-written (human-curated) | Up to +19% | +4% (marginal gain) | Minimal |
| No context file | Baseline | Baseline | Baseline |

### Critical Insight

When all other documentation was removed from the repository, LLM-generated files improved performance by 2.7%. This confirms: LLM-generated context files duplicate information agents already discover from README, docs, and code. The duplication adds cost without signal.

### Implications for Practice

1. Never auto-generate and commit an AGENTS.md without human review
2. Include only what agents cannot discover independently
3. Remove architectural overviews -- they increased cost without improving success
4. Keep files short -- shorter human-written files had lower overhead than longer ones

## The Six Core Sections

GitHub's analysis of 2,500+ AGENTS.md files identified six sections that consistently improve agent behavior.

### Section 1: Stack Definition

State framework, language, versions, and package manager explicitly. Agents default to whatever conventions dominate their training data.

```markdown
## Stack
- Framework: Next.js 15 (App Router + Pages Router hybrid)
- Language: TypeScript (strict mode)
- Package Manager: pnpm (always use pnpm, never npm)
- Node Version: 22.x (required)
- Database: PostgreSQL 16 via Prisma ORM
```

Include versions for frameworks and major dependencies. "React project" tells the agent nothing useful. "React 19 with Vite 6, Tailwind CSS v4, and Zustand" tells it everything.

### Section 2: Executable Commands

Place commands early in the file -- agents reference them repeatedly. Include full flags and options, not just tool names.

```markdown
## Commands
- Install: `pnpm install`
- Dev server: `pnpm dev` (port 3000)
- Build: `pnpm build`
- Typecheck: `pnpm typecheck`
- Lint: `pnpm lint`
- Test all: `pnpm test`
- Test single file: `pnpm vitest run src/path/to/file.test.ts`
- Test by name: `pnpm vitest run -t "pattern"`
```

Agents will attempt to run these commands before finishing tasks. Accuracy prevents wasted iterations.

### Section 3: Coding Conventions

Show conventions through code examples. One real snippet beats three paragraphs of description. Focus on the counterintuitive.

```markdown
## Conventions
All client `api`, `apiVoid`, and `apiForm` methods never throw exceptions.
They always return an `ApiResult<T>` with either a response or an error
with a populated `ResponseStatus`. Using `try/catch` around `client.api`
calls is always wrong.
```

Without this, an agent wraps every API call in try/catch. The file explains the mechanism so the agent generalizes to novel situations.

### Section 4: Testing Rules

For simple setups, guidelines suffice. For complex build systems, provide exact commands.

```markdown
## Testing
- Write tests for all new functionality
- Tests use Vitest, never Jest
- Mock external HTTP calls with msw
- Run `pnpm test` before marking any task complete
- If adding a new API endpoint, add tests in tests/api/
```

### Section 5: Boundaries

The most impactful section. "Never commit secrets" was the single most common helpful constraint across 2,500+ repos. Use a three-tier system:

```markdown
## Boundaries

### Always
- Run linting before committing
- Use named exports, not default exports
- Add tests for new functionality

### Ask First
- Database schema changes
- Adding new dependencies
- Modifying CI/CD configuration

### Never
- Commit secrets or .env files
- Force push to main
- Modify files in vendor/ or dist/
- Remove failing tests
```

### Section 6: Non-Standard Tooling

The highest ROI section. Cover tools underrepresented in LLM training data:

```markdown
## Package Management
This project uses pixi, not pip:
- `pixi run <command>`
- `pixi run python script.py`
- `pixi run pytest`
```

For standard tools (npm, pytest, cargo), agents already know the conventions. Do not waste tokens on them.

## Writing Principles

### Specificity Spectrum

| Vague (Weak) | Specific (Strong) |
|--------------|-------------------|
| "Format code properly" | "Use 2-space indentation, no tabs" |
| "Test your changes" | "Run `npm test` before committing" |
| "Keep files organized" | "API handlers live in `src/api/handlers/`" |
| "Follow best practices" | "Use parameterized queries for all SQL" |
| "Use good naming" | "Functions: camelCase, Classes: PascalCase, Constants: UPPER_SNAKE_CASE" |

### Verifiable Rules

Every instruction should be verifiable. If you cannot check compliance programmatically or by inspection, the rule is too vague. Transform vague guidance into concrete, checkable statements.

### Mechanism Over Edict

Explain WHY a rule exists so the agent can generalize. "Never use localStorage for tokens" is weaker than "Store tokens in HttpOnly cookies -- localStorage is vulnerable to XSS, allowing any injected script to steal the token."

### Brevity Over Completeness

Context windows are shared. Every line of instruction competes with conversation, code, and tool outputs. A 2,000-line AGENTS.md means critical rules on line 1,847 get lost in the middle.

| Root File Size | Recommendation |
|----------------|----------------|
| Under 100 lines | Ideal for most projects |
| 100-200 lines | Maximum for root file |
| 200-400 lines | Split into subdirectory files |
| 400+ lines | Mandatory split; remove redundant content |

## Anti-Patterns

### Auto-Generated Files

Running `/init` and committing without review produces files that duplicate existing docs. The ETH study showed this reduces performance. Generate a draft, then edit ruthlessly -- keep only non-inferable details.

### Context File Bloat

Every agent mistake triggers the impulse to add another rule. Rules are rarely removed. Files accumulate contradictory patches and one-off fixes. Audit quarterly: remove stale rules, merge overlapping ones, delete rules agents already follow without instruction.

### Stale Structural References

"The billing service is in /src/billing/" becomes a liability when billing moves to /services/billing/. Agents follow the stale reference, wasting iterations. Remove file structure documentation unless it genuinely helps (non-obvious organization). Agents discover structure by reading the filesystem.

### Silent Rule Dropout

Documented in Claude Code issues: agents in long sessions ignore later instructions ("lost in the middle" phenomenon). Place critical rules early. Keep files short. Start new sessions for new tasks.

### Duplicated Content

Maintaining identical instructions in AGENTS.md, CLAUDE.md, and .cursorrules guarantees drift. Use a single canonical file with tool-specific bridges (see `references/cross-tool-strategy.md`).

### Style Guide Dumps

Pasting an entire 50-page coding standard into AGENTS.md. Extract the 10 rules that matter most for agent behavior. Link to the full guide for human reference.

## Context Cost Tradeoff

Every instruction file adds tokens to the prompt. Using Claude Sonnet pricing ($3/MTok input):

| Monthly Task Volume | 19% Overhead Cost |
|---------------------|-------------------|
| 1,000 tasks | ~$45 |
| 10,000 tasks | ~$450 |
| 100,000 tasks | ~$4,500 |

Prompt caching reduces this significantly (cache reads 90% cheaper). The overhead is justified only when files improve agent behavior enough to reduce debugging and rework time.

## Template: Starting Point

```markdown
# AGENTS.md

## Stack
[Framework, language, versions, package manager -- be specific]

## Commands
[Install, dev, build, test, lint, typecheck -- exact commands with flags]

## Conventions
[Show style through code example, not description]
[Focus on counterintuitive patterns]

## Testing
[Framework, location, commands, expectations]

## Boundaries
### Always: [safe operations]
### Ask first: [risky operations]
### Never: [destructive operations]
```

Start with this. Expand only when agents make mistakes that could have been prevented by instruction. Treat expansion as a code change requiring review.

## Real-World Convention Patterns

These patterns appear repeatedly in effective AGENTS.md files across production repositories.

### Error Handling Convention

```markdown
## Error Handling
- API routes return `{ success: boolean, data?: T, error?: string }`
- Never throw unhandled exceptions in API handlers
- Use `Result<T, E>` pattern for service layer functions
- Log errors with structured format: `logger.error({ err, context, requestId })`
- Client-side: display user-friendly messages, log technical details to console
```

### Import Ordering Convention

```markdown
## Import Order
Enforce this order in all TypeScript files (ESLint import/order handles it):
1. Node built-ins (`node:fs`, `node:path`)
2. External packages (`react`, `zod`, `drizzle-orm`)
3. Internal aliases (`@/lib/`, `@/components/`)
4. Relative imports (`./utils`, `../types`)
5. Style imports (`./styles.css`)

Separate each group with a blank line.
```

### Git Commit Convention

```markdown
## Commits
- Format: `type(scope): description` (e.g., `fix(auth): handle expired refresh tokens`)
- Types: feat, fix, docs, style, refactor, test, chore
- Scope: the package or module name
- Description: imperative mood, lowercase, no period
- Breaking changes: add `!` after type (e.g., `feat(api)!: change response format`)
```

### Database Conventions

```markdown
## Database
- All queries use parameterized statements -- never string interpolation
- Migrations are append-only: never modify an existing migration file
- New tables require an `id` (UUID v7), `created_at`, and `updated_at` column
- Use transactions for multi-table writes
- Index every foreign key column
```

## Edge Cases in Instruction Design

### When Conventions Clash with Agent Training

Agents have strong priors from training data. When your project deviates from mainstream conventions, instructions must be explicit and repeated.

| Training Default | Your Convention | Required Instruction |
|-----------------|-----------------|---------------------|
| Jest for React testing | Vitest | "Use Vitest, NEVER Jest. No `jest.fn()`, use `vi.fn()`" |
| `export default` components | Named exports only | "Always use named exports. No default exports anywhere." |
| REST APIs | tRPC | "All API communication uses tRPC. Never create REST endpoints." |
| npm | pnpm | "Use pnpm for all commands. npm and yarn are not configured." |
| CSS Modules | Tailwind | "Style with Tailwind utility classes. No CSS files." |

For strong deviations, use both a positive statement ("Use Vitest") and a negative constraint ("Never use Jest"). Agents occasionally revert to training defaults mid-task.

### Handling Generated Code

```markdown
## Generated Files
These files are auto-generated. Never edit them manually:
- `src/generated/api-types.ts` -- generated by `pnpm codegen`
- `prisma/client/` -- generated by `prisma generate`
- `src/graphql/__generated__/` -- generated by GraphQL Code Generator

If types are wrong, fix the source schema and re-run the generator.
```

Without this instruction, agents routinely edit generated files, producing changes that are overwritten on the next generation run.

### Multi-Language Repositories

For polyglot projects, partition instructions by language clearly:

```markdown
## Python (services/)
- Python 3.12+, type hints required on all functions
- Use `uv` for package management, not pip
- Run tests: `uv run pytest`
- Linting: `uv run ruff check .`

## TypeScript (frontend/)
- Node 22, pnpm, TypeScript strict
- Run tests: `pnpm vitest run`
- Linting: `pnpm eslint .`

## Shared Rules
- All services communicate via gRPC (protobuf definitions in /proto/)
- Never hardcode URLs -- use environment variables
```

## Measuring Instruction Effectiveness

### Signals That Instructions Are Working

| Signal | Meaning |
|--------|---------|
| Agent runs correct build command first try | Commands section is accurate |
| Agent places new files in correct directories | Conventions section is clear |
| Agent does not touch forbidden files | Boundaries section is effective |
| Agent uses project-specific patterns | Convention examples are being followed |
| Agent asks before risky operations | "Ask first" tier is respected |

### Signals That Instructions Need Revision

| Signal | Likely Cause |
|--------|-------------|
| Agent uses npm instead of pnpm | Missing or buried package manager instruction |
| Agent creates `*.test.js` instead of `*.test.ts` | Missing testing convention |
| Agent edits generated files | Missing generated files section |
| Agent ignores a rule after long context | File too long; rule buried past effective window |
| Agent adds default exports | Convention stated but not reinforced with negative constraint |

### Iterative Improvement Workflow

1. Run agent on a real task without AGENTS.md
2. Note every mistake the agent makes
3. For each mistake, ask: "Could the agent have discovered this from the codebase?"
4. If no: add a concise instruction
5. If yes: do not add an instruction (it would be redundant)
6. After adding instructions, run the same task again to verify improvement
7. Remove any instruction that did not change agent behavior
