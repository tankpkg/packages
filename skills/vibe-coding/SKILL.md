---
name: "@tank/vibe-coding"
description: |
  Vibe coding methodology for AI-assisted software development. Covers the
  full spectrum from Karpathy's original concept through production-grade
  agentic engineering. Rules file authoring (AGENTS.md, CLAUDE.md,
  .cursor/rules/, .windsurfrules), prompt engineering for code generation,
  context engineering and window management, the Research-Plan-Implement
  framework, tool selection (Cursor, Claude Code, OpenCode, Windsurf, Copilot,
  Aider), quality guardrails and tech debt prevention, architecture-first
  patterns, testing strategies for AI-generated code, refactoring vibe-coded
  prototypes into production systems, and failure mode detection and recovery.

  Synthesizes Karpathy (Feb 2025 X post, Feb 2026 agentic engineering),
  Waseem et al. (Vibe Coding in Practice, arXiv 2512.11922), vibecoding.app
  practitioner guides, Anthropic Claude Code documentation, Cursor
  documentation, and 2024-2026 community patterns.

  Trigger phrases: "vibe coding", "vibe code", "vibe coding rules",
  "vibe coding best practices", "vibe coding setup", "vibe coding cursor",
  "vibe coding claude", "AI rapid prototyping", "vibe coding tips",
  "vibe coding workflow", "rules file", "cursorrules", "CLAUDE.md",
  "AGENTS.md", "context engineering", "agentic coding", "AI code generation",
  "vibe coding mistakes", "vibe coding framework", "prompt engineering code",
  "AI pair programming", "vibe coding production", "vibe to production"
---

# Vibe Coding

## Core Philosophy

1. **Architecture before generation** — Define data models, component boundaries, and API contracts before prompting. AI generates code fast; wrong architecture generated fast is worse than no code at all.
2. **Rules files are your codebase's memory** — LLMs forget between sessions. Persistent rules files (AGENTS.md, CLAUDE.md, .cursor/rules/) encode conventions, stack decisions, and patterns so the AI starts every session aligned.
3. **Iterate in small bites** — One feature per prompt. Monolithic prompts produce monolithic, uncontrollable output. Break work into scaffold, connect, style, test.
4. **Review AI output like a junior dev's PR** — AI handles happy paths well. It misses edge cases, security gaps, and architectural drift. Every generation gets human review before merge.
5. **Know when to stop vibing** — Vibe coding excels at prototypes, CRUD, UI scaffolding, and boilerplate. Switch to manual engineering for security-critical code, performance-sensitive paths, and complex state machines.

## Quick-Start: Common Problems

### "How do I set up vibe coding for my project?"

1. Choose your AI tool based on project stage and team size
2. Create a rules file describing stack, conventions, file structure
3. Write an architecture document the AI can reference
4. Start with a small, well-defined feature to establish the pattern
-> See `references/tool-selection.md` and `references/rules-files.md`

### "My AI keeps generating inconsistent code"

1. Check rules files — are conventions explicitly stated?
2. Verify context window — long conversations cause drift
3. Start fresh conversations for new features
4. Reference existing code as style examples with @ mentions
-> See `references/context-engineering.md`

### "I vibe-coded a prototype and now it's a mess"

1. Run the codebase through static analysis and type checking
2. Identify the 3-5 architectural decisions that need correcting
3. Refactor in layers: data model first, then API, then UI
4. Add tests before each refactoring step
-> See `references/prototype-to-production.md`

### "How do I write prompts that produce good code?"

1. Be specific: name files, describe data shapes, state expected behavior
2. Use the Research-Plan-Implement framework for complex features
3. Provide reference code for style matching
4. Break large features into 3-5 sequential prompts
-> See `references/prompt-patterns.md`

### "AI-generated code has security issues"

1. Never trust AI with auth, encryption, or access control without review
2. Add security-focused rules to your rules file
3. Run SAST tools (Semgrep, ESLint security) on every generation
4. Treat AI output as untrusted input — validate before shipping
-> See `references/quality-guardrails.md`

## Decision Trees

### When to Vibe vs When to Engineer

| Signal | Approach |
|--------|----------|
| Prototype / MVP / hackathon | Vibe code freely |
| CRUD endpoints, forms, boilerplate | Vibe code with review |
| UI scaffolding and styling | Vibe code with design reference |
| Test generation | Vibe code then verify coverage |
| Auth, payments, encryption | Manual engineering with AI assist |
| Performance-critical hot paths | Manual engineering |
| Complex state machines | Manual engineering with AI planning |
| Regulatory / compliance code | Manual engineering, AI review only |

### Tool Selection

| Situation | Tool |
|-----------|------|
| Full-stack with IDE integration | Cursor (Agent Mode) |
| Terminal-first, agentic workflow | Claude Code or OpenCode |
| Existing VS Code workflow + Copilot | GitHub Copilot |
| Open-source, self-hosted models | Aider or Continue |
| Quick prototypes, no local setup | Bolt.new, Lovable, v0 |
| Team standardization needed | AGENTS.md + any tool |

### Rules File Format

| Tool | File | Format |
|------|------|--------|
| Cursor | `.cursor/rules/*.mdc` | Markdown + YAML frontmatter |
| Claude Code | `CLAUDE.md` | Plain markdown |
| OpenCode | `AGENTS.md` or instructions | Plain markdown |
| Windsurf | `.windsurfrules` | Plain markdown |
| GitHub Copilot | `.github/copilot-instructions.md` | Plain markdown |
| Cross-tool standard | `AGENTS.md` | Plain markdown (Linux Foundation) |

## Reference Index

| File | Contents |
|------|----------|
| `references/rules-files.md` | Rules file authoring for every tool, structure patterns, what to include/exclude, cross-tool AGENTS.md standard |
| `references/prompt-patterns.md` | Prompt engineering for code generation, Research-Plan-Implement framework, iterative prompting, role assignment, context referencing |
| `references/context-engineering.md` | Context window management, anti-drift strategies, project documentation for AI, type-driven context, conversation hygiene |
| `references/tool-selection.md` | AI coding tool comparison (Cursor, Claude Code, OpenCode, Windsurf, Copilot, Aider, Bolt.new), selection criteria, workflow patterns per tool |
| `references/quality-guardrails.md` | Code review for AI output, security scanning, testing strategies, static analysis, tech debt prevention, the junior-dev-PR mental model |
| `references/prototype-to-production.md` | Refactoring vibe-coded prototypes, architecture recovery, incremental hardening, test-first refactoring, data model correction |
| `references/failure-modes.md` | Anti-patterns and failure modes, architecture drift detection, context window exhaustion, over-reliance signals, recovery procedures |
