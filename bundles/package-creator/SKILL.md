---
name: "@tank/package-creator"
description: |
  Master routing guide for creating ANY Tank package. Given a user request
  ("I want to create a hook", "I need a tool bundle", "write a new skill"),
  identifies the correct package type and routes to the specialized creator
  skill. Covers all 8 package primitives (instruction, bundle, hook, tool,
  rule, agent, prompt, resource) plus composite patterns. Contains decision
  trees for package type identification, format selection (instruction-only
  vs multi-atom), and a universal pre-publish quality checklist.
  Synthesizes Tank Contributing Standard (AGENTS.md) and the 8 creator
  skills (@tank/skill-creator, @tank/bundle-creator, @tank/hook-creator,
  @tank/tool-creator, @tank/rule-creator, @tank/agent-creator,
  @tank/prompt-creator, @tank/resource-creator).

  Trigger phrases: "create a package", "new tank package", "create a skill",
  "create a bundle", "create a hook", "create a tool", "create a rule",
  "create an agent", "create a prompt", "create a resource", "tank package",
  "what kind of package", "which creator", "package type", "build a package",
  "new package", "start a package", "package decision tree", "pre-publish check"
---

# Tank Package Creator

Route any "I want to create..." request to the correct specialized creator.

## Core Philosophy

1. **Route, do not duplicate.** This skill identifies the right creator and
   hands off. The 8 creator skills contain the deep knowledge. Loading all
   of them wastes context; loading the right one is the job.

2. **Format follows need.** Instruction-only skills are simpler to author,
   review, and maintain. Reach for multi-atom bundles only when the problem
   demands machine enforcement, delegation, or external integration.

3. **Composition over complexity.** Most packages need 1-3 atom kinds. A
   bundle with all 7 atom kinds is almost certainly over-engineered. Start
   with the minimum atoms that solve the problem.

4. **Quality is non-negotiable.** Every package passes the same checklist
   before publishing. No exceptions for "simple" packages.

## What Do You Want to Create?

### "I want to teach the agent domain knowledge"

1. This is an **instruction-only skill** (the simplest package type).
2. Load `@tank/skill-creator` for the full workflow.
3. Create under `skills/{name}/` with `SKILL.md` + `tank.json`.

### "I want to intercept agent behavior at lifecycle events"

1. This requires a **hook atom** inside a multi-atom bundle.
2. Load `@tank/hook-creator` for event catalog and handler patterns.
3. Load `@tank/bundle-creator` for the bundle scaffold.

### "I want to wire an MCP server into the agent"

1. This requires a **tool atom** inside a multi-atom bundle.
2. Load `@tank/tool-creator` for transport wiring and extension bags.
3. Load `@tank/bundle-creator` for the bundle scaffold.

### "I want to enforce a policy without writing code"

1. This requires a **rule atom** inside a multi-atom bundle.
2. Load `@tank/rule-creator` for policy design and event targeting.
3. Load `@tank/bundle-creator` for the bundle scaffold.

### "I want to define a sub-agent with specific tools"

1. This requires an **agent atom** inside a multi-atom bundle.
2. Load `@tank/agent-creator` for role design and tool scoping.
3. Load `@tank/bundle-creator` for the bundle scaffold.

### "I want a reusable template or slash command"

1. This requires a **prompt atom** inside a multi-atom bundle.
2. Load `@tank/prompt-creator` for template design and variable syntax.
3. Load `@tank/bundle-creator` for the bundle scaffold.

### "I want to expose data the agent can read on demand"

1. This requires a **resource atom** inside a multi-atom bundle.
2. Load `@tank/resource-creator` for URI design and pull-model patterns.
3. Load `@tank/bundle-creator` for the bundle scaffold.

### "I want a composite package with multiple atom types"

1. Start with `@tank/bundle-creator` for the scaffold and atoms array.
2. Load the specific creator for each atom kind you need.
3. Refer to `references/decision-guide.md` for common combinations.

## Decision Trees

### Format Selection

| Signal                                   | Format           | Creator              |
| ---------------------------------------- | ---------------- | -------------------- |
| Pure knowledge, no enforcement needed    | Instruction-only | `@tank/skill-creator`  |
| Need lifecycle hooks                     | Multi-atom       | `@tank/bundle-creator` |
| Need a sub-agent with scoped tools       | Multi-atom       | `@tank/bundle-creator` |
| Need declarative policy enforcement      | Multi-atom       | `@tank/bundle-creator` |
| Need MCP tool or resource registration   | Multi-atom       | `@tank/bundle-creator` |
| Need on-demand prompt templates          | Multi-atom       | `@tank/bundle-creator` |

### Atom Kind Selection

| Need                                     | Atom Kind     | Specialized Creator       |
| ---------------------------------------- | ------------- | ------------------------- |
| Behavioral context injected every session| `instruction` | `@tank/skill-creator`     |
| Code at lifecycle events (gate, format)  | `hook`        | `@tank/hook-creator`      |
| Delegatable sub-agent with scoped tools  | `agent`       | `@tank/agent-creator`     |
| Declarative block/warn/allow policy      | `rule`        | `@tank/rule-creator`      |
| MCP server registration                 | `tool`        | `@tank/tool-creator`      |
| On-demand readable data or context       | `resource`    | `@tank/resource-creator`  |
| Reusable invocable template              | `prompt`      | `@tank/prompt-creator`    |

### Common Bundle Patterns

| Pattern                    | Atoms Involved                    | Example                |
| -------------------------- | --------------------------------- | ---------------------- |
| Quality gate               | hook + agent + instruction        | `@tank/quality-gate`   |
| Safety policy              | rule + instruction                | Command blocklist      |
| Tool integration           | tool + instruction                | MCP server wrapper     |
| Automated workflow         | prompt + agent + hook             | PR description bot     |
| Context provider           | resource + instruction            | Project architecture   |
| Full enforcement pipeline  | hook + agent + rule + instruction | Review + block + fix   |

## Pre-Publish Checklist (Quick)

Run through `references/quality-checklist.md` before every `tank publish`.
Summary of critical gates:

1. `name` field matches between `SKILL.md` and `tank.json`
2. `name` starts with `@tank/`
3. SKILL.md body under 200 lines
4. SKILL.md description has 10-15 trigger phrases
5. tank.json permissions are minimal
6. tank.json repository is `https://github.com/tankpkg/packages`
7. Reference files: 250-450 lines, no frontmatter, no overlap
8. Multi-atom: every atom has required fields, files exist

-> See `references/quality-checklist.md` for the full checklist.

## Creator Skills Index

| Creator                  | Scope                                          |
| ------------------------ | ---------------------------------------------- |
| `@tank/skill-creator`    | Instruction-only skills (SKILL.md + references)|
| `@tank/bundle-creator`   | Multi-atom bundle scaffold and atoms array     |
| `@tank/hook-creator`     | Hook atoms, DSL/JS handlers, lifecycle events  |
| `@tank/tool-creator`     | Tool atoms, MCP wiring, extension bags         |
| `@tank/rule-creator`     | Rule atoms, policy design, declarative guards  |
| `@tank/agent-creator`    | Agent atoms, role design, tool scoping         |
| `@tank/prompt-creator`   | Prompt atoms, templates, variable design       |
| `@tank/resource-creator` | Resource atoms, URI design, pull-model context |

## Reference Index

| File                             | Contents                                       |
| -------------------------------- | ---------------------------------------------- |
| `references/decision-guide.md`   | Complete package type identification guide      |
| `references/quality-checklist.md`| Universal pre-publish validation checklist      |
