# Troubleshooting Agent Instruction Files

Sources: Anthropic Claude Code docs, OpenAI Codex documentation, GitHub Copilot docs, ETH Zurich context file study (2026), Claude Code GitHub issues

Covers: diagnosing instruction failures, discovery verification per tool, staleness detection, conflict resolution, size limit handling, session lifecycle issues, and common failure modes with fixes.

## Diagnostic Framework

When an agent ignores instructions, follow this sequence:

1. **Verify discovery** -- Confirm the file is being loaded
2. **Check conflicts** -- Look for contradictory rules
3. **Assess specificity** -- Vague rules get ignored
4. **Measure size** -- Large files cause lost-in-middle
5. **Check session** -- Instructions load at start, not mid-session
6. **Test isolation** -- Reproduce with only the instruction file

## Discovery Verification by Tool

### Codex CLI

```bash
# Verify which files Codex loads
codex --ask-for-approval never "List the instruction sources you loaded."

# Check from specific directory
codex --cd services/payments "Show which instruction files are active."

# Check logs for loaded files
cat ~/.codex/log/codex-tui.log | grep -i "agents\|instruction"
```

Common issues:
- File is empty (Codex skips empty files)
- Combined size exceeds `project_doc_max_bytes` (32 KiB default)
- Override file exists at higher level, blocking your AGENTS.md
- Not in Git root (Codex needs Git root to start walking)

### Claude Code

```
# In a Claude Code session
/memory
```

The `/memory` command lists all CLAUDE.md, CLAUDE.local.md, and rules files loaded. If your file is not listed, Claude cannot see it.

Common issues:
- CLAUDE.md in a subdirectory loads on demand, not at launch
- File excluded via `claudeMdExcludes` setting
- Working directory different from expected
- External `@imports` not approved (first-time dialog)

Use the `InstructionsLoaded` hook to log exactly which files load and when:

```json
{
  "hooks": {
    "InstructionsLoaded": {
      "command": "echo 'Loaded: $CLAUDE_INSTRUCTIONS_FILES' >> /tmp/claude-instructions.log"
    }
  }
}
```

### Cursor

Cursor does not expose a "loaded rules" diagnostic command. Verify by:

1. Check `.cursor/rules/` directory exists with `.mdc` files
2. Verify YAML frontmatter is valid (description, globs, alwaysApply)
3. Confirm `AGENTS.md` exists at project root
4. Test: ask the agent "What coding rules are you following?" and check response

Common issues:
- `.mdc` file missing YAML frontmatter (required for Cursor rules)
- `alwaysApply: false` without matching `globs` -- agent decides relevance from description
- `.cursorrules` file present alongside `.cursor/rules/` (both read, possible conflict)
- Glob pattern too narrow or too broad

### GitHub Copilot

In VS Code, check:
1. `.github/copilot-instructions.md` exists
2. `AGENTS.md` exists at project root
3. Any `.github/instructions/*.instructions.md` files have valid `applyTo` frontmatter
4. Custom instructions enabled in VS Code settings

Common issues:
- Instructions file in wrong directory (`.github/` required for Copilot-specific)
- `applyTo` glob pattern doesn't match target files
- Copilot extension not updated to version that reads AGENTS.md

### OpenCode

```
# Run /init to check what OpenCode discovers
/init
```

Common issues:
- Both AGENTS.md and CLAUDE.md present (AGENTS.md takes precedence)
- Global AGENTS.md at `~/.config/opencode/AGENTS.md` overriding project
- `OPENCODE_DISABLE_CLAUDE_CODE=1` set when CLAUDE.md fallback needed

## Conflict Resolution

### Identifying Conflicts

Conflicts arise when multiple instruction files give contradictory guidance:

```markdown
# Root AGENTS.md
Use Jest for all tests.

# apps/web/AGENTS.md
Use Vitest for all tests.
```

An agent receiving both instructions may pick either one arbitrarily.

### Conflict Detection Procedure

1. List all instruction files in the project:

```bash
find . \( -name "AGENTS.md" -o -name "CLAUDE.md" -o -name "CLAUDE.local.md" \
  -o -name ".cursorrules" -o -name "*.mdc" -o -name "copilot-instructions.md" \
  -o -name "*.instructions.md" -o -name ".windsurfrules" -o -name "GEMINI.md" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*"
```

2. Scan for common conflict patterns:

```bash
# Find testing framework mentions
grep -rn "jest\|vitest\|mocha\|pytest" AGENTS.md CLAUDE.md .cursor/rules/ 2>/dev/null

# Find package manager mentions
grep -rn "npm\|yarn\|pnpm\|bun" AGENTS.md CLAUDE.md .cursor/rules/ 2>/dev/null

# Find formatting/style mentions
grep -rn "tabs\|spaces\|indent\|semicolon" AGENTS.md CLAUDE.md .cursor/rules/ 2>/dev/null
```

3. Compare content across files for drift:

```bash
# Check if CLAUDE.md and AGENTS.md have diverged
diff <(grep -v "^#\|^$\|^@" AGENTS.md) <(grep -v "^#\|^$\|^@" CLAUDE.md)
```

### Resolution Strategies

| Conflict Type | Resolution |
|---------------|------------|
| Root vs subdirectory | Subdirectory wins (intended behavior) |
| AGENTS.md vs CLAUDE.md | Make CLAUDE.md import AGENTS.md |
| .cursorrules vs .cursor/rules/ | Migrate to .cursor/rules/, delete .cursorrules |
| User vs project | Project should win for team standards |
| Stale vs current | Delete the stale file |

## Staleness Detection

Stale instruction files are the most insidious failure mode. The file looks correct but references outdated reality.

### Warning Signs

| Signal | Indicates |
|--------|-----------|
| File references directories that no longer exist | Structural staleness |
| Commands fail when agent runs them | Command staleness |
| Agent uses deprecated patterns despite instructions | Rule staleness |
| Last git change to instruction file > 3 months ago | Review needed |
| Codebase had major refactor but instructions unchanged | Structural staleness |

### Detection Script

```bash
# Find instruction files not modified in 90+ days
find . \( -name "AGENTS.md" -o -name "CLAUDE.md" -o -name "*.mdc" \) \
  -not -path "*/node_modules/*" -mtime +90 -exec echo "STALE: {}" \;

# Verify referenced directories still exist
grep -oP '(?<=`)[^`]*/' AGENTS.md | while read dir; do
  [ -d "$dir" ] || echo "MISSING DIR: $dir referenced in AGENTS.md"
done

# Verify referenced commands still work
grep -oP '`[a-z]+ [^`]+`' AGENTS.md | tr -d '`' | head -5 | while read cmd; do
  echo "Testing: $cmd"
  eval "$cmd" 2>/dev/null || echo "  FAILED"
done
```

### Staleness Prevention

- Review instruction files when merging significant PRs
- Add instruction file review to sprint retrospectives
- Use CODEOWNERS to require review for instruction file changes
- Remove architectural overviews (agents discover structure from filesystem)
- Date-stamp complex sections: `## API Patterns (reviewed 2026-03)`

## Size Limit Handling

### Tool-Specific Limits

| Tool | Limit | What Happens |
|------|-------|--------------|
| Codex CLI | 32 KiB (configurable) | Truncates combined content |
| Claude Code | No hard limit | Adherence degrades with length |
| Cursor | No documented limit | Context window competition |
| Copilot | No documented limit | Context window competition |

### Symptoms of Oversized Files

- Agent follows rules at top of file but ignores rules at bottom
- Inconsistent behavior across sessions (different rules "win")
- Agent takes longer to respond (processing overhead)
- Rules near the end of file are sporadically ignored

### Remediation

1. Count current lines: `wc -l AGENTS.md`
2. If over 200 lines, split into subdirectory files
3. Remove content agents discover independently (README duplicates, obvious conventions)
4. Remove architectural overviews (ETH study showed they increase cost without benefit)
5. Collapse verbose explanations into concise rules
6. For Codex: raise `project_doc_max_bytes` if splitting is not feasible

## Session Lifecycle Issues

### When Instructions Load

| Tool | Loads At | Mid-Session Changes |
|------|----------|---------------------|
| Codex CLI | Session/run start | Not re-read |
| Claude Code | Session start + on-demand for subdirs | File re-read after /compact |
| Cursor | Session start | Requires restart |
| Copilot | Context construction | May refresh per request |

### Common Session Issues

**Instructions added mid-session**: Most tools do not re-read instruction files during a session. Start a new session after modifying instruction files.

**Lost after /compact (Claude Code)**: CLAUDE.md survives compaction (re-read from disk). Conversational instructions do not. If something disappeared after /compact, it was not in CLAUDE.md.

**Long session drift**: In extended sessions, agents may deprioritize instruction file content as conversation grows ("lost in the middle"). Start fresh sessions for new tasks.

## Common Failure Patterns and Fixes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Agent ignores all instructions | File not discovered | Verify file location and tool support |
| Agent follows some rules, ignores others | File too large / conflicts | Shorten file, resolve conflicts |
| Agent follows instructions initially, stops later | Long session drift | Start new session for new tasks |
| Agent uses wrong framework version | Stack not specified | Add explicit version numbers |
| Agent modifies protected files | Boundaries too vague | Use "Never" + specific paths |
| Agent adds wrong dependencies | Package manager not specified | State exact package manager |
| Agent writes wrong test framework | Multiple testing mentions | Remove ambiguity, one clear directive |
| Instructions work in Tool A not Tool B | Format incompatibility | Check tool's native format |
| Override file blocks intended rules | AGENTS.override.md exists | Remove or update override |
| Subdirectory rules not loading | Tool loads on demand | Edit a file in that directory first |

## Emergency Fixes

### Agent Running Wrong Commands

Add boundary as first line of AGENTS.md:

```markdown
CRITICAL: Use pnpm, never npm. Use Vitest, never Jest.
```

Place critical corrections at the top of the file where they are least likely to be lost in context.

### Agent Modifying Protected Files

Add explicit Never section:

```markdown
## Never
- Never modify files in /db/migrations/
- Never modify files in /vendor/
- Never modify .env or .env.* files
- Never modify package-lock.json directly
```

### Complete Instruction Reset

If instruction files have become unmaintainable:

1. Archive current files: `mkdir .instruction-backup && cp AGENTS.md CLAUDE.md .instruction-backup/`
2. Start fresh with minimal AGENTS.md (stack + commands + boundaries only)
3. Add rules incrementally as agent makes specific mistakes
4. Each addition should respond to an observed failure, not speculative prevention
