# Tank Skill Catalog

Complete mapping from detected project signals to published Tank skills.

## Published @tank Skills (as of Feb 2026)

| Skill | Version | Score | Domain |
|-------|---------|-------|--------|
| `@tank/clean-code` | 3.0.0 | 10 | Code quality (SOLID, KISS, refactoring) |
| `@tank/react` | 2.0.0 | 10 | React patterns, hooks, state, performance |
| `@tank/python` | 2.0.0 | 10 | Modern Python 3.10+, type hints, async |
| `@tank/node-express` | 2.0.0 | 10 | Node.js/Express API servers |
| `@tank/tdd-workflow` | 2.0.0 | 10 | Test-driven development cycle |
| `@tank/planning` | 2.0.0 | 10 | Planning methodology for complex tasks |
| `@tank/bdd-e2e-testing` | 1.0.0 | 10 | BDD with Playwright, Cucumber, Gherkin |
| `@tank/relational-db-mastery` | 1.0.0 | 10 | PostgreSQL/MySQL optimization |
| `@tank/frontend-craft` | 0.0.1 | 10 | Frontend polish, micro-interactions |
| `@tank/figma-to-code` | 1.1.0 | 10 | Pixel-perfect Figma implementation |
| `@tank/figma-plugin` | 1.1.0 | 8 | Figma plugin development |
| `@tank/github-docs` | 0.0.1 | 8 | GitHub README/docs best practices |
| `@tank/skill-creator` | 1.1.0 | 8 | Creating new Tank skills |
| `@tank/tank-package-publisher` | 1.1.0 | 10 | Publishing skills to Tank |
| `@tank/google-docs` | 1.1.0 | 10 | Google Docs API |
| `@tank/google-sheets` | 1.1.0 | 10 | Google Sheets API |
| `@tank/google-calendar` | 1.1.0 | 10 | Google Calendar API |
| `@tank/gmail` | 1.1.0 | 10 | Gmail API |
| `@tank/notion` | 1.1.0 | 10 | Notion API |
| `@tank/slack` | 1.1.0 | 10 | Slack API |

## Notable Third-Party Skills

| Skill | Domain |
|-------|--------|
| `@solaraai/seo-ai-mastery` | SEO strategy |
| `@solaraai/modern-frontend-ui` | Frontend UI patterns |
| `@solaraai/e2e-test-creator` | E2E test writing |
| `@solaraai/eslint-rule-creator` | Custom ESLint rules |
| `@solaraai/oss-product-partner` | OSS product decisions |

## Stack-to-Skill Mapping

### Language Detection

| Detected Language | Skills | Version Range |
|------------------|--------|---------------|
| TypeScript | `@tank/clean-code` | `^3.0.0` |
| Python | `@tank/python`, `@tank/clean-code` | `^2.0.0`, `^3.0.0` |
| JavaScript (Node) | `@tank/node-express`, `@tank/clean-code` | `^2.0.0`, `^3.0.0` |

### Framework Detection

| Detected Framework | Skills | Version Range |
|-------------------|--------|---------------|
| React | `@tank/react`, `@tank/frontend-craft` | `^2.0.0`, `*` |
| Next.js | `@tank/react`, `@tank/frontend-craft` | `^2.0.0`, `*` |
| Angular | `@tank/frontend-craft` | `*` |
| Vue.js | `@tank/frontend-craft` | `*` |
| Express | `@tank/node-express` | `^2.0.0` |
| FastAPI / Django / Flask | `@tank/python` | `^2.0.0` |
| Figma Plugin | `@tank/figma-plugin` | `^1.0.0` |

### Tooling Detection

| Detected Tool | Skills | Version Range |
|--------------|--------|---------------|
| Tailwind CSS | `@tank/frontend-craft` | `*` |
| Playwright | `@tank/bdd-e2e-testing`, `@tank/tdd-workflow` | `^1.0.0`, `^2.0.0` |
| Cypress | `@tank/bdd-e2e-testing`, `@tank/tdd-workflow` | `^1.0.0`, `^2.0.0` |
| Jest / Vitest | `@tank/tdd-workflow` | `^2.0.0` |
| Prisma / Drizzle / SQLAlchemy | `@tank/relational-db-mastery` | `^1.0.0` |
| ESLint | `@tank/clean-code` | `^3.0.0` |

### Infrastructure Detection

| Detected Infra | Skills | Version Range |
|---------------|--------|---------------|
| GitHub (.github/) | `@tank/github-docs` | `*` |
| Google Workspace | `@tank/gmail`, `@tank/google-docs`, etc. | `^1.0.0` |
| Slack integration | `@tank/slack` | `^1.0.0` |
| Notion integration | `@tank/notion` | `^1.0.0` |

### Universal Recommendations

These skills are recommended for ALL projects unless user opts out:

| Skill | Reason |
|-------|--------|
| `@tank/clean-code` | Universal code quality improvement |
| `@tank/planning` | Helps with complex task decomposition |

## Skill Combination Patterns

Common stacks and their complete skill sets:

### Full-Stack React + Node.js

```json
{
  "skills": {
    "@tank/clean-code": "^3.0.0",
    "@tank/react": "^2.0.0",
    "@tank/node-express": "^2.0.0",
    "@tank/frontend-craft": "*",
    "@tank/tdd-workflow": "^2.0.0",
    "@tank/relational-db-mastery": "^1.0.0",
    "@tank/github-docs": "*"
  }
}
```

### Next.js App

```json
{
  "skills": {
    "@tank/clean-code": "^3.0.0",
    "@tank/react": "^2.0.0",
    "@tank/frontend-craft": "*",
    "@tank/tdd-workflow": "^2.0.0",
    "@tank/github-docs": "*"
  }
}
```

### Python API

```json
{
  "skills": {
    "@tank/clean-code": "^3.0.0",
    "@tank/python": "^2.0.0",
    "@tank/relational-db-mastery": "^1.0.0",
    "@tank/tdd-workflow": "^2.0.0"
  }
}
```

### Figma Plugin

```json
{
  "skills": {
    "@tank/clean-code": "^3.0.0",
    "@tank/figma-plugin": "^1.0.0",
    "@tank/figma-to-code": "^1.0.0"
  }
}
```

### E2E Testing Project

```json
{
  "skills": {
    "@tank/clean-code": "^3.0.0",
    "@tank/bdd-e2e-testing": "^1.0.0",
    "@tank/tdd-workflow": "^2.0.0"
  }
}
```

### Minimal / New Project

```json
{
  "skills": {
    "@tank/clean-code": "^3.0.0",
    "@tank/planning": "^2.0.0"
  }
}
```

## Version Range Strategy

| Range | Meaning | When to Use |
|-------|---------|-------------|
| `^X.Y.Z` | Compatible with X (minor/patch updates) | Default — safe updates |
| `~X.Y.Z` | Patch updates only | When stability is critical |
| `*` | Any version | For skills with no breaking changes expected |
| `X.Y.Z` | Exact version | When reproducibility is paramount |

**Default**: Use `^X.Y.Z` (caret range) for all skills. This allows non-breaking
updates while locking the major version.

## Discovering New Skills

The catalog above reflects a point-in-time snapshot. To find new skills:

```bash
tank search "query"    # Search by keyword
tank search ""         # Browse all skills (if supported)
```

When the user asks for a capability not in this catalog, search the registry
first before saying it doesn't exist.
