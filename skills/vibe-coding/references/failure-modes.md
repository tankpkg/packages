# Failure Modes

Sources: Waseem et al. (Vibe Coding in Practice, arXiv 2512.11922), SoftwareSeni (Evidence Against Vibe Coding, 2026), Masood (Vibe Coding = Tech Debt Factory, 2026), pixelmojo.io (Vibe Coding Vulnerabilities, 2026), Autonoma AI (Quality Triage Playbook, 2026)

Covers: anti-patterns and failure modes in vibe coding, architecture drift detection, context window exhaustion, over-reliance signals, hallucination patterns in code, and recovery procedures.

## Failure Mode Catalog

### 1. Architecture Drift

**Description:** Over multiple sessions, the AI introduces inconsistent patterns. One endpoint uses middleware auth, another uses inline checks. One component fetches data in useEffect, another uses a server component. The codebase becomes a patchwork of conflicting approaches.

**Detection signals:**
- Same problem solved differently in different files
- New developers ask "which pattern should I follow?"
- Code review comments say "this doesn't match our existing pattern"
- Grep reveals 3+ different ways to do the same thing

**Root cause:** Each AI session starts fresh. Without persistent rules files, the AI reinvents solutions each time. Long conversations compound drift as context window pushes out earlier decisions.

**Recovery:**
1. Audit the codebase for variant patterns: `grep -rn "fetch(" src/` to find all data fetching patterns
2. Choose the canonical pattern (usually the first or best-implemented version)
3. Document the canonical pattern in rules files
4. Refactor variants to match the canonical pattern (AI assists well here)
5. Add lint rules to enforce the pattern going forward

**Prevention:**
- Maintain rules files with explicit pattern decisions
- Start fresh conversations for each feature
- Reference existing code as style examples in every prompt
- Review for consistency, not just correctness

### 2. Context Window Exhaustion

**Description:** After 20-30 messages in a conversation, the AI begins contradicting earlier decisions. It rewrites code it generated 15 messages ago. It forgets constraints established at the start of the session.

**Detection signals:**
- AI suggests changes that undo previous work
- AI reintroduces patterns you explicitly rejected earlier
- AI generates code that conflicts with its own earlier generation
- Output quality noticeably degrades compared to early messages

**Root cause:** Context windows are finite. As conversation length grows, the oldest messages get truncated. The AI literally cannot see what it decided 20 messages ago.

**Recovery:**
1. Stop the current conversation
2. Commit all working code
3. Start a fresh conversation
4. Reference committed files with @ mentions
5. Restate key constraints in the opening prompt

**Prevention:**
- One conversation per feature (not per session)
- Start fresh every 15-20 messages
- Use checkpoint summaries (see `references/context-engineering.md`)
- Put persistent decisions in rules files, not conversation messages

### 3. Dependency Bloat

**Description:** AI liberally adds npm packages for functionality that could be implemented in a few lines or already exists in the project's dependencies.

**Detection signals:**
- `package.json` grows significantly with each feature
- Multiple packages serve overlapping purposes (three date libraries)
- Bundle size increases disproportionately
- `npm audit` reports increase over time

**Root cause:** AI training data includes millions of code samples that use packages. The AI defaults to "install a package" over "write 10 lines of code." It doesn't track what packages are already installed.

**Recovery:**
1. Run `npx knip` to identify unused dependencies
2. Run `npx depcheck` to find unnecessary packages
3. For each questionable package: can this be replaced with existing deps or 10 lines of code?
4. Remove unnecessary packages and replace with direct implementations
5. Run test suite to verify nothing breaks

**Prevention:**
- Add to rules file: "Do not add new dependencies without explicit approval. Check existing dependencies first."
- Review `package.json` changes in every code review
- Use `npx npm-check-updates` to audit additions periodically

### 4. The "It Works" Trap

**Description:** AI-generated code produces correct output for the demo scenario. Developer ships based on visual correctness without testing edge cases. Failures appear in production.

**Detection signals:**
- No test coverage on AI-generated features
- Features tested only by clicking through them manually
- Errors appear only when real users interact with the system
- Bug reports cluster around AI-generated features after launch

**Root cause:** AI handles happy paths well. The demo scenario is a happy path by definition. AI rarely generates code that handles: empty lists, null values, network timeouts, concurrent modifications, invalid Unicode, or malformed input.

**Recovery:**
1. Run security audit (see `references/quality-guardrails.md`)
2. Add tests for every bug report received
3. Systematically test edge cases for each feature
4. Add error handling for each discovered gap

**Prevention:**
- Generate tests before (or alongside) implementation
- Test edge cases explicitly: empty, null, max-length, concurrent, offline
- Use the "junior dev PR" mental model for all reviews
- Automate validation in CI (types, lint, tests, security scan)

### 5. Hallucinated APIs and Libraries

**Description:** AI generates code that calls APIs, methods, or configuration options that don't exist. The code looks correct syntactically but references fictional interfaces.

**Detection signals:**
- TypeScript errors on non-existent properties or methods
- Runtime errors: "X is not a function" or "X is not defined"
- Import statements for packages that don't exist or wrong versions
- Configuration options that have no effect

**Common hallucination patterns:**

| Category | Example |
|----------|---------|
| Fictional npm packages | `import { magic } from 'react-magic-table'` (doesn't exist) |
| Wrong API version | Using Next.js 15 API in a Next.js 14 project |
| Invented methods | `array.groupBy()` (not standard JavaScript) |
| Mixed framework APIs | React hooks in a Vue component pattern |
| Deprecated features | Using removed APIs from older versions |

**Recovery:**
1. Run `tsc --noEmit` to catch type errors from hallucinated APIs
2. Verify every import resolves to an actual installed package
3. Check API documentation for every method call that looks unfamiliar
4. Replace hallucinated APIs with real equivalents

**Prevention:**
- Specify exact versions in rules files: "Next.js 14.2, not 15"
- Include relevant documentation snippets in context
- Run type checking after every generation
- Be skeptical of unfamiliar APIs — verify before trusting

### 6. Security Blind Spots

**Description:** 45% of vibe-coded applications contain at least one security vulnerability (pixelmojo.io, 2026). AI generates code that is functionally correct but security-insufficient.

**Common vulnerabilities in AI-generated code:**

| Vulnerability | How AI Gets It Wrong |
|--------------|---------------------|
| Missing input validation | Trusts all input from forms and API calls |
| Hardcoded secrets | Puts API keys directly in source code |
| SQL injection | String interpolation in database queries |
| Missing auth checks | Protects the UI but not the API endpoints |
| Overly permissive CORS | Sets `Access-Control-Allow-Origin: *` |
| Insecure defaults | Creates admin accounts with weak passwords |
| Missing rate limiting | No protection against brute force |
| Exposed error details | Stack traces in API error responses |

**Recovery:** See `references/quality-guardrails.md` for the full security scanning pipeline.

**Prevention:**
- Add security requirements to rules files
- Run SAST tools (Semgrep, ESLint security) on every generation
- Never let AI write auth, encryption, or access control without line-by-line review
- Use database ORMs with parameterized queries (Prisma, Drizzle)

### 7. Over-Reliance Erosion

**Description:** Developer gradually loses the ability to read, debug, and understand code. Prompts become "fix this" without understanding what's broken. The developer becomes a prompt-relay between error messages and the AI.

**Detection signals:**
- Cannot explain what the code does without AI help
- Debug strategy is "paste error into AI" without reading the error
- Cannot write a simple function without AI assistance
- Architecture decisions delegated entirely to AI
- Unable to evaluate whether AI output is correct

**Root cause:** Vibe coding is seductive. Speed feels like productivity. The developer stops engaging with the code mentally and becomes a prompt operator rather than an engineer.

**Recovery:**
1. For every AI-generated function, write a one-line comment explaining what it does
2. Read error messages fully before prompting the AI
3. Attempt a manual fix before asking AI to fix it
4. Periodically code small features without AI to maintain skill
5. Understand the architecture at the module level even if not every line

**Prevention:**
- Set a "no AI" time block weekly for manual coding practice
- Always understand the data model and architecture
- Review AI output for understanding, not just correctness
- Be able to answer: "What does this file do?" for every file in the project

### 8. Prompt Chasing

**Description:** Spending more time crafting perfect prompts and iterating with the AI than it would take to write the code manually. The AI produces 80% of what's needed, and the last 20% takes five prompts to get right.

**Detection signals:**
- 5+ prompt iterations for a single function
- More time debugging AI output than writing from scratch would take
- Prompts become increasingly specific and prescriptive (essentially writing pseudocode)
- Frustration cycle: prompt, reject, re-prompt, reject, re-prompt

**Recovery:**
1. After 3 failed prompts, write the code manually
2. Use the AI-generated 80% and manually edit the remaining 20%
3. Save working patterns as reference examples for future prompts

**Prevention:**
- Two-attempt rule: if two prompts don't produce 90%+ correct output, write it manually
- Accept that AI is an accelerator, not a replacement for coding skill
- Use AI for generation, not for pixel-perfect control

## Organizational Failure Modes

| Failure Mode | Description | Mitigation |
|-------------|-------------|------------|
| No quality standards for AI code | AI output shipped without review | Treat AI code with same PR standards as human code |
| Inconsistent tooling across team | Each developer uses different AI tools with different conventions | Standardize on AGENTS.md + one primary tool |
| Knowledge concentration | Only the AI operator understands the system | Architecture docs, pair programming, code reviews |
| Estimation blindness | Assuming AI makes everything instant | Account for review, testing, and iteration time |
| Security theater | "AI wrote it, it must be secure" | Mandatory security review for all shipped code |

## Recovery Decision Tree

```
Problem identified
|
+-- Security vulnerability
|   +-- P0: Fix immediately, review all similar code
|
+-- Architecture inconsistency
|   +-- Document canonical pattern in rules
|   +-- Refactor incrementally (not all at once)
|
+-- Test coverage gap
|   +-- Generate tests for critical paths first
|   +-- Expand coverage progressively
|
+-- Dependency bloat
|   +-- Audit with knip/depcheck
|   +-- Remove unused, replace trivial packages
|
+-- Context drift in session
|   +-- Commit working code
|   +-- Start fresh conversation
|   +-- Restate constraints from rules files
|
+-- Developer skill erosion
    +-- Weekly manual coding practice
    +-- Read code before prompting AI to fix it
    +-- Explain architecture without AI assistance
```

## Monitoring Thresholds

Track these metrics to detect failure modes early:

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Type errors (tsc) | 0 | 1-5 | 5+ |
| Security vulnerabilities (npm audit) | 0 critical | 1 moderate | Any critical |
| Test coverage (critical paths) | 80%+ | 60-80% | Under 60% |
| Dependency count growth/month | 0-2 | 3-5 | 5+ |
| Prompt iterations per feature | 1-3 | 4-6 | 7+ |
| Bug reports on AI-generated features | Below average | At average | Above average |
