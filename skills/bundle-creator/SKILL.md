---
name: "@tank/bundle-creator"
description: |
  Author multi-atom Tank bundles that combine instruction, hook, agent, rule,
  tool, resource, and prompt atoms into composite packages. Covers the atoms
  array schema, atom kind selection, handler wiring (JS and DSL), agent
  definition, rule policies, extension bags, permission scoping, and
  bundle directory layout. Synthesizes the Tank Contributing Standard
  (AGENTS.md), the @tank/quality-gate canonical bundle, and Tank registry
  conventions.

  Trigger phrases: "create a bundle", "new bundle", "multi-atom package",
  "tank bundle", "build a bundle", "atoms array", "hook atom", "agent atom",
  "rule atom", "tool atom", "resource atom", "prompt atom", "composite package",
  "bundle tank.json", "write a bundle"
---

# Bundle Creator

Compose multiple atom primitives into a single deployable package that
extends agent behavior beyond what instructions alone can achieve.

## Core Philosophy

1. **Atoms are the unit of composition.** Each atom does one thing: inject
   context, intercept lifecycle events, define a sub-agent, enforce a rule,
   register a tool, expose a resource, or template a prompt. A bundle wires
   atoms together into a cohesive capability.

2. **Start with the lightest atom.** If pure instructions solve the problem,
   use an instruction-only skill. Add atoms only when you need machine
   enforcement (hooks, rules), delegation (agents), or external integration
   (tools, resources). Every atom adds complexity.

3. **Permission budget is real.** Each atom widens the package's attack
   surface. Scope permissions to the minimum each atom actually needs.
   A readonly reviewer agent does not need `write` or `bash`.

4. **Hooks and rules are different tools.** Hooks run arbitrary code at
   lifecycle events. Rules declare static policies the runtime enforces.
   Prefer rules for simple allow/block decisions; use hooks when you need
   conditional logic, delegation, or side effects.

5. **Name the bundle for the capability, not the atoms.** `@tank/quality-gate`
   names the outcome. `@tank/hook-agent-rule-combo` names the plumbing.
   Users install capabilities, not implementation details.

## Quick-Start: Common Problems

### "I need a bundle that reviews code before the agent stops"

1. Create `bundles/{name}/tank.json` with atoms array
2. Add a `hook` atom on `pre-stop` pointing to `./hooks/{name}.ts`
3. Add an `agent` atom for the reviewer with `readonly: true`
4. Add an `instruction` atom referencing `./SKILL.md` for context
5. Write the hook handler that delegates to the agent
   -> See `references/worked-examples.md` (quality-gate walkthrough)

### "I need to enforce a rule without writing code"

1. Add a `rule` atom with `event`, `policy`, and `reason`
2. Pair with an `instruction` atom explaining the rationale
3. No hook handler needed — the runtime enforces declaratively
   -> See `references/bundle-composition.md` (rule patterns)

### "I need to register an MCP tool or expose data"

1. Add a `tool` atom with `name` and connection config
2. Or add a `resource` atom with `uri` for readable data
3. Add an `instruction` atom so the agent knows when to use them
   -> See `references/tank-json-anatomy.md` (tool and resource atoms)

### "I am not sure if I need a bundle or a skill"

1. Check the decision tree below
2. If every atom would be `instruction`, use a skill instead
   -> See `references/bundle-composition.md` (skill vs bundle)

## Decision Trees

### Skill vs Bundle

| Signal                                  | Format           |
| --------------------------------------- | ---------------- |
| Pure instructions/knowledge             | Instruction-only |
| Need lifecycle hooks (pre-stop, etc.)   | Bundle           |
| Need a sub-agent with specific tools    | Bundle           |
| Need machine-enforced rules             | Bundle           |
| Need MCP tool or resource registration  | Bundle           |
| Need prompt templates or slash commands | Bundle           |

### Which Atom Kind

| Need                              | Atom Kind     | Required Fields         |
| --------------------------------- | ------------- | ----------------------- |
| Behavioral context for the agent  | `instruction` | `content` (file path)   |
| Code at lifecycle events          | `hook`        | `event`, `handler`      |
| Delegatable sub-agent             | `agent`       | `name`, `role`          |
| Declarative policy enforcement    | `rule`        | `event`, `policy`       |
| MCP server registration           | `tool`        | `name`                  |
| Readable data/context source      | `resource`    | `uri`                   |
| Reusable invocable template       | `prompt`      | `name`, `template`      |

### Hook Handler Type

| Signal                                    | Handler Type |
| ----------------------------------------- | ------------ |
| Simple block/allow/rewrite on match       | DSL          |
| Conditional logic, delegation, side fx    | JS           |
| Needs access to git diff, file content    | JS           |
| Portable across all runtimes              | DSL          |

### Agent Model Tier

| Workload                            | Model Tier  |
| ----------------------------------- | ----------- |
| Fast classification, triage         | `fast`      |
| Code review, analysis               | `balanced`  |
| Architecture decisions, complex     | `powerful`  |

## Bundle Directory Layout

```
bundles/{kebab-name}/
  tank.json             # Required — metadata + permissions + atoms array
  SKILL.md              # Optional — instruction content (referenced by atom)
  hooks/                # Optional — JS/TS hook handlers
  references/           # Optional — deep docs (250-450 lines each)
  scripts/              # Optional — executable code
  assets/               # Optional — templates, images
```

## Atom Wiring Checklist

1. Every `hook` atom references an existing file in `hooks/`
2. Every `instruction` atom references an existing `.md` file
3. Every `agent` atom has `name`, `role`, and a `tools` array
4. Every `rule` atom has `event`, `policy`, and `reason`
5. Permissions in `tank.json` cover what all atoms need combined
6. `repository` points to `https://github.com/tankpkg/packages`

## Reference Index

| File                              | Contents                                                          |
| --------------------------------- | ----------------------------------------------------------------- |
| `references/tank-json-anatomy.md` | Full tank.json schema: fields, atoms array, each atom kind        |
| `references/bundle-composition.md`| When to compose which atoms, sizing signals, permission scoping   |
| `references/worked-examples.md`   | Three real bundle walkthroughs showing atom interplay             |
