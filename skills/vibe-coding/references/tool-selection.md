# Tool Selection

Sources: vibecoding.app (Best Vibe Coding Tools, 2026), promptt.dev (Claude Code vs Cursor, 2026), appwrite.io (Comparing Vibe Coding Tools, 2026), daily.dev (Vibe Coding 2026), Anthropic Claude Code documentation, Cursor documentation

Covers: AI coding tool comparison, selection criteria by project stage and team size, workflow patterns per tool, pricing considerations, and migration between tools.

## Tool Landscape (2026)

The AI coding tool market has segmented into distinct categories. Choose based on workflow preference, not hype.

### Category Map

| Category | Tools | Best For |
|----------|-------|----------|
| IDE-integrated | Cursor, Windsurf, Continue | Full-time development with AI assistance |
| Terminal-first | Claude Code, OpenCode, Aider | Agentic workflows, CLI-native developers |
| Inline assistant | GitHub Copilot, Codeium | Autocomplete and light assistance |
| Browser generators | Bolt.new, Lovable, v0, Replit Agent | Rapid prototyping, no local setup |
| Specialized | Devin, Codex CLI | Autonomous task execution |

## Tool Profiles

### Cursor

**Category:** IDE (VS Code fork with native AI)
**Rules file:** `.cursor/rules/*.mdc`
**Pricing:** Free tier + Pro $20/month + Business $40/month

**Strengths:**
- Familiar VS Code environment with full extension support
- Agent Mode for multi-file autonomous changes
- Composer for multi-file generation with conversation
- Tab completion that understands codebase context
- `.cursor/rules/` directory with glob-based auto-apply

**Weaknesses:**
- Proprietary — lock-in to Cursor-specific rules format
- Heavy IDE for simple tasks
- Subscription cost adds up for teams

**Best workflow:**
1. Set up `.cursor/rules/` with project conventions
2. Use Composer for new features (multi-file generation)
3. Use Agent Mode for refactoring and migration tasks
4. Use Tab for inline completions during manual coding
5. Use Cmd+K for single-file inline edits

**When to choose:** Full-stack development, team environments, VS Code users who want deep AI integration.

### Claude Code

**Category:** Terminal-first agent
**Rules file:** `CLAUDE.md`
**Pricing:** Usage-based (via Anthropic API) or Claude subscription

**Strengths:**
- Terminal-native — reads/writes files, runs commands, executes tests
- Reads `CLAUDE.md` from project root and subdirectories
- Deep codebase understanding (scans project structure)
- Extended thinking for complex reasoning tasks
- Git-aware — understands branches, commits, diffs

**Weaknesses:**
- No GUI — terminal only
- Usage-based pricing can be unpredictable
- Requires comfort with CLI workflows

**Best workflow:**
1. Write `CLAUDE.md` with project conventions
2. Start Claude Code in the project root
3. Describe the goal — let the agent plan and execute
4. Review generated files and test results
5. Iterate on specific files or behaviors

**When to choose:** Terminal-native developers, agentic workflows where the AI drives execution, complex multi-file changes, CLI tool development.

### OpenCode

**Category:** Terminal-first agent (open-source)
**Rules file:** `AGENTS.md` or custom instructions
**Pricing:** Free (bring your own API key)

**Strengths:**
- Open-source and self-hostable
- Multi-provider support (Anthropic, OpenAI, Google, local models)
- Skill system for domain-specific knowledge injection
- MCP server integration for tool connectivity
- Agent delegation for parallel task execution

**Weaknesses:**
- Newer ecosystem — fewer community resources
- Requires API key management
- Configuration more complex than turnkey solutions

**Best workflow:**
1. Configure `opencode.json` with provider and model
2. Write `AGENTS.md` for project conventions
3. Install relevant skills for domain-specific assistance
4. Use agent delegation for parallel subtask execution
5. MCP servers for database, API, and tool integration

**When to choose:** Open-source preference, multi-model flexibility, skill-augmented workflows, self-hosted requirements.

### GitHub Copilot

**Category:** Inline assistant (IDE extension)
**Rules file:** `.github/copilot-instructions.md`
**Pricing:** Free tier + Individual $10/month + Business $19/month

**Strengths:**
- Integrated into VS Code, JetBrains, Neovim
- Copilot Chat for conversational coding
- Copilot Workspace for issue-to-PR automation
- Lowest friction for existing GitHub workflows
- Agent mode (2026) for multi-file changes

**Weaknesses:**
- Less powerful agentic capabilities than Cursor or Claude Code
- Inline suggestions sometimes interrupt flow
- Chat less contextually aware than Cursor Composer

**Best workflow:**
1. Set up `.github/copilot-instructions.md`
2. Use inline suggestions for boilerplate and completions
3. Use Copilot Chat for explanations and small changes
4. Use Copilot Workspace for issue-driven development

**When to choose:** Teams already on GitHub, cost-sensitive, want AI assistance without switching editors.

### Windsurf

**Category:** IDE (VS Code fork)
**Rules file:** `.windsurfrules`
**Pricing:** Free tier + Pro plans

**Strengths:**
- Cascade agent pulls context autonomously from large codebases
- Strong at understanding project structure without explicit references
- Write Mode for autonomous multi-file generation

**Weaknesses:**
- Smaller community than Cursor
- Fewer integrations and plugins

**When to choose:** Large codebases where autonomous context discovery matters more than manual @ references.

### Aider

**Category:** Terminal agent (open-source)
**Rules file:** `.aider.conf.yml` + conventions file
**Pricing:** Free (bring your own API key)

**Strengths:**
- Open-source, works with any LLM provider
- Git-native — auto-commits changes with meaningful messages
- Map of entire codebase for context
- Works with local models (Ollama, LM Studio)

**Weaknesses:**
- Steeper learning curve
- Less polished UX than commercial tools
- No IDE integration (terminal only)

**When to choose:** Open-source preference, local/self-hosted models, git-centric workflow, privacy requirements.

### Browser Generators (Bolt.new, Lovable, v0)

**Category:** Browser-based generation
**Pricing:** Free tiers + paid plans

**Strengths:**
- Zero local setup — start building immediately
- Visual preview of generated output
- Good for designers and non-developers
- Quick prototyping and validation

**Weaknesses:**
- Limited customization after generation
- Harder to maintain long-term
- Export to local development needed for production
- Less control over architecture and code quality

**When to choose:** Rapid prototyping, user validation before building, non-developers building MVPs, hackathons.

## Selection Decision Tree

```
What stage is the project?
|
+-- Prototype / validation
|   |-- No coding experience -> Lovable or Bolt.new
|   +-- Developer -> Any tool (speed matters most)
|
+-- Active development
|   |-- Solo developer
|   |   |-- Prefer IDE -> Cursor
|   |   |-- Prefer terminal -> Claude Code or OpenCode
|   |   +-- Prefer open-source -> Aider or OpenCode
|   |
|   +-- Team
|       |-- GitHub-centric -> Copilot + AGENTS.md
|       |-- Need deep AI integration -> Cursor Business
|       +-- Open-source + multi-model -> OpenCode
|
+-- Maintenance / legacy
    |-- Large codebase -> Windsurf (context discovery) or Cursor
    +-- Bug fixes / small changes -> Any tool with codebase access
```

## Tool Combination Patterns

Most productive developers use multiple tools:

| Combination | Use Case |
|-------------|----------|
| Cursor + Claude Code | Cursor for IDE work, Claude Code for complex refactoring |
| Copilot + Cursor | Copilot for inline, Cursor Composer for features |
| Bolt.new + Cursor | Bolt for prototype, export to Cursor for production |
| OpenCode + Copilot | OpenCode for agentic tasks, Copilot for inline assist |

### Cross-Tool Rules Synchronization

When using multiple tools, maintain a canonical rules source:

1. Write the canonical rules in `AGENTS.md` (cross-tool standard)
2. Adapt to tool-specific formats as needed
3. Automate synchronization with a script or pre-commit hook

For rules file details, see `references/rules-files.md`.

## Migration Between Tools

### Cursor to Claude Code

1. Convert `.cursor/rules/*.mdc` content to `CLAUDE.md` format
2. Remove YAML frontmatter — CLAUDE.md is plain markdown
3. Consolidate multiple rule files into one (or use subdirectory CLAUDE.md files)
4. Adjust workflow from IDE-centric to terminal-centric

### Any Tool to AGENTS.md

1. Extract conventions from tool-specific rules files
2. Write as plain markdown in `AGENTS.md`
3. Keep tool-specific files as symlinks or generated from AGENTS.md
4. Most tools now read AGENTS.md directly or can be configured to

## Cost Comparison (2026)

| Tool | Solo Developer | Small Team (5) |
|------|---------------|----------------|
| Cursor Pro | $20/month | $200/month (Business) |
| Claude Code (moderate use) | ~$30-50/month API | ~$150-250/month API |
| GitHub Copilot | $10/month | $95/month (Business) |
| OpenCode | API costs only | API costs only |
| Aider | API costs only | API costs only |
| Windsurf Pro | $15/month | $75/month |

API-cost tools (Claude Code, OpenCode, Aider) scale with usage. Heavy use during feature sprints can spike costs. Budget $50-100/month per developer for moderate usage.
