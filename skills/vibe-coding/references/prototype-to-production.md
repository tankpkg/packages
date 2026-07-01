# Prototype to Production

Sources: Nes (The Vibe-Coding Trap, Level Up Coding, 2026), Ashcraft (Vibe Coding Technical Debt, 2026), BaytechConsulting (AI Technical Debt and TCO, 2026), Vishnu KG (The Vibe Coding Hangover, 2026), Waseem et al. (Vibe Coding in Practice, arXiv 2512.11922)

Covers: refactoring vibe-coded prototypes into production systems, architecture recovery, incremental hardening, test-first refactoring, data model correction, and the staged migration approach.

## The Prototype Problem

Vibe-coded prototypes share a consistent set of qualities:

**What works:**
- Core user flow functions end-to-end
- UI looks reasonable (AI generates decent CSS)
- Basic CRUD operations succeed for single-user scenarios
- Happy paths feel polished

**What doesn't:**
- No error handling beyond the happy path
- Authentication may be incomplete or insecure
- Data model reflects AI assumptions, not business requirements
- No tests exist (or tests only cover happy paths)
- Code structure is flat — everything in one file or scattered randomly
- Dependencies are bloated (AI adds packages liberally)
- Performance degrades under real load or data volume

The gap between "demo-ready prototype" and "production-ready software" is larger than most vibe coders expect. This reference provides a systematic approach to crossing that gap.

## Assessment Phase

Before refactoring anything, assess what exists. Run this diagnostic:

### Automated Assessment

```bash
# Type safety check
tsc --noEmit 2>&1 | wc -l  # Count type errors

# Dependency audit
npm audit --audit-level=moderate
npm ls --all | wc -l  # Total dependency count

# Code complexity
npx eslint --rule 'complexity: ["error", 10]' src/ 2>&1 | grep "error" | wc -l

# Test coverage (if tests exist)
npx vitest run --coverage 2>&1 | grep "All files"

# Dead code detection
npx knip --reporter compact
```

### Manual Assessment Checklist

| Area | Questions |
|------|-----------|
| Authentication | Is auth complete? Are all routes protected? Session handling correct? |
| Data model | Does the schema match business requirements? Are relationships correct? |
| Error handling | What happens on network failure? Invalid input? Missing data? |
| Security | Input validation on all endpoints? No hardcoded secrets? CORS configured? |
| Performance | How does it handle 1000 records? 10,000? Concurrent users? |
| Testing | Any tests at all? What do they cover? |
| Dependencies | How many? Are they all needed? Any known vulnerabilities? |
| Code structure | Is there a recognizable architecture? Or is everything in random files? |

### Priority Matrix

After assessment, categorize issues:

| Priority | Category | Examples |
|----------|----------|---------|
| P0: Ship-blocker | Security vulnerability, data corruption risk | Missing auth, SQL injection, no input validation |
| P1: Must-fix | Incorrect business logic, broken edge cases | Wrong data model, missing error handling |
| P2: Should-fix | Maintainability, performance under load | No tests, flat file structure, unnecessary dependencies |
| P3: Nice-to-have | Code quality, optimization | Naming consistency, bundle size, type coverage |

Address P0 first, P1 next. Do not start P3 work while P0 or P1 issues remain.

## The Staged Migration Approach

Do not attempt a full rewrite. Incremental migration preserves working behavior while improving quality.

### Stage 1: Stabilize

**Goal:** Make the current code safe to refactor without breaking things.

1. **Add types** — Run `tsc --noEmit` and fix all type errors. Add explicit return types to all exported functions. Replace `any` with proper types.

2. **Add critical tests** — Write tests for the 3-5 most important user flows. These tests are your safety net for all subsequent refactoring.

3. **Fix security P0s** — Add input validation, fix auth gaps, remove hardcoded secrets. These cannot wait.

4. **Set up CI** — Automate `tsc`, `eslint`, and test runs on every commit.

```bash
# Example: minimal CI check
tsc --noEmit && eslint src/ && vitest run
```

After Stage 1, the code is no better architecturally, but it is safe and tested.

### Stage 2: Correct the Data Model

The data model is the foundation. If it's wrong, every layer built on it is also wrong.

**Common AI data model problems:**

| Problem | Symptom | Fix |
|---------|---------|-----|
| Missing relationships | Manual ID tracking in application code | Add proper foreign keys and relations |
| Flat structure | All fields on one table | Normalize into related tables |
| Wrong cardinality | One-to-one that should be one-to-many | Alter schema, migrate data |
| Missing constraints | Invalid data in database | Add NOT NULL, UNIQUE, CHECK constraints |
| No indexes | Slow queries on common access patterns | Add indexes for frequent query columns |

**Migration procedure:**

1. Document the current schema (AI can help: "describe all tables and relationships")
2. Design the target schema based on business requirements
3. Write a migration script (not the AI — migrations are fragile)
4. Test migration against a copy of production data
5. Update application code to use new schema
6. Run the test suite — all tests from Stage 1 must pass

### Stage 3: Introduce Architecture

Vibe-coded prototypes typically have no recognizable architecture. Code lives wherever the AI put it.

**Target architecture (typical web app):**

```
src/
  app/            # Routes and layouts (Next.js/Remix)
  components/     # UI components (presentational)
  features/       # Feature modules (domain logic + UI)
  lib/            # Shared utilities
    db.ts         # Database client and helpers
    auth.ts       # Authentication utilities
    errors.ts     # Error classes and handlers
  types/          # Shared TypeScript types
  __tests__/      # Test files (mirroring src structure)
```

**Refactoring procedure:**

1. Create the target directory structure
2. Move files one module at a time, running tests after each move
3. Update imports (use IDE "move file" refactoring or AI-assisted bulk update)
4. Extract shared code into `/lib` as you discover duplication
5. Extract reusable UI components as you identify patterns

### Stage 4: Harden Error Handling

AI-generated code typically handles only the success case. Add error handling layer by layer.

**API endpoints:**

```typescript
// Before (AI-generated — no error handling)
export async function POST(req: Request) {
  const body = await req.json();
  const project = await db.project.create({ data: body });
  return Response.json(project);
}

// After (production-ready)
export async function POST(req: Request) {
  const parsed = CreateProjectSchema.safeParse(await req.json());
  if (!parsed.success) {
    return Response.json(
      { error: 'Invalid input', details: parsed.error.flatten() },
      { status: 400 }
    );
  }

  try {
    const project = await db.project.create({ data: parsed.data });
    return Response.json(project, { status: 201 });
  } catch (error) {
    if (error instanceof PrismaClientKnownRequestError) {
      if (error.code === 'P2002') {
        return Response.json(
          { error: 'Project with this name already exists' },
          { status: 409 }
        );
      }
    }
    logger.error('Failed to create project', { error });
    return Response.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

**UI components:**

- Add loading states for all async operations
- Add error boundaries around feature modules
- Add empty states for lists and data displays
- Add form validation with user-facing error messages
- Handle network failures with retry options

### Stage 5: Add Comprehensive Tests

With architecture in place, add thorough test coverage:

| Layer | Test Type | Tool | Priority |
|-------|-----------|------|----------|
| Business logic | Unit tests | Vitest | High |
| API endpoints | Integration tests | Supertest/Vitest | High |
| Database queries | Integration tests (test DB) | Vitest + test container | High |
| Critical user flows | E2E tests | Playwright | High |
| UI components | Component tests | Testing Library | Medium |
| Edge cases | Unit tests | Vitest | Medium |

**Test generation with AI:**

Use AI to generate test scaffolds, but review edge cases manually:

```
"Generate comprehensive tests for the createProject endpoint.
Include: valid input, missing required fields, duplicate name,
invalid team ID, unauthorized user, database failure.
Follow patterns in @__tests__/users.test.ts."
```

### Stage 6: Optimize

Only after Stages 1-5 are complete:

- Remove unused dependencies (`npx knip`)
- Optimize database queries (add indexes, fix N+1)
- Add caching where appropriate
- Bundle analysis and code splitting
- Performance testing under realistic load

## Common Refactoring Recipes

### Recipe: Extract API Client

AI often scatters `fetch` calls throughout components:

1. Find all `fetch` calls: `grep -rn "fetch(" src/`
2. Group by API endpoint
3. Create `/lib/api.ts` with typed functions per endpoint
4. Replace scattered fetch calls with API client calls
5. Add error handling in one place

### Recipe: Centralize State Management

AI generates local state everywhere, leading to prop drilling and inconsistency:

1. Identify shared state (user, auth, settings, cart)
2. Extract into context providers or state management library
3. Replace prop drilling with context consumption
4. Keep local state for truly local concerns (form inputs, UI toggles)

### Recipe: Consolidate Duplicate Code

AI generates similar code in multiple places because it doesn't track what it already generated:

1. Run duplicate detection: `npx jscpd src/ --min-lines 5`
2. Identify the canonical implementation (best version)
3. Extract to shared location
4. Replace duplicates with imports

## Anti-Patterns in Refactoring

| Anti-Pattern | Problem | Better Approach |
|-------------|---------|-----------------|
| Full rewrite | Lose working behavior, take months | Incremental staged migration |
| Refactoring without tests | No safety net, introduce regressions | Add tests before refactoring |
| Using AI to fix AI mess | Compounds the problem | Manual review + targeted AI assistance |
| Perfecting before shipping | Ship never arrives | Ship with P0/P1 fixed, improve in production |
| Ignoring data model | Architecture on wrong foundation | Fix data model in Stage 2, before architecture |

## Timeline Expectations

| Prototype Size | Stages 1-2 | Stages 3-4 | Stages 5-6 | Total |
|---------------|-----------|-----------|-----------|-------|
| Small (5-10 pages) | 1-2 days | 2-3 days | 2-3 days | 1-2 weeks |
| Medium (20-30 pages) | 3-5 days | 1-2 weeks | 1-2 weeks | 3-5 weeks |
| Large (50+ pages) | 1-2 weeks | 2-4 weeks | 2-4 weeks | 5-10 weeks |

These timelines assume one developer working with AI assistance for the refactoring itself. The AI accelerates the mechanical parts (moving files, updating imports, generating tests) while the developer drives architectural decisions.
