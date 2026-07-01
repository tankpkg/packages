# Context Engineering

Sources: vexp.dev (Context Engineering for AI Coding Agents, 2026), kilo.ai (Beyond Vibe Coding: Prompt and Context Engineering, 2026), vibecoding.app (Advanced Vibe Coding, 2026), Anthropic Claude Code documentation, Cursor documentation (2026)

Covers: context window management, anti-drift strategies, project documentation for AI consumption, type-driven context, conversation hygiene, and file referencing patterns.

## From Prompt Engineering to Context Engineering

Prompt engineering optimizes the instruction. Context engineering optimizes the environment so the AI cannot fail. Instead of crafting clever prompts, structure the project so the right answer becomes obvious.

| Prompt Engineering | Context Engineering |
|-------------------|---------------------|
| Craft the perfect question | Structure the codebase so any question works |
| Per-interaction optimization | Persistent, reusable optimization |
| Skill of the prompter | Property of the project |
| Fragile (depends on exact wording) | Robust (works across phrasings) |

Context engineering is the successor to prompt engineering for code generation. Invest in project structure, not prompt tricks.

## The Context Window

Every AI tool has a finite context window — the total text the model can consider at once. This window holds:

- System prompt and rules files
- Conversation history
- Referenced files and documentation
- The current prompt

When the window fills, older content gets pushed out. This causes drift: the AI forgets earlier decisions and starts contradicting itself.

### Window Budget Management

| Content Type | Priority | Strategy |
|-------------|----------|----------|
| Rules files | Highest | Always loaded, keep concise |
| Current file being edited | High | Auto-included by most tools |
| Referenced files (@ mentions) | High | Include only what's relevant |
| Conversation history | Medium | Start fresh for new features |
| Full codebase scan | Low | Let the tool decide what's relevant |

### Window Size by Tool (Approximate, 2026)

| Tool | Context Window | Effective Capacity |
|------|---------------|-------------------|
| Cursor (Claude) | 200K tokens | ~150K after system prompt |
| Claude Code | 200K tokens | ~150K after CLAUDE.md |
| OpenCode | Model-dependent | Varies by provider |
| GitHub Copilot | 128K tokens | ~100K effective |
| Windsurf | 128K tokens | ~100K effective |

"Effective capacity" accounts for system prompts, rules files, and tool overhead.

## Project Documentation for AI

Write documentation that AI can parse efficiently. AI reads differently than humans — it processes everything literally and benefits from structured, scannable formats.

### Architecture Document

Create a file the AI can reference for system-level decisions:

```markdown
# Architecture Overview

## Data Flow
1. User action triggers API call from React component
2. API route validates input with Zod schema
3. Service layer handles business logic
4. Repository layer interacts with database
5. Response returns through the same chain

## Key Patterns
- All async operations use try/catch with AppError
- User context available via useAuth() hook
- Database transactions for multi-step operations
- Optimistic updates in UI, reconcile on server response

## Module Boundaries
- /modules/auth — authentication and session management
- /modules/billing — Stripe integration, subscription logic
- /modules/projects — core domain logic
- /modules/notifications — email and in-app notifications
```

### Naming This Document

Place architecture docs where AI tools find them automatically:

| Tool | Recommended Location |
|------|---------------------|
| Cursor | Referenced via `@docs/architecture.md` in rules |
| Claude Code | Mentioned in CLAUDE.md or placed in project root |
| OpenCode | Referenced in AGENTS.md |
| Any tool | `/docs/architecture.md` (conventional location) |

## Type-Driven Context

TypeScript interfaces and Zod schemas are the highest-value context for AI code generation. They constrain possibilities and make intent explicit.

```typescript
// This interface gives AI everything it needs to generate
// CRUD operations, form components, and API handlers
interface CreateProjectInput {
  name: string;           // 3-50 characters
  description?: string;   // Max 500 characters
  teamId: string;         // UUID of owning team
  visibility: 'private' | 'team' | 'public';
  deadline?: Date;        // Must be in the future
}

interface Project extends CreateProjectInput {
  id: string;
  createdAt: Date;
  updatedAt: Date;
  owner: User;
  members: TeamMember[];
  taskCount: number;
}
```

Type definitions are dense context: few tokens, high information content. Prioritize including type files over implementation files when context budget is tight.

### Schema as Documentation

Zod schemas serve double duty — runtime validation and AI context:

```typescript
const CreateProjectSchema = z.object({
  name: z.string().min(3).max(50),
  description: z.string().max(500).optional(),
  teamId: z.string().uuid(),
  visibility: z.enum(['private', 'team', 'public']),
  deadline: z.date().refine(d => d > new Date()).optional(),
});
```

When the AI sees this schema, it generates code that respects all constraints without you restating them in the prompt.

## File Referencing Patterns

### Explicit References

Use @ mentions to pull specific files into context:

```
@types/project.ts @lib/db.ts
Create a new API endpoint for listing projects with pagination.
Follow the existing pattern in @app/api/users/route.ts.
```

### Reference Strategy

| When | Reference |
|------|-----------|
| Creating new code | Type definitions + one example of the same pattern |
| Fixing a bug | The broken file + related test file |
| Refactoring | The file(s) being changed + architecture doc |
| Code review | The changed files + relevant type definitions |
| Test generation | Implementation file + existing test file for style |

### What Not to Reference

- Entire directories (context bloat)
- Lock files (package-lock.json, yarn.lock)
- Build output
- Node modules or vendored dependencies
- Files unrelated to the current task

## Anti-Drift Strategies

Context drift is the primary failure mode of long vibe coding sessions. After 20-30 messages, the AI loses track of earlier decisions and produces contradictory code.

### Strategy 1: Fresh Conversations

Start a new conversation for each major feature or concern. One conversation per feature, not one conversation per session.

| Good | Bad |
|------|-----|
| "Auth system" conversation | One conversation for the entire app |
| "Dashboard charts" conversation | Adding charts mid-auth conversation |
| "API error handling" conversation | Mixing error handling with UI work |

### Strategy 2: Periodic Context Restatement

Every 10-15 messages, restate critical constraints:

```
"Reminder: we're using the existing Prisma schema from @prisma/schema.prisma.
All new endpoints follow the pattern in @app/api/users/route.ts.
Auth uses the middleware in @lib/auth.ts.
Now, continue with the notification endpoints."
```

### Strategy 3: Checkpoint Summaries

After completing a significant piece of work, ask the AI to summarize what was built:

```
"Summarize the notification system we just built:
- What files were created/modified
- What patterns were established
- What remains to be done
Save this as a reference for the next session."
```

Use this summary to start the next conversation with full context.

### Strategy 4: Rules File as Drift Anchor

Update rules files with decisions made during a session. If the session established "notifications use Server-Sent Events," add that to the rules file so future sessions know.

## Conversation Hygiene

### Starting a Session

1. Verify rules files are current
2. Reference the architecture document
3. State the specific goal for this session
4. Reference relevant files with @ mentions
5. Begin with a research or planning prompt

### During a Session

| After This Many Messages | Do This |
|--------------------------|---------|
| 5-10 | Check AI is still following established patterns |
| 10-15 | Restate key constraints |
| 15-20 | Consider starting a fresh conversation |
| 20+ | Start fresh — drift is almost certain |

### Ending a Session

1. Ask for a summary of changes made
2. Update rules files with any new conventions
3. Commit working code before ending
4. Note what remains for the next session

## Codebase Readability for AI

Certain codebase qualities make AI more effective:

| Quality | Impact |
|---------|--------|
| Consistent naming | AI learns patterns from examples |
| Typed interfaces | AI generates code that fits the type system |
| Small, focused files | AI can reference one file without pulling in everything |
| Descriptive function names | AI understands intent from names alone |
| Conventional file structure | AI knows where to find and create files |
| Clear module boundaries | AI avoids cross-cutting concerns |

### Codebase Anti-Patterns for AI

| Anti-Pattern | Problem for AI |
|-------------|----------------|
| God files (500+ lines) | AI can't fit the whole file in context |
| Magic strings everywhere | AI can't infer valid values |
| Implicit dependencies | AI misses required imports and setup |
| Inconsistent patterns | AI can't learn "the way we do things" |
| Missing types | AI guesses data shapes, often wrong |
| Environment-dependent behavior | AI can't reproduce or test locally |

Improving codebase readability for AI also improves it for humans. The investment pays dividends beyond vibe coding.

## Context Engineering Checklist

Before starting a vibe coding session on a project:

- Rules files current and concise (under 150 lines each)
- Architecture document exists and is referenced
- Type definitions are comprehensive and up to date
- File structure follows conventions described in rules
- Example patterns exist for the AI to follow
- No contradictions between rules files and actual code
