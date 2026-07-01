# Claude Code Memory System Deep Dive

Sources: Anthropic Claude Code documentation (code.claude.com, 2026), Anthropic context engineering guide, Claude Code GitHub issues

Covers: CLAUDE.md file hierarchy, .claude/rules/ with path globs, auto memory mechanics, managed policy deployment, @import syntax, claudeMdExcludes, /init and /memory commands, and troubleshooting.

## CLAUDE.md vs Auto Memory

Claude Code has two complementary memory systems:

| Dimension | CLAUDE.md Files | Auto Memory |
|-----------|----------------|-------------|
| Who writes it | Developer | Claude |
| What it contains | Instructions and rules | Learnings and patterns |
| Scope | Project, user, or org | Per working tree |
| Loaded into | Every session | Every session (first 200 lines or 25 KB) |
| Use for | Coding standards, workflows, architecture | Build commands, debugging insights, preferences |
| Survives compaction | Yes (re-read from disk) | Yes (re-read from disk) |

Use CLAUDE.md for deliberate guidance. Auto memory captures things Claude learns from corrections without manual effort.

## CLAUDE.md File Hierarchy

### Location Matrix

| Scope | Location | Purpose | Shared With |
|-------|----------|---------|-------------|
| Managed policy | `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS) | Org-wide IT standards | All users (cannot be excluded) |
| Managed policy | `/etc/claude-code/CLAUDE.md` (Linux/WSL) | Same | All users |
| Managed policy | `C:\Program Files\ClaudeCode\CLAUDE.md` (Windows) | Same | All users |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team standards | Team via git |
| User | `~/.claude/CLAUDE.md` | Personal cross-project | Just you |
| Local | `./CLAUDE.local.md` | Personal project prefs | Just you (gitignored) |

### Loading Order

1. Managed policy CLAUDE.md (always first, cannot be excluded)
2. Walk UP from CWD to project root, loading CLAUDE.md + CLAUDE.local.md per level
3. User-level `~/.claude/CLAUDE.md`
4. All files concatenated (not overridden)
5. CLAUDE.local.md appended after CLAUDE.md at each level (last-read wins for conflicts)
6. Subdirectory CLAUDE.md files load on demand when Claude reads files in those dirs

### Size Recommendations

Target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence. Claude Code loads CLAUDE.md in full regardless of length, but shorter files produce better compliance.

## @Import Syntax

CLAUDE.md files can import additional files using `@path/to/file` syntax:

```markdown
# CLAUDE.md

See @README.md for project overview.
See @package.json for available scripts.

## Development
Follow the workflow in @docs/git-instructions.md.

## Cross-tool Instructions
@AGENTS.md
```

### Import Rules

| Rule | Detail |
|------|--------|
| Path resolution | Relative to the file containing the import |
| Absolute paths | Allowed |
| Recursive imports | Supported, max depth 5 hops |
| First-time approval | External imports show approval dialog |
| When loaded | At launch, alongside the importing file |
| Home directory | `@~/.claude/my-project-instructions.md` works |

### AGENTS.md Integration

Claude Code does not natively auto-load AGENTS.md. Create this bridge:

```markdown
# CLAUDE.md

@AGENTS.md

## Claude Code Specific
Use plan mode for changes under src/billing/.
Prefer Read tool over grep for files under 500 lines.
```

Claude loads AGENTS.md content first, then appends the Claude-specific instructions below.

## .claude/rules/ Directory

For larger projects, organize instructions into modular rule files:

```
project/
  .claude/
    CLAUDE.md              # Main project instructions
    rules/
      code-style.md        # Code style guidelines
      testing.md            # Testing conventions
      security.md           # Security requirements
      frontend/
        components.md       # Component patterns
      backend/
        api-design.md       # API conventions
```

### Basic Rules (Always Loaded)

Files without `paths` frontmatter load at launch with the same priority as `.claude/CLAUDE.md`:

```markdown
# security.md

Never commit secrets, API keys, or .env files.
All user input must be validated before use.
Database queries must use parameterized statements.
```

### Path-Specific Rules (Loaded on Match)

Use YAML frontmatter with `paths` field to scope rules:

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API Development Rules

All API endpoints must include input validation.
Use the standard error response format from src/api/errors.ts.
Include OpenAPI documentation comments.
```

### Glob Pattern Reference

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All TypeScript files in any directory |
| `src/**/*` | All files under src/ |
| `*.md` | Markdown files in project root |
| `src/components/*.tsx` | React components in specific directory |
| `src/**/*.{ts,tsx}` | TypeScript and TSX files under src/ |
| `tests/**/*.test.ts` | Test files under tests/ |

Multiple patterns in a single rule:

```yaml
---
paths:
  - "src/**/*.{ts,tsx}"
  - "lib/**/*.ts"
  - "tests/**/*.test.ts"
---
```

### Rules vs Skills

| Dimension | Rules (.claude/rules/) | Skills (.claude/skills/) |
|-----------|------------------------|--------------------------|
| When loaded | Every session or path match | On invocation or agent decision |
| Purpose | Persistent constraints | Task-specific workflows |
| Token cost | Always in context | Only when needed |
| Best for | Standards, conventions | Repeatable procedures |

Use rules for always-on guidance. Use skills for task-specific workflows that load on demand.

## Auto Memory

### How It Works

Auto memory lets Claude save notes for itself across sessions: build commands, debugging insights, architecture notes, preferences. Claude decides what to save based on whether the information would be useful in a future conversation.

### Storage

```
~/.claude/projects/<project>/memory/
  MEMORY.md              # Index, loaded every session (first 200 lines / 25 KB)
  debugging.md           # Detailed debugging patterns
  api-conventions.md     # API design decisions
  ...                    # Any topic files Claude creates
```

All worktrees and subdirectories within the same git repository share one auto memory directory.

### Loading Behavior

- `MEMORY.md` first 200 lines (or 25 KB) loaded at session start
- Content beyond the threshold is not loaded
- Topic files (debugging.md, patterns.md) load on demand via file tools
- Claude keeps MEMORY.md concise by moving details into topic files

### Configuration

```json
{
  "autoMemoryEnabled": false
}
```

Or set `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.

Custom location:

```json
{
  "autoMemoryDirectory": "~/my-custom-memory-dir"
}
```

### Audit and Edit

Run `/memory` to browse all loaded instruction files and auto memory. Select any file to open in editor. Everything is plain Markdown -- edit or delete freely.

## Managed Policy for Organizations

Organizations can deploy centrally managed CLAUDE.md files that apply to all users:

### Deployment

Place the file at the managed policy location for the OS. Deploy via MDM, Group Policy, Ansible, or similar tools.

### Managed Policy vs Managed Settings

| Concern | Use |
|---------|-----|
| Block specific tools, commands, paths | Managed settings: `permissions.deny` |
| Enforce sandbox isolation | Managed settings: `sandbox.enabled` |
| Code style and quality guidelines | Managed CLAUDE.md |
| Data handling and compliance | Managed CLAUDE.md |
| Behavioral instructions | Managed CLAUDE.md |

Settings are enforced by the client. CLAUDE.md instructions shape behavior but are not hard enforcement.

## claudeMdExcludes

Skip irrelevant CLAUDE.md files in large monorepos:

```json
{
  "claudeMdExcludes": [
    "**/monorepo/CLAUDE.md",
    "/home/user/monorepo/other-team/.claude/rules/**"
  ]
}
```

- Patterns matched against absolute file paths using glob syntax
- Configurable at user, project, local, or managed policy layer
- Arrays merge across layers
- Managed policy CLAUDE.md files CANNOT be excluded

## /init Command

Generate a starting CLAUDE.md from codebase analysis:

```bash
claude /init
```

Claude analyzes the codebase and creates a file with build commands, test instructions, and project conventions it discovers. If a CLAUDE.md already exists, `/init` suggests improvements rather than overwriting.

### Interactive Mode

Set `CLAUDE_CODE_NEW_INIT=1` for multi-phase flow:

1. Asks which artifacts to set up (CLAUDE.md, skills, hooks)
2. Explores codebase with a subagent
3. Asks follow-up questions to fill gaps
4. Presents reviewable proposal before writing

Always review and edit the generated file. Remove content agents can discover independently. Add non-inferable details the generator missed.

## Sharing Rules Across Projects

### Symlinks in .claude/rules/

```bash
ln -s ~/shared-claude-rules .claude/rules/shared
ln -s ~/company-standards/security.md .claude/rules/security.md
```

Symlinks resolve normally. Circular symlinks detected gracefully.

### User-Level Rules

```
~/.claude/rules/
  preferences.md         # Personal coding preferences
  workflows.md           # Preferred workflows
```

User-level rules load before project rules. Project rules have higher priority.

### Git Worktrees

CLAUDE.local.md exists only in the worktree where created. For shared personal instructions across worktrees, import from home directory:

```markdown
# CLAUDE.local.md
@~/.claude/my-project-instructions.md
```

## HTML Comments

Block-level HTML comments are stripped before injection:

```markdown
<!-- This note is for human maintainers only.
     Claude never sees this text. -->

## Rules Claude Does See
Use TypeScript strict mode.
```

Use comments for maintainer notes without spending context tokens. Comments inside code blocks are preserved. When reading CLAUDE.md with the Read tool directly, comments remain visible.

## Troubleshooting

### Claude Ignores Instructions

1. Run `/memory` to verify files are loaded
2. Check file is in a location that gets loaded for the session
3. Make instructions more specific ("Use 2-space indentation" not "format nicely")
4. Look for conflicts across CLAUDE.md files
5. Use `--append-system-prompt` for system-prompt-level instructions (scripts only)
6. Use `InstructionsLoaded` hook to log exactly which files load

### Instructions Lost After /compact

CLAUDE.md fully survives compaction -- re-read from disk. If instructions disappeared, they were given in conversation only, not in CLAUDE.md. Add persistent instructions to the file.

### CLAUDE.md Too Large

- Move details into `.claude/rules/` files
- Use `@path` imports for referenced content
- Remove content agents discover independently
- Split into path-scoped rules to reduce per-session token load

### Auto Memory Unexpected Behavior

Run `/memory` to browse saved notes. Delete or edit any memory file -- all plain Markdown. Set `autoMemoryEnabled: false` in project settings to disable.
