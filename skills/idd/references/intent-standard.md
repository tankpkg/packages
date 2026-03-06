# Intent File Standard

Sources: ArcBlock/idd intent-standard v1.1 (MIT), Praxis templates (MIT),
FORGE PRD format (MIT), synthesized into one opinionated format.

Covers: INTENT.md structure, frontmatter, anchor rules, three-layer model,
size budget, supporting file formats (dependencies, boundaries, decisions).

## INTENT.md Anatomy

Every intent file follows this skeleton:

```markdown
---
status: active
---

# Auth Module Intent

> Anchor: Handle user authentication and session management for the web app.
> Depends: .idd/modules/database
> See also: planning/auth-research.md

## Responsibilities

- What this module does (3-5 bullets)
- What it explicitly does NOT do

## Structure

` ` `
src/auth/
├── middleware/
│   ├── jwt.ts           # Token verification
│   └── session.ts       # Session lifecycle
├── routes/
│   ├── login.ts
│   └── logout.ts
└── index.ts             # Public API surface
` ` `

## Constraints

| Rule | Rationale |
|------|-----------|
| Never import from `src/payments/` | Auth must not know about billing |
| Session TTL must be configurable | Different environments need different timeouts |
| All auth errors return 401, never 403 | Prevent information leakage about resource existence |

## API

### authenticate(credentials: Credentials): Promise<Session>

**Parameters:**
- `credentials.email` — user email (validated, lowercase)
- `credentials.password` — plaintext (hashed internally, never stored)

**Returns:** `Session { id, userId, expiresAt }`

**Constraints:**
- Rate limit: 5 attempts per minute per IP
- Lock account after 10 consecutive failures

## Examples

| Input | Output |
|-------|--------|
| `authenticate({ email: "valid@test.com", password: "correct" })` | `Session { status: "active" }` |
| `authenticate({ email: "valid@test.com", password: "wrong" })` | `AuthError { code: "INVALID_CREDENTIALS" }` |
| `authenticate({ email: "locked@test.com", password: "any" })` | `AuthError { code: "ACCOUNT_LOCKED" }` |
```

## The Anchor

The anchor is the single most important line in any intent file. It's
a one-sentence declaration of why this module exists.

**Rules:**
- One or two sentences maximum. Not a paragraph.
- Immediately after the H1 title, in a blockquote
- Every section in the file must trace back to it
- If you can't connect a section to the anchor, the section doesn't belong

**Good anchors:**
- `> Anchor: Enable type-safe binary communication between nodes.`
- `> Anchor: Handle user authentication and session management.`
- `> Anchor: Transform raw event streams into queryable aggregates.`

**Bad anchors:**
- `> Anchor: This module does various things related to users.` (vague)
- `> Anchor: Provide a flexible, extensible, plugin-based architecture
  for handling multiple authentication providers with support for
  future expansion.` (over-engineered, too long)

## Dependency and Reference Tags

Two optional tags follow the anchor:

```markdown
> Depends: .idd/modules/database, .idd/modules/config
> See also: planning/auth-research.md, planning/competitor-analysis.md
```

- **Depends** — other intents this one requires. Only direct dependencies,
  not transitive. Used by audit to build the dependency graph and detect
  orphaned intents.
- **See also** — planning docs, research, external URLs that informed this
  intent. Informational only, no graph edges.

## Frontmatter

Optional YAML frontmatter for machine-readable metadata:

```yaml
---
status: active
needs: [critique]
---
```

- **status**: `active` | `implemented` | `shelved` | `abandoned` | `superseded`
- **needs**: pickup signals — what processing this intent still requires
- **superseded_by**: path to replacement (only when `status: superseded`)

Omitting frontmatter entirely means `status: active`. Keep it minimal —
prose belongs in the document body, not YAML fields.

### Needs — Pickup Signals

The `needs` field flags pending work:

| Value | Meaning | What to do |
|-------|---------|------------|
| `anchor` | Missing or weak anchor | Run interview |
| `critique` | Over budget or stale | Run critique |
| `review` | Sections need human approval | Run review |
| `sync` | Code may have drifted | Run sync check |

Remove values as they're addressed. Delete the field when empty.

## The Three Layers In Practice

### Layer 1: Structure Diagrams

Draw the module's shape. Directory trees, data flow, component relations.
ASCII art is the primary medium — not Mermaid, not prose.

**Why ASCII?** Every LLM and every terminal renders it identically. No
toolchain dependency. Instantly scannable by humans and machines alike.

```
                    Request
                      │
              ┌───────┴───────┐
              │   API Router  │
              └───┬───────┬───┘
                  │       │
          ┌───────┴──┐ ┌──┴────────┐
          │ Auth MW  │ │ Rate Limit│
          └───────┬──┘ └───────────┘
                  │
          ┌───────┴──────┐
          │  Session DB  │
          └──────────────┘
```

### Layer 2: Constraint Rules

Constraints are testable rules. Write them as tables, not paragraphs.
Each constraint should convert directly into a lint rule or test assertion.

**Format: table with rule + rationale**

| Constraint | Rationale |
|------------|-----------|
| Auth module never imports from payments | Prevent billing logic leaking into auth |
| All DB queries use parameterized statements | SQL injection prevention |
| Response time < 200ms at p95 | SLA requirement |
| Max 3 retries with exponential backoff | Prevent thundering herd on downstream failure |

**Not constraints (move to planning/):**
- Background analysis ("OAuth2 has four grant types...")
- Exploration notes ("We could use Redis or Memcached...")
- Comparisons without a decision ("Pros and cons of JWT vs sessions")

### Layer 3: Behavior Examples

Concrete input-output pairs. Each one maps directly to a test case.
Include happy paths, error cases, and edge cases.

**Table format (preferred):**

| Input | Output | Notes |
|-------|--------|-------|
| `login("valid@test.com", "correct")` | `Session { active: true }` | Happy path |
| `login("valid@test.com", "wrong")` | `Error { code: 401 }` | Bad credentials |
| `login("locked@test.com", "any")` | `Error { code: 423 }` | After 10 failures |
| `login("", "any")` | `Error { code: 400 }` | Missing email |

## Size Budget

Intent files bloat naturally. Every interview adds content, every
discussion adds "just one more section." Fight this actively.

| Lines | Status | What happens |
|-------|--------|-------------|
| ≤ 300 | Healthy | Normal operation |
| 300–500 | Warning | Flag for review. Consider splitting. |
| > 500 | Blocked | All work stops. Run critique. Must net-reduce before continuing. |

Frontmatter lines don't count toward the budget.

**When you hit the ceiling:**
1. Does every section serve the anchor? Cut what doesn't.
2. Is background analysis mixed in? Move it to `planning/`.
3. Can this intent split into two module-level intents?
4. Are constraints and examples duplicated? Consolidate.

## Supporting Files

### decisions.md

Output of the interview phase. Flat list of questions, decisions, and
rationale. Does not duplicate INTENT.md — the two files serve different
purposes. Decisions captures *why we chose X over Y*. Intent captures
*what we're building*.

```markdown
# Interview Decisions: Auth Module

> Anchor: Handle user authentication and session management.

## Decisions

### 1. Session Storage
- **Question**: Where do we store sessions?
- **Decision**: Redis with 24h TTL
- **Rationale**: Need shared sessions across instances. DB is too slow for
  per-request lookups.

### 2. Token Format
- **Question**: JWT or opaque tokens?
- **Decision**: Opaque tokens with server-side session lookup
- **Rationale**: JWTs can't be revoked without a blocklist, which defeats
  the purpose. Opaque tokens with Redis give us instant revocation.

## Open Items
- MFA provider selection (blocked on vendor evaluation)

## Out of Scope
- Social login (separate module, separate intent)
```

### dependencies.md

Module dependency graph. ASCII diagram primary, matrix secondary.

```markdown
# Module Dependencies

## Dependency Graph

` ` `
    API
     │
  ┌──┴──┐
  ▼     ▼
Auth  Payments
  │     │
  └──┬──┘
     ▼
  Database
` ` `

## Dependency Matrix

|          | Auth | Payments | Database | Config |
|----------|------|----------|----------|--------|
| API      | OK   | OK       | NO       | OK     |
| Auth     | -    | NO       | OK       | OK     |
| Payments | NO   | -        | OK       | OK     |
| Database | NO   | NO       | -        | OK     |

OK = allowed. NO = forbidden. - = self.
```

### boundaries.md

Explicit forbidden patterns with verification commands.

```markdown
# Boundary Rules

## Principles
- Dependencies flow downward: API → Services → Data
- No lateral imports between peer services
- All cross-module communication through public API

## Forbidden Patterns

| Source | Forbidden Import | Why |
|--------|-----------------|-----|
| `src/auth/` | `src/payments/*` | Auth must not know about billing |
| `src/api/` | `src/*/internal/*` | API layer uses public exports only |
| Any module | `src/database/migrations/*` | Migrations are not runtime code |

## Verification

` ` `bash
# Detect forbidden auth → payments imports
grep -r "from.*payments" src/auth/
# Should return nothing
` ` `
```

### records/ Directory

Append-only archive of raw inputs — interview transcripts, critique
reports, review decisions. Never edit old records. Each record gets an
entry in `INDEX.md`.

```markdown
# Records Index

| Date | Type | Summary |
|------|------|---------|
| 2026-03-01 | interview | Initial auth module interview |
| 2026-03-05 | critique | Reduced from 420 to 290 lines |
| 2026-03-06 | review | Locked API signatures section |
```

### planning/ Directory

Lives alongside `.idd/`, NOT inside it. This is the divergent space —
ideas, research, competitor analysis, user feedback. No budget constraint.
Content here feeds into intent files when it solidifies into decisions.

```
project/
├── .idd/          # Convergent: specs, constraints, testable
└── planning/      # Divergent: exploration, ideas, research
    ├── auth-research.md
    ├── competitor-analysis.md
    └── user-feedback-q1.md
```

**The key distinction:** planning is exploratory, intent is definitive.
If you're writing "we could do X or Y," that's planning. If you're
writing "we will do X because Z," that's intent.
