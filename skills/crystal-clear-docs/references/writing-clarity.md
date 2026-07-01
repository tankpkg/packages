# Writing for Clarity: Words and Comparisons

Sources: Strunk & White (The Elements of Style, 1918), William Zinsser (On Writing Well, 1976), Google Technical Writing Course (One), Steve Krug (Don't Make Me Think — Chapter 5: Omit Needless Words), Robert Horn (Information Mapping).

Covers: Word-level and sentence-level techniques for crystal-clear technical writing. Active voice, eliminating jargon, sentence construction, comparison patterns, worked examples, and the MECE framework for structuring arguments.

## The Core Principle

**Every word must earn its place.** If removing a word changes nothing, remove it. If a simpler word works, use it. Clarity is not about dumbing down — it's about respecting the reader's time and attention.

## Omit Needless Words (Krug + Strunk & White)

Before:
> "In order to successfully authenticate the user's credentials, it is necessary for the system to verify the provided password against the hashed value that has been previously stored in the database."

After:
> "The system checks the password against the stored hash."

Technique: Write the sentence. Delete every word. Re-add only what's essential to convey the meaning. You will re-add about 40% of the original.

## Active Voice

Active voice makes actors visible and responsibility clear.

| Passive | Active |
|---------|--------|
| "The configuration file should be updated." | "Update the configuration file." |
| "Errors are logged to the console." | "The server logs errors to the console." |
| "The token is verified before access is granted." | "The API verifies the token before granting access." |

**When passive voice is acceptable**: The actor is irrelevant or unknown ("The server was compromised"), or you want to emphasize the recipient over the actor.

## Define Terms on First Use

Every new or unfamiliar term gets defined the first time it appears. Definition goes in the same sentence or the very next one.

**Good**:
> "The system uses JWT (JSON Web Token) — a compact, URL-safe token that proves identity without server-side session storage."

**Bad**:
> "The system uses JWT."
> *(reader Googles "JWT" and doesn't come back)*

## Eliminating Jargon

Jargon is domain-specific vocabulary your reader may not know. The test: would your next-door neighbor understand this term?

| Jargon | Plain Alternative |
|--------|-------------------|
| "Implement a pub/sub pattern" | "Set up a message system where one service publishes and others subscribe" |
| "Utilize a monorepo architecture" | "Keep all code in a single repository" |
| "Leverage horizontal scaling" | "Add more servers instead of bigger servers" |
| "Idempotent operation" | "Safe to retry — running it twice has the same effect as running it once" |

**Exception for developer docs**: Domain-appropriate jargon is fine IF defined on first use. Developers know "idempotent" — but still define it. Your more junior readers don't know it yet.

## Sentence Construction

### Length

- Core sentences: 15-20 words
- Limit: 25 words maximum
- If a sentence runs longer, split it. If splitting loses meaning, use a list.

### Structure

Lead with the subject and verb. Don't make readers hold context while you set up.

**Before**:
> "After considering the various authentication approaches available, including OAuth 2.0, API keys, and session-based auth, and weighing their respective tradeoffs in terms of security, implementation complexity, and user experience, the team decided to implement JWT-based authentication."

**After**:
> "The team chose JWT-based authentication. It balances security, implementation simplicity, and user experience better than OAuth 2.0, API keys, or session-based auth."

## Comparison Patterns

### Side-by-Side Table — for multiple options, multiple criteria

| Feature | Method A | Method B | Method C |
|---------|----------|----------|----------|
| Speed | Fast | Medium | Slow |
| Setup | Simple | Complex | Medium |
| Security | Basic | Enterprise | Standard |
| **Best for** | Prototypes | Production | Internal tools |

### Pros/Cons List — for evaluating a single option

```
### JWT Authentication

**Pros**
- Stateless — no server-side session storage
- Works across domains (no CORS issues)
- Compact (URL-safe)

**Cons**
- Cannot revoke individual tokens
- Token size grows with claims
- Requires token refresh mechanism
```

### When to Use Which

| Situation | Format |
|-----------|--------|
| Choosing between 2+ options | Side-by-side table |
| Evaluating whether to use X | Pros/Cons list |
| Contrasting old vs new approach | Before/After paired boxes |
| Showing step-by-step difference | Numbered old flow vs numbered new flow |

## Worked Examples

A worked example takes a realistic scenario (not a contrived toy) and walks through it completely. It includes: the setup, the happy path, common errors, and the final state.

### Structure of a Good Worked Example

```
### Example: Adding Authentication to a REST API

**The scenario**: You have an existing Express API for a todo app.
Currently, anyone can read or modify any todo. You need to add
user-specific authentication.

**Step 1**: Install and configure the auth library.
[Code block with exactly what to run]

**Step 2**: Add the auth middleware to protected routes.
[Code block showing before/after]

**Step 3**: Test that unauthenticated requests are rejected.
[Terminal output showing 401 response]

**Step 4**: Test that authenticated requests succeed.
[Terminal output showing 200 response]

**What just happened**: [Explanation of the mechanism]

**Common pitfalls**:
- Forgetting to add the middleware to ALL protected routes → use router-level middleware
- Storing tokens in localStorage → use httpOnly cookies instead
```

### Why Worked Examples Work

1. Readers learn by doing, not reading about doing
2. A realistic example surfaces real-world edge cases
3. They validate the documentation (if the example doesn't work, the docs are wrong)

## MECE Framework for Structuring Arguments

From Barbara Minto's Pyramid Principle: arguments should be **M**utually **E**xclusive and **C**ollectively **E**xhaustive.

- **Mutually Exclusive**: No overlap between categories. Each item appears in exactly one place.
- **Collectively Exhaustive**: Together, the categories cover everything. Nothing is left out.

Applied to documentation:

**Non-MECE** (overlap + gaps):
- Authentication methods: API keys, OAuth, JWT, Bearer tokens
- Problem: JWT and Bearer tokens overlap

**MECE**:
- Authentication methods:
  - Server-side: Session cookies, API keys stored in DB
  - Client-side: JWT tokens
  - Delegated: OAuth 2.0

## BLUF: Bottom Line Up Front

Military communication principle: state the conclusion first, then provide supporting reasoning. This is the written equivalent of the inverted pyramid.

In practice:
- The document's first sentence IS the conclusion
- Supporting evidence follows
- The reader never wonders "where is this going?"

## Anticipating Reader Questions

The best technical writing answers questions before they're asked. For every claim, ask:

- **"So what?"** — Why does this matter to the reader? If you can't answer, cut it.
- **"Why is that true?"** — What's the evidence? If you can't provide it, the claim is weak.
- **"What could go wrong?"** — What happens if the reader makes the wrong choice? Warn them.

## Quality Checklist for Clarity

- [ ] Every term defined on first use (with a single sentence, in context)
- [ ] Zero passive voice where active voice would be clearer
- [ ] Every sentence under 25 words (or split/listed)
- [ ] No word can be removed without losing meaning
- [ ] Every code block is copy-paste runnable
- [ ] Every "why" question the reader might ask is answered (or linked)
- [ ] First paragraph tells the reader exactly what they'll get

## Information Mapping (Robert Horn)

A framework for breaking content into structured, reusable blocks based on the type of information. Every block of content should be classified as one of these types, and each type should follow a consistent format:

| Block Type | Purpose | Format Pattern |
|-----------|---------|----------------|
| **Concept** | Define or explain an idea | Definition → Examples → Non-examples → Related concepts |
| **Procedure** | Steps to complete a task | Prerequisites → Ordered Steps (numbered) → Expected Result → Troubleshooting |
| **Process** | How something works (system behavior) | Overview → Stages (sequential) → Feedback at each stage → Output |
| **Principle** | Rules, guidelines, best practices | Rule statement → Rationale → When to apply → Exceptions |
| **Fact** | Reference data, specifications | Data point → Context → Source → Caveats |

Each block should be self-contained and labeled so readers can identify the type at a glance. This lets them skip procedure blocks when they want concepts, or skip concepts when they want to execute.

## The Three-Pass Editing Process

From Google's Technical Writing course and Zinsser:

### Pass 1: Structure
- Does the document open with a TL;DR that answers "what is this about?"
- Are sections in logical order?
- Do headings accurately compress their content?
- Can a reader self-select their depth?

### Pass 2: Clarity
- Replace every passive voice construction with active (where possible)
- Split every sentence over 25 words
- Convert every 3-item prose list to a bulleted or numbered list
- Define every jargon term on first use
- Bold every key term exactly once (on first mention)

### Pass 3: Conciseness
- Read each sentence. Delete every word. Re-add only what's essential.
- Remove: "It should be noted that", "In order to", "The fact that", "Due to the fact that"
- Replace: "utilize" → "use", "implement" → "build", "leverage" → "use", "facilitate" → "help"
- Delete any sentence repeating what the code block already shows
- Cut adjectives and adverbs that don't add precision (most don't)

## The Curse of Knowledge

The single biggest obstacle to clear technical writing: you know too much. Once you understand something deeply, you cannot imagine what it's like not to understand it. This causes three specific failures:

1. **Unexplained prerequisites**: You assume the reader knows X, but they don't.
2. **Jargon without context**: You use terms fluently without defining them.
3. **Skipped steps**: You leap from A to C because B is so obvious to you.

**Counter-measures**:
- Write the prerequisites section BEFORE the content. Be ruthlessly explicit.
- Have a non-expert read your draft. Every place they pause or ask "what's that?" — add explanation.
- Run your TL;DR through the Up-Goer Five test: can you explain the core idea in only common words?

## Handling Different Audience Levels

Most technical documents have a split audience: beginners who need everything explained, and experts who just need the reference. Structure accommodates both:

| Section | Serves | Content |
|---------|--------|---------|
| TL;DR + Quickstart | Both | Answer; simplest working example |
| Overview / Concepts | Beginners | What it is, why it exists, core ideas |
| How-To Guides | Intermediate | Task-based, realistic workflows |
| API Reference | Experts | Complete, exhaustive parameter/type docs |
| Architecture / Internals | Advanced | Design decisions, tradeoffs, implementation details |

The key: a beginner reads top-to-bottom. An expert jumps to API Reference. Neither is forced to wade through content they don't need.

## Error Messages as Documentation

Error messages are the most-read documentation you'll ever write. A good error message:

1. **Says what happened** — in plain language, not error codes
2. **Says why it happened** — what condition caused it
3. **Says what to do** — the specific action that fixes it

**Bad**: `Error: EACCES: permission denied`
**Good**: `Cannot write to /etc/config.json — you don't have permission. Run with sudo or change the file owner: chown $USER /etc/config.json`

### Error Message Template

```
[What happened]: [plain language description]
[Symptoms]: [what the user sees]
[Cause]: [why this happened]
[Fix]: [specific action to resolve]
[If that doesn't work]: [fallback / support link]
```

## Formatting References and Further Reading

Every document should end with clear paths forward. Three levels:

1. **Next logical step**: If the reader completed this document, what should they do next?
2. **Related topics**: Tangential documentation that provides context or alternatives.
3. **External references**: Official docs, RFCs, seminal blog posts that informed the content.

Format:
```markdown
## What's Next

- **[Next Step: Add Role-Based Authorization](./authorization.md)** — now that authentication works, restrict what each user can do.
- **[Alternative: OAuth 2.0](./oauth.md)** — if you need delegated auth instead of JWT.
- **See also**: [JWT RFC 7519](https://tools.ietf.org/html/rfc7519), [jwt.io debugger](https://jwt.io)
```

## Voice and Tone

Technical documentation is not academic writing. The best docs sound like a knowledgeable colleague explaining something to you directly. The voice is:

- **Confident, not cold**: "Here's how it works" not "The system operates in the following manner"
- **Direct, not distant**: Use "you" for the reader. "You'll need to install..." not "The user must install..."
- **Honest about tradeoffs**: "This approach is simpler but slower" not "This approach may have performance implications"
- **Respectful of the reader's intelligence**: Assume competence. Don't condescend. Don't over-explain the obvious.

## The 30-Second Test

A reader should be able to determine, within 30 seconds of opening your document:
1. What this page is about
2. Whether it's relevant to them
3. What they need to do

If they cannot, the document has failed regardless of how good the deep content is.
