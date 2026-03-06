# Writing Good Intent

Sources: ArcBlock/idd methodology (MIT), FORGE Refine phase (MIT),
Praxis intent templates (MIT), production intent analysis.

Covers: Diagrams-first writing, constraint table format, behavior
example pairs, organizing by module, anti-patterns with corrections.

## The Golden Rule

If an AI reads your INTENT.md and builds the wrong thing, the intent
was bad — not the AI. Intent quality directly predicts implementation
quality. Garbage in, garbage out, but with more ceremony.

---

## Diagrams First, Words Second

The single biggest upgrade to any intent file is replacing paragraphs
with ASCII diagrams. Here's why:

**Paragraph version (bad):**
> The authentication module sits between the API router and the database
> layer. Incoming requests first pass through rate limiting, then through
> the auth middleware which validates the session token. If valid, the
> request proceeds to the business logic handler. The session store uses
> Redis for performance, while user credentials live in PostgreSQL.

**Diagram version (good):**
```
    Request
       │
   ┌───┴───┐
   │ Router │
   └───┬───┘
       │
  ┌────┴────┐    ┌───────────┐
  │Rate Limiter├──│ Redis     │
  └────┬────┘    │ (counters)│
       │         └───────────┘
  ┌────┴────┐    ┌───────────┐
  │Auth MW  ├────│ Redis     │
  └────┬────┘    │ (sessions)│
       │         └───────────┘
  ┌────┴────┐    ┌───────────┐
  │Handler  ├────│ PostgreSQL│
  └─────────┘    │ (users)   │
                 └───────────┘
```

The diagram says the same thing in a form that's:
- Instantly scannable (you see the flow in 2 seconds)
- Unambiguous (no interpreting prose)
- LLM-native (tokenizes efficiently, parses reliably)
- Diff-friendly (changes are visually obvious)

### Directory Trees

Show the module's file layout. Label files with their responsibility.

```
src/auth/
├── middleware/
│   ├── jwt.ts           # Token verification + refresh
│   └── rate-limit.ts    # Per-IP throttling
├── routes/
│   ├── login.ts         # POST /auth/login
│   ├── logout.ts        # POST /auth/logout
│   └── refresh.ts       # POST /auth/refresh
├── store/
│   ├── session.ts       # Redis session CRUD
│   └── user.ts          # PostgreSQL user lookup
└── index.ts             # Public exports (nothing else)
```

### Data Structure Diagrams

Show relationships, not just fields.

```
┌─────────────┐       ┌──────────────┐
│ User        │       │ Session      │
├─────────────┤  1:N  ├──────────────┤
│ id: uuid    │───────│ id: uuid     │
│ email: str  │       │ userId: uuid │
│ hash: str   │       │ expiresAt: ts│
│ lockedAt: ts│       │ ip: str      │
└─────────────┘       └──────────────┘
```

---

## Writing Constraints That Convert to Tests

A constraint is only useful if you can test it. "The system should be
secure" is useless. "All inputs are sanitized against XSS" is testable.

### The Format

Use tables with two columns: the rule and why it exists.

| Constraint | Rationale |
|------------|-----------|
| `auth/` never imports from `payments/` | Billing logic must not leak into auth |
| Login endpoint rate-limited to 5/min/IP | Brute-force prevention |
| Session tokens are UUID v4 (122 bits entropy) | Prevent guessing attacks |
| Password hash uses bcrypt with cost factor 12 | Industry-standard resistance to offline cracking |
| Failed login counter resets after successful login | Prevent permanent lockout from occasional typos |

### Good vs Bad Constraints

| Bad (vague, untestable) | Good (specific, testable) |
|------------------------|--------------------------|
| "System should be fast" | "p95 response time < 200ms under 100 concurrent users" |
| "Handle errors gracefully" | "All errors return `{ code, message }` with HTTP status" |
| "Support multiple databases" | "Uses PostgreSQL. No abstraction layer." |
| "Secure authentication" | "Bcrypt cost 12. Lock after 10 failures. Unlock after 30min." |
| "Scalable architecture" | "Stateless handlers. Session state in Redis. No local disk." |

### What Doesn't Belong in Constraints

Move these to `planning/`:

- Background research ("OAuth2 supports four grant types...")
- Open comparisons ("Redis vs Memcached: pros and cons...")
- Future possibilities ("We might want to add WebSocket support...")
- Implementation notes ("Use the `bcrypt` npm package v5.1")

Constraints are decisions. If you haven't decided, it's still planning.

---

## Writing Examples That Become Tests

Layer 3 examples map directly to test cases. Write them as input-output
pairs, not as prose narratives.

### Table Format (best for APIs)

| Input | Output | Category |
|-------|--------|----------|
| `login("alice@test.com", "correct")` | `Session { id, expiresAt }` | Happy |
| `login("alice@test.com", "wrong")` | `AuthError { code: "INVALID_CREDS" }` | Error |
| `login("locked@test.com", "any")` | `AuthError { code: "ACCOUNT_LOCKED" }` | Error |
| `login("", "any")` | `ValidationError { field: "email" }` | Edge |
| `login("a@b.c", "x".repeat(10000))` | `ValidationError { field: "password" }` | Edge |
| 6th login attempt in 60s from same IP | `RateLimitError { retryAfter: 60 }` | Security |

### Scenario Format (best for workflows)

```
Scenario: User logs in successfully
  Setup: User "alice" exists with known password
  Action: POST /auth/login { email: "alice@test.com", password: "correct" }
  Result: 200 { session: { id: uuid, expiresAt: future } }
  Side effect: Session stored in Redis with 24h TTL

Scenario: Account locks after 10 failures
  Setup: User "bob" exists, 9 failed attempts recorded
  Action: POST /auth/login { email: "bob@test.com", password: "wrong" }
  Result: 423 { code: "ACCOUNT_LOCKED", unlockAt: now + 30min }
  Side effect: lockedAt set on user record
```

### Coverage Checklist

For each API endpoint or function, aim for examples covering:

| Category | What to test | Minimum count |
|----------|-------------|---------------|
| Happy path | Normal successful operation | 2-3 |
| Error path | Known failure modes | 3-5 (more than happy paths) |
| Edge cases | Boundaries, empty inputs, extremes | 2-3 |
| Security | Auth bypass attempts, injection, brute force | 2-3 |
| Data integrity | Concurrent access, partial failures | 1-2 |
| Destructive ops | Delete, revoke, bulk operations | 1-2 |

Error path examples should outnumber happy path examples. There are
more ways to fail than to succeed.

---

## Organizing by Module

Never organize intent by requirement type (functional, UX, technical).
Always organize by module. Each module gets its own INTENT.md.

### Why?

An LLM implementing the auth module needs ALL auth context in one place:
the data structures, the API, the constraints, the examples. If the
data structures are in `functional-requirements.md` and the security
constraints are in `technical-requirements.md`, the LLM has to assemble
the full picture from fragments. It will miss things.

### Splitting Intent

When a single INTENT.md is getting too large (approaching 500 lines),
split by module boundary — not by topic.

**Bad split (by topic):**
```
.idd/
  auth-api.intent.md          # API endpoints
  auth-data.intent.md         # Data structures
  auth-security.intent.md     # Security constraints
```

**Good split (by module):**
```
.idd/modules/
  auth/INTENT.md              # Everything about auth
  session/INTENT.md           # Session management (extracted)
  rate-limiting/INTENT.md     # Rate limiting (extracted)
```

Each split module gets its own anchor, its own three layers, its own
budget. The `Depends:` tag maintains the connection.

---

## Common Anti-Patterns

### 1. The Novel

A 900-line INTENT.md that reads like a technical specification document
from 2005. Background research, market analysis, competitor comparison,
architecture decision records, and somewhere buried in there, the actual
module design.

**Fix:** Extract everything that isn't structure/constraints/examples
into `planning/`. Enforce the 500-line budget.

### 2. The Wish List

```markdown
## Future Enhancements
- Support SAML
- Support LDAP
- Support biometric auth
- Support passwordless via WebAuthn
- Support social login (Google, GitHub, Apple)
```

**Fix:** Delete the entire section. YAGNI. When you need SAML, write
a SAML intent. Don't pollute today's intent with tomorrow's maybes.

### 3. The Implementation Guide

```markdown
## How to Implement
1. Install bcrypt: `npm install bcrypt`
2. Create a hash function in utils/crypto.ts
3. Use cost factor 12 for production
4. Store the hash in the `password_hash` column
```

**Fix:** Replace with a constraint. "Passwords hashed with bcrypt,
cost factor 12." The AI knows how to use bcrypt. Tell it what to
achieve, not how to type it.

### 4. The Orphan

An INTENT.md that references modules, data structures, and APIs that
don't exist in the codebase and were never implemented. Nobody removed
the intent when the feature was cancelled.

**Fix:** Run sync to detect orphans. Move abandoned intents to `_archive/`
via `git mv`. Never delete — the history has value.

### 5. The Mirror

Intent that just describes what the code already does, written after
the code was shipped. Adds no value — it's documentation, not intent.

**Fix:** Intent drives code, not the other way around. If you're writing
intent for existing code, focus on the *constraints and boundaries* that
aren't obvious from reading the code. What should never change? What
invariants must hold? That's the value-add.
