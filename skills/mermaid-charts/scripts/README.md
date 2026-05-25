# Mermaid Validator

Local validator for Mermaid diagrams. Runs the **official** `mermaid.parse()`
grammar via Node + jsdom — no Puppeteer, no Chromium, no network.

## Setup

```bash
cd scripts/
npm install
```

This installs `mermaid` (^11.0.0) and `jsdom` (^25.0.0).

## Usage

```bash
# Walk a directory, lint every mermaid block in every .md / .mdx file:
node validate-mermaid.mjs path/to/docs/

# Lint a single file:
node validate-mermaid.mjs path/to/diagram.md

# Lint a raw .mmd / .mermaid file:
node validate-mermaid.mjs path/to/chart.mmd

# Lint piped text:
echo 'flowchart TD\n  A --> B' | node validate-mermaid.mjs --stdin
node validate-mermaid.mjs --stdin < diagram.mmd
```

## Exit codes

| Code | Meaning                                |
| ---- | -------------------------------------- |
| 0    | All diagrams valid                     |
| 1    | At least one parse error               |
| 2    | Validator crashed (bad args, missing deps) |

## Output format

```
path/to/file.md:42: mermaid parse error
  Parse error on line 3:
  ...flowchart TQ;A--x|text including
  -----------------------^
  Expecting 'NEWLINE', ...
```

The line number is offset to the **source file**, so editors can jump to it.

## Why this approach

| Tool                              | Verdict                                                |
| --------------------------------- | ------------------------------------------------------ |
| `@mermaid-js/mermaid-cli` (mmdc)  | Pulls Puppeteer + Chromium (~300MB). Too heavy.        |
| `@probelabs/maid`                 | Different parser. False positives + missed real errors.|
| `go-mermaid`                      | Custom parser; drifts from official grammar.           |
| `@mermaid-js/parser` (Langium)    | Official but incomplete coverage (subset of diagrams). |
| **`mermaid.parse()` + jsdom**     | **Same grammar as renderers. Complete. ~2s. Picked.**  |

If a diagram passes this validator, it renders on GitHub, GitLab, Notion,
Obsidian, VS Code preview, and mermaid.live.

## CI integration

```yaml
# .github/workflows/mermaid.yml
- run: cd scripts && npm install
- run: node scripts/validate-mermaid.mjs docs/ README.md
```

Pre-commit (Husky / lefthook):

```bash
node scripts/validate-mermaid.mjs $(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(md|mdx|mmd)$')
```
