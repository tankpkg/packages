# Project Detection Guide

How to identify project stack from filesystem indicators and map to Tank skills.

## Detection Strategy

Scan the project root for indicator files in priority order. Each match adds
to the detected stack. A project can (and usually does) match multiple signals.

**Priority order matters**: check framework-specific files before generic ones.
For example, `next.config.js` (Next.js) before `package.json` (generic Node.js).

## Detection Rules

### Tier 1: Framework-Specific (Highest Confidence)

These files unambiguously identify a framework:

| Indicator File | Stack | Confidence |
|---------------|-------|------------|
| `next.config.js` / `next.config.mjs` / `next.config.ts` | Next.js | 100% |
| `angular.json` / `.angular-cli.json` | Angular | 100% |
| `nuxt.config.ts` / `nuxt.config.js` | Nuxt.js | 100% |
| `svelte.config.js` | SvelteKit | 100% |
| `astro.config.mjs` / `astro.config.ts` | Astro | 100% |
| `remix.config.js` / `remix.config.ts` | Remix | 100% |
| `figma-plugin/manifest.json` / `manifest.json` (with `api` field) | Figma Plugin | 100% |

### Tier 2: Tooling-Specific (High Confidence)

| Indicator File | Stack | Confidence |
|---------------|-------|------------|
| `tsconfig.json` | TypeScript | 95% |
| `tailwind.config.js` / `tailwind.config.ts` / `tailwind.config.mjs` | Tailwind CSS | 95% |
| `playwright.config.ts` / `playwright.config.js` | Playwright/E2E | 95% |
| `cypress.config.ts` / `cypress.config.js` / `cypress.json` | Cypress/E2E | 95% |
| `jest.config.*` / `vitest.config.*` | Unit Testing | 90% |
| `prisma/schema.prisma` | Database (Prisma) | 95% |
| `drizzle.config.ts` / `drizzle.config.js` | Database (Drizzle) | 95% |
| `.eslintrc.*` / `eslint.config.*` | Linting | 85% |

### Tier 3: Language & Runtime (Medium Confidence)

| Indicator File | Stack | Confidence |
|---------------|-------|------------|
| `package.json` | Node.js | 90% |
| `pyproject.toml` | Python (modern) | 90% |
| `requirements.txt` | Python (legacy) | 85% |
| `setup.py` / `setup.cfg` | Python (legacy) | 80% |
| `Cargo.toml` | Rust | 95% |
| `go.mod` | Go | 95% |
| `Gemfile` | Ruby | 90% |
| `pom.xml` / `build.gradle` | Java/Kotlin | 90% |
| `*.csproj` / `*.sln` | .NET/C# | 90% |

### Tier 4: Infrastructure (Context Signals)

| Indicator File | Stack | Confidence |
|---------------|-------|------------|
| `.github/` | GitHub-hosted | 95% |
| `.gitlab-ci.yml` | GitLab CI | 95% |
| `Dockerfile` / `docker-compose.yml` | Docker | 90% |
| `terraform/` / `*.tf` | Terraform | 90% |
| `k8s/` / `kubernetes/` | Kubernetes | 85% |
| `vercel.json` | Vercel deployment | 90% |
| `netlify.toml` | Netlify deployment | 90% |

## Deep Inspection: package.json

When `package.json` exists, inspect `dependencies` and `devDependencies`
for framework detection:

```
"react"           → React project
"next"            → Next.js project
"express"         → Express/Node API server
"@angular/core"   → Angular project
"vue"             → Vue.js project
"svelte"          → Svelte project
"tailwindcss"     → Tailwind CSS
"prisma"          → Prisma ORM (database)
"drizzle-orm"     → Drizzle ORM (database)
"@playwright/test" → Playwright testing
"cypress"         → Cypress testing
"jest"            → Jest testing
"vitest"          → Vitest testing
```

### Express Detection Heuristic

Express alone doesn't mean "API server" — it could be middleware for Next.js.
Check for:

1. `express` in `dependencies` (not devDependencies)
2. Absence of `next` / `@angular/core` / `vue` in dependencies
3. Presence of server-like files: `server.js`, `app.js`, `index.js` at root
4. Presence of `routes/` or `controllers/` directories

If 2+ of these match → likely an Express API server.

## Deep Inspection: pyproject.toml

When `pyproject.toml` exists, inspect for framework signals:

```toml
[tool.poetry.dependencies]    # or [project.dependencies]
fastapi = "..."               → FastAPI (Python API)
django = "..."                → Django
flask = "..."                 → Flask
pytest = "..."                → Testing
sqlalchemy = "..."            → Database ORM
```

## Detection Output Format

The detection script should output JSON:

```json
{
  "languages": ["typescript", "python"],
  "frameworks": ["next.js", "tailwind"],
  "tools": ["playwright", "prisma"],
  "ci_platform": "github-actions",
  "infrastructure": ["docker", "vercel"],
  "recommended_skills": [
    { "name": "@tank/clean-code", "version": "^3.0.0", "reason": "Universal code quality" },
    { "name": "@tank/react", "version": "^2.0.0", "reason": "React detected in package.json" },
    { "name": "@tank/tdd-workflow", "version": "^2.0.0", "reason": "Playwright config detected" }
  ]
}
```

## Edge Cases

### Monorepos

Check for monorepo indicators:

| Indicator | Tool |
|-----------|------|
| `pnpm-workspace.yaml` | pnpm workspaces |
| `lerna.json` | Lerna |
| `nx.json` | Nx |
| `turbo.json` | Turborepo |
| `packages/` or `apps/` directories | Convention-based |

For monorepos, scan each workspace root individually and merge results.
The project-level `skills.json` should include the union of all workspace needs.

### Hybrid Projects

A project can be both frontend and backend (e.g., Next.js with Prisma).
Include skills for ALL detected stacks — don't pick one over the other.

### Empty / New Projects

If no indicators found:
1. Ask the user what they're building
2. Suggest starting with `@tank/clean-code` and `@tank/planning`
3. Offer to set up skills.json with their choices

### Pre-existing skills.json

If `skills.json` already exists with a `skills` field:
1. Read existing skill dependencies
2. Detect stack that isn't already covered
3. Suggest additions (don't remove existing skills)
4. Let user confirm before modifying

## Detection Algorithm (Pseudocode)

```
function detectProject(rootDir):
  stack = {}

  # Tier 1: Framework-specific
  for each (file, framework) in TIER_1_RULES:
    if exists(rootDir / file):
      stack.frameworks.add(framework)

  # Tier 2: Tooling
  for each (file, tool) in TIER_2_RULES:
    if exists(rootDir / file):
      stack.tools.add(tool)

  # Tier 3: Language
  if exists(rootDir / "package.json"):
    stack.languages.add("javascript")
    pkg = parseJSON("package.json")
    inspectDependencies(pkg, stack)

  if exists(rootDir / "tsconfig.json"):
    stack.languages.add("typescript")

  if exists(rootDir / "pyproject.toml") or exists("requirements.txt"):
    stack.languages.add("python")
    inspectPythonDeps(stack)

  # Tier 4: Infrastructure
  if exists(rootDir / ".github"):
    stack.ci_platform = "github-actions"
  elif exists(rootDir / ".gitlab-ci.yml"):
    stack.ci_platform = "gitlab-ci"

  # Map to skills
  stack.recommended_skills = mapToSkills(stack)

  return stack
```

## Confidence Threshold

Only include a skill recommendation when detection confidence >= 80%.
For confidence < 80%, mention the signal to the user and ask for confirmation.
