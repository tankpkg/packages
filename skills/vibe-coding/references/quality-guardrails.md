# Quality Guardrails

Sources: Waseem et al. (Vibe Coding in Practice, arXiv 2512.11922), pixelmojo.io (Vibe Coding Adoption and Vulnerabilities, 2026), Autonoma AI (Vibe Coding Quality Triage, 2026), OWASP AI Security guidelines, vibecoding.app (Mistakes to Avoid, 2026)

Covers: code review for AI-generated output, security scanning, testing strategies, static analysis integration, tech debt prevention, and the junior-dev-PR mental model.

## The Junior Developer Mental Model

Treat every AI-generated code block as a pull request from a talented but inexperienced junior developer. The code will:

- Handle happy paths well
- Miss edge cases (null inputs, network failures, concurrent access)
- Have security gaps (missing validation, overly permissive access)
- Look polished but lack architectural awareness
- Work in the demo but fail under production load

This mental model calibrates the right level of review: thorough enough to catch real issues, not so paranoid that vibe coding loses its speed advantage.

## Code Review Checklist

### Security Review (Non-Negotiable)

Review every AI generation for these categories:

| Category | Check For |
|----------|----------|
| Authentication | Auth checks on every protected route, not just the obvious ones |
| Authorization | Row-level access control, not just role checks |
| Input validation | Zod/Joi schemas on every external input (forms, API, URL params) |
| SQL/NoSQL injection | Parameterized queries, no string interpolation in queries |
| XSS | Output encoding, CSP headers, no dangerouslySetInnerHTML |
| Secrets | No hardcoded API keys, tokens, or credentials in source |
| Dependencies | No unnecessary packages, check for known vulnerabilities |
| Error exposure | Error messages don't leak internal details to users |

### Architectural Review

| Check | Why |
|-------|-----|
| File placement follows conventions | Prevents structural drift |
| New patterns match existing patterns | Consistency reduces maintenance cost |
| Dependencies added are justified | AI tends to add unnecessary packages |
| No circular dependencies introduced | AI doesn't track dependency graphs well |
| Database schema changes are intentional | AI may modify migrations unexpectedly |

### Logic Review

| Check | Why |
|-------|-----|
| Edge cases handled (empty arrays, null, undefined) | AI optimizes for happy paths |
| Error states have user-facing messages | AI often swallows errors silently |
| Loading states exist for async operations | AI generates the success state first |
| Pagination handles boundaries correctly | Off-by-one errors common in AI output |
| Race conditions in concurrent operations | AI rarely considers concurrent access |

## Static Analysis Integration

Run automated checks on every AI-generated change before committing:

### TypeScript Projects

```json
{
  "scripts": {
    "check": "tsc --noEmit",
    "lint": "eslint . --ext .ts,.tsx",
    "lint:security": "eslint . --ext .ts,.tsx --rule 'security/detect-object-injection: error'",
    "test": "vitest run",
    "validate": "npm run check && npm run lint && npm run test"
  }
}
```

Run `npm run validate` after every significant AI generation.

### Security-Focused Linting

Install and configure security-specific ESLint rules:

```bash
npm install -D eslint-plugin-security eslint-plugin-no-secrets
```

For deeper analysis, run Semgrep with language-specific rulesets:

```bash
semgrep --config auto --error src/
```

### Pre-Commit Hooks

Automate validation so AI-generated code gets checked before commit:

```yaml
# .husky/pre-commit
npm run check
npm run lint
npm run test -- --run
```

This catches type errors, lint violations, and test failures regardless of whether the code was human-written or AI-generated.

## Testing Strategies

### Test Generation with AI

AI excels at generating tests — use this strength to guard against its weaknesses.

**Pattern: Generate tests first, then implementation.**

```
"Write comprehensive tests for a createProject function that:
- Validates name is 3-50 characters
- Requires a valid team ID (UUID)
- Defaults visibility to 'private'
- Returns the created project with an ID and timestamps
- Throws AppError for invalid input
- Throws AppError if team doesn't exist

Use Vitest and follow the patterns in @__tests__/users.test.ts."
```

Then prompt for the implementation that passes these tests. This is TDD-by-vibe — the AI writes both sides, but tests constrain the implementation.

### Test Categories by Risk

| Risk Level | What to Test | How |
|-----------|-------------|-----|
| Critical (auth, payments) | Full coverage: unit + integration + E2E | Write tests manually or review AI tests line-by-line |
| High (core business logic) | Unit tests + integration tests | AI-generate, then review edge cases |
| Medium (CRUD, forms) | Happy path + basic error cases | AI-generate, spot-check |
| Low (styling, static pages) | Visual regression or none | Skip or use snapshot tests |

### What AI Tests Miss

| Gap | Example | Prevention |
|-----|---------|------------|
| Concurrency | Two users editing same resource | Add specific concurrent test scenarios |
| Rate limiting | API abuse patterns | Test with rapid sequential requests |
| Large datasets | Pagination with 100K records | Add performance test with realistic data volume |
| Network failures | API timeout, partial response | Mock network errors explicitly |
| Timezone issues | Date logic across timezones | Test with multiple timezone offsets |
| Unicode and i18n | Emoji in usernames, RTL text | Add unicode test fixtures |

## Tech Debt Prevention

### The Vibe Coding Debt Cycle

Research (Waseem et al., 2512.11922) documents a consistent pattern:

```
Fast generation -> "It works!" -> Ship -> Discover issues ->
Prompt AI to fix -> AI adds complexity -> More issues ->
Prompt AI to fix the fix -> Spaghetti code -> Rewrite
```

Break this cycle with checkpoints.

### Checkpoint System

After every significant feature, stop and verify:

| Checkpoint | Questions |
|-----------|-----------|
| Architecture | Does this feature fit the existing architecture? Any new patterns introduced? |
| Dependencies | Were new packages added? Are they necessary? Are they maintained? |
| Type safety | Does `tsc --noEmit` pass cleanly? Any new `any` types? |
| Test coverage | Are critical paths tested? Do tests cover error cases? |
| Security | Was input validation added for new endpoints? Auth checks present? |
| Documentation | Are new patterns documented in rules files? |

### Dependency Hygiene

AI tools frequently add unnecessary dependencies. After AI generates code with new packages:

1. Check if the functionality already exists in current dependencies
2. Verify the package is actively maintained (last commit < 6 months)
3. Check download counts and vulnerability reports
4. Ensure the package license is compatible with your project
5. Question packages that do very little — a 10-line utility doesn't need a dependency

### Code Complexity Monitoring

Track these metrics to catch AI-generated complexity creep:

| Metric | Tool | Threshold |
|--------|------|-----------|
| Cyclomatic complexity | ESLint complexity rule | Max 10 per function |
| File length | Custom lint rule | Max 300 lines |
| Function length | ESLint max-lines-per-function | Max 50 lines |
| Import depth | Dependency graph analysis | Max 3 levels |
| Type coverage | typescript-coverage | Min 95% |

## Security Scanning Pipeline

### Minimal Pipeline (Every Project)

```bash
# Type checking
tsc --noEmit

# Linting with security rules
eslint --ext .ts,.tsx src/

# Dependency vulnerability check
npm audit --audit-level=moderate

# Secret detection
npx secretlint "**/*"
```

### Comprehensive Pipeline (Production Projects)

```bash
# Everything from minimal, plus:

# SAST with Semgrep
semgrep --config auto --config p/owasp-top-ten src/

# Container scanning (if applicable)
trivy image your-app:latest

# License compliance
npx license-checker --failOn "GPL-3.0;AGPL-3.0"

# Bundle analysis (frontend)
npx @next/bundle-analyzer
```

### When AI Generates Infrastructure Code

Extra scrutiny for AI-generated infrastructure, deployment, and configuration:

| Category | Risk | Check |
|----------|------|-------|
| Docker files | Exposed ports, running as root | Review USER directive, port mappings |
| CI/CD configs | Secret exposure, permissive permissions | Check env variable handling |
| Database migrations | Data loss, constraint violations | Review in staging before production |
| Environment configs | Wrong values, missing variables | Compare against template |
| API integrations | Hardcoded URLs, missing error handling | Test against sandbox/staging |

## The "Ship It" Decision Framework

Before deploying AI-generated code to production:

| Question | If No |
|----------|-------|
| Does `tsc --noEmit` pass? | Fix type errors |
| Do all tests pass? | Fix or add tests |
| Has security review been done? | Review auth, validation, secrets |
| Are there no new `any` types? | Add proper types |
| Is the code complexity reasonable? | Refactor before shipping |
| Would you approve this as a PR from a colleague? | Revise until you would |
