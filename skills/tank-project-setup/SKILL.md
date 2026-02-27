---
name: tank-project-setup
description: |
  Auto-detect project stack and integrate Tank skills into any repository.
  Scans for framework indicators (package.json, pyproject.toml, angular.json,
  tsconfig.json, etc.), recommends relevant Tank skills, creates project-level
  skills.json, runs `tank install`, and sets up CI/CD pipelines (GitHub Actions,
  GitLab CI) so skills install automatically — like `npm ci` for agent skills.

  Trigger phrases: "set up tank", "add tank to project", "tank init project",
  "install tank skills", "detect project type", "tank ci/cd", "tank cicd",
  "configure tank for this repo", "add skills to project", "tank install setup",
  "integrate tank", "set up agent skills", "project skills setup",
  "add tank to ci", "tank github action"
---

# Tank Project Setup

Detect project stack, install relevant Tank skills, and wire up CI/CD so every
clone gets skills automatically via `tank install`.

## Core Workflow

Execute steps in order. Do not skip.

### Step 1: Detect Project Stack

Run `scripts/detect-project.sh` in the project root, or manually scan for:

| File | Stack Signal |
|------|-------------|
| `package.json` | Node.js (inspect `dependencies` for framework) |
| `tsconfig.json` | TypeScript |
| `next.config.*` | Next.js |
| `angular.json` | Angular |
| `tailwind.config.*` | Tailwind CSS |
| `pyproject.toml` / `requirements.txt` | Python |
| `.github/` | GitHub-hosted (CI target) |
| `docker-compose.yml` | Docker/infrastructure |
| `prisma/` / `drizzle.config.*` | Database ORM |
| `playwright.config.*` / `cypress.config.*` | E2E testing |
| `figma-plugin/manifest.json` | Figma plugin |

Present detected stack to user for confirmation before proceeding.

### Step 2: Map Stack to Skills

Use the mapping table in `references/SKILL_CATALOG.md` to select skills.
Always include `@tank/clean-code` unless user opts out.

### Step 3: Create or Update skills.json

If `skills.json` exists at project root, merge new skills into the `skills`
field. If not, create one:

```json
{
  "skills": {
    "@tank/clean-code": "^3.0.0",
    "@tank/react": "^2.0.0"
  }
}
```

**Project-level skills.json** only needs the `skills` field — it is NOT a
skill manifest (no `name`, `version`, or `permissions` required).

### Step 4: Install Skills

```bash
tank install
```

This reads `skills.json`, resolves versions, downloads packages to the local
`.tank/` cache, and creates `skills.lock` with SHA-512 integrity hashes.

After install, verify:
```bash
tank doctor
tank permissions
```

### Step 5: Set Up CI/CD

Detect CI platform and add `tank install` step:

- **GitHub Actions**: See `assets/github-action-tank-install.yml`
- **GitLab CI**: See `references/CICD_INTEGRATION.md`

Key requirements for CI:
1. Install Tank CLI: `npm install -g @tankpkg/cli`
2. Run `tank install` (reads lockfile for deterministic installs)
3. Run `tank verify` to confirm integrity

**No authentication needed for `tank install`** — only `tank publish` requires auth.

### Step 6: Update .gitignore

Add Tank artifacts that should not be committed:

```
# Tank skills (installed via tank install)
.tank/
```

Ensure `skills.json` and `skills.lock` ARE committed (like package.json and
package-lock.json).

## Decision Tree: When to Use Global vs Local

| Scenario | Install Type | Command |
|----------|-------------|---------|
| Skills shared across all projects | Global | `tank install -g @org/skill` |
| Skills specific to this project | Local | `tank install @org/skill` |
| CI/CD pipeline | Local (from lockfile) | `tank install` |
| Developer onboarding | Local (from lockfile) | `tank install` |

## Quick Reference: Tank Consumer Commands

```bash
tank install                     # Install all from lockfile
tank install @org/skill          # Add specific skill
tank install -g @org/skill       # Install globally
tank update                      # Update all within ranges
tank update @org/skill           # Update specific skill
tank remove @org/skill           # Remove skill
tank verify                      # Verify lockfile integrity
tank permissions                 # Show permission summary
tank doctor                      # Health check
tank search "query"              # Find skills in registry
tank info @org/skill             # Show skill metadata
```

## Failure Map

| Problem | Fix |
|---------|-----|
| `tank: command not found` | `npm install -g @tankpkg/cli` |
| `No skills.json found` | Create one with `skills` field or run `tank init` |
| `Version not found` | Check available versions: `tank info @org/skill` |
| `Integrity check failed` | Delete `skills.lock` and `.tank/`, re-run `tank install` |
| `Permission denied in CI` | No auth needed for install; check file permissions |

## Resources

### References

- [references/PROJECT_DETECTION.md](references/PROJECT_DETECTION.md) — Detection signals, priority order, confidence scoring
- [references/CICD_INTEGRATION.md](references/CICD_INTEGRATION.md) — CI/CD templates for GitHub Actions, GitLab CI, CircleCI
- [references/SKILL_CATALOG.md](references/SKILL_CATALOG.md) — Complete project-type to Tank skill mapping

### Scripts

- `scripts/detect-project.sh <dir>` — Scan project directory and output detected stack as JSON

### Assets

- [assets/github-action-tank-install.yml](assets/github-action-tank-install.yml) — Drop-in GitHub Actions workflow
- [assets/project-skills.json.template](assets/project-skills.json.template) — Starter project-level skills.json
