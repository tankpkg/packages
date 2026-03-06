# Drift Detection

Sources: ArcBlock/idd sync command (MIT), Praxis spec-check concept (MIT),
FORGE Evaluate phase (MIT), configuration drift patterns from infrastructure
management literature.

Covers: drift definition, sync process (Step 8), drift categories, audit
dimensions (Step 9), health scoring, CI/CD integration, automated detection,
common drift patterns.

## What Is Drift

Drift is the gap between what an intent file says and what the code actually
does. It accumulates silently — no alarm fires when a function signature
changes without updating INTENT.md.

Two directions:

| Direction | Definition | Risk |
|-----------|------------|------|
| Forward drift | Code is ahead of intent | AI gets stale guidance; intent is fiction |
| Backward drift | Intent is ahead of code | Intent describes unbuilt features; misleads new contributors |

**Why drift happens:**

- Implementation reveals reality — the design changes as you build
- Scope changes — a constraint gets relaxed under pressure
- Emergency patches — a hotfix lands without an intent update
- Parallel work — two developers update code and intent independently

**Why drift matters:**

AI agents read intent files as ground truth. Stale intent produces stale
code. New team members read intent to understand the system — wrong intent
means wrong mental model. Drift turns intent from a living spec into
abandoned documentation.

## The Sync Process (Step 8)

Sync is the structured reconciliation of intent against code. Run it after
any significant implementation phase, before a release, or whenever the
`needs: [sync]` flag appears in frontmatter.

For the full lifecycle context, see `references/idd-lifecycle.md` Step 8.

### Step-by-Step Sync

**1. Scan the codebase**

Identify the public surface of the module: exported functions, types,
classes, route handlers, event names, data structures. Focus on what
crosses module boundaries — internal helpers are secondary.

```bash
# List all exports from a TypeScript module
grep -r "^export" src/auth/ --include="*.ts" | sort

# List all route definitions
grep -r "router\.\(get\|post\|put\|delete\|patch\)" src/api/ --include="*.ts"
```

**2. Compare against INTENT.md section by section**

Walk each section of the intent file and check it against the scan:

- Responsibilities: does the code do what's listed? Does it do more?
- Structure: does the directory tree match?
- Constraints: are the rules enforced in code?
- API: do signatures match? Are parameters and return types accurate?
- Examples: do the input-output pairs still hold?

**3. Categorize every diff**

| Category | Definition | Action |
|----------|------------|--------|
| New | Exists in code, not in intent | Add to intent or decide it's internal |
| Changed | Both exist but differ | Update intent to match code reality |
| Confirmed | Code matches intent exactly | No action needed |
| Removed | Exists in intent, not in code | Delete from intent (dead intent) |

**4. Present the diff report**

Generate a structured report before making any changes. Format:

```markdown
# Sync Report: Auth Module
Date: 2026-03-06
Commit: a3f9c12

## New (in code, not in intent)
- `refreshToken(token: string): Promise<Session>` — not documented
- `src/auth/middleware/csrf.ts` — new file, not in structure diagram

## Changed
- `authenticate()` now returns `Session | null` (was `Session`)
- Rate limit changed from 5/min to 10/min per IP

## Confirmed
- Session TTL configurable: confirmed
- All auth errors return 401: confirmed

## Removed (in intent, not in code)
- `revokeAllSessions(userId)` — removed in commit b2e1a09
```

**5. Human approves updates**

Present the report. The human decides:
- Which "New" items belong in intent vs. stay as internal implementation
- Whether "Changed" items reflect intentional decisions or accidental drift
- Whether "Removed" items should be deleted or flagged as planned work

**6. Update INTENT.md**

Apply only the approved changes. Do not silently update — every change
should trace to a human decision in the sync report.

**7. Add sync marker**

Append a sync marker to the intent file immediately after the anchor block:

```markdown
> Synced: 2026-03-06 from commit a3f9c12
```

Update this marker on every sync. It tells readers exactly how fresh the
intent is. Archive the full sync report in `.idd/modules/auth/records/`.

## Drift Categories by Layer

Each of the three intent layers drifts differently:

| Layer | What Drifts | How to Detect | What to Do |
|-------|-------------|---------------|------------|
| Structure | Directory tree, file names, module boundaries | `find src/auth -type f` vs. tree in intent | Update ASCII diagram |
| Constraints | Import rules, performance limits, error codes | grep for forbidden patterns; run benchmarks | Update constraint table; add test if missing |
| Examples | Function signatures, return types, error shapes | Run examples as tests; compare actual output | Update example table; flag if behavior changed intentionally |

**Structure drift** is the easiest to detect — file paths are concrete.
**Constraint drift** is the most dangerous — a relaxed constraint may
indicate a security regression, not just a documentation gap.
**Example drift** is the most actionable — if examples fail as tests,
the intent is provably wrong.

## Audit Dimensions (Step 9)

Audit is the periodic health check across all intent files in the project.
Where sync focuses on one module, audit covers the entire `.idd/` tree.

For the full lifecycle context, see `references/idd-lifecycle.md` Step 9.

| Dimension | What to Measure | Detection Method | Flag Threshold |
|-----------|----------------|------------------|----------------|
| Coverage | Modules with intent / total modules | `find src -maxdepth 1 -type d` vs. `.idd/modules/` | < 80% |
| Freshness | Days since intent edit vs. last code commit | `git log -1 --format="%ct"` on both paths | > 14 days gap |
| Budget | Line count per intent file | `grep -c "" INTENT.md` | > 300 warn; > 500 block |
| Approval | Status distribution across all intents | `grep -r "^status:" .idd` | > 20% draft |
| Dependencies | Declared `Depends:` vs. actual imports | grep imports in source; compare to tags | Any undeclared dep |
| Boundary violations | Forbidden import patterns in source | grep for each rule in `boundaries.md` | Any match |
| Orphans | Intent files with no matching `src/` dir | Compare `.idd/modules/` to `src/` | Any orphan |
| Stale references | `Depends:` / `See also:` paths that don't exist | `[ -e "$path" ]` for each extracted path | Any missing |

**Coverage**: target 100% of public modules; internal utilities may be exempt.

**Freshness**: store results in `.idd/_data/freshness.json`. Flag intents
where source was modified more than 14 days after the intent was last updated.

**Budget**: thresholds defined in `references/quality-enforcement.md`.
Healthy ≤ 300 lines; warning 301–500; blocked > 500.

**Approval**: high draft percentage signals incomplete intent work. High
implemented percentage with no recent syncs signals staleness risk.

**Boundary violations**: a single violation is blocking — constraints exist
for architectural reasons, not style preferences.

**Orphans**: accumulate when modules are renamed or deleted. Remove or
update paths immediately.

**Stale references**: break the dependency graph and mislead audit tools.
Fix by updating or removing the tag.

## Health Scoring

Combine audit dimensions into a single composite score (0–100).

### Score Formula

| Dimension | Weight | How to Score |
|-----------|--------|--------------|
| Coverage | 20 | (modules with intent / total modules) × 20 |
| Freshness | 20 | (intents updated within 14d of code change / total) × 20 |
| Budget | 15 | (intents within budget / total) × 15 |
| Approval | 10 | (active + implemented / total) × 10 |
| Dependencies | 15 | (declared deps matching actual / total declared) × 15 |
| Boundary violations | 10 | 10 if zero violations; 0 if any violation |
| Orphans | 5 | (non-orphan intents / total) × 5 |
| Stale references | 5 | (valid refs / total refs) × 5 |

### Score Interpretation

| Score | Status | Meaning |
|-------|--------|---------|
| 90–100 | Excellent | Intent is current and complete |
| 70–89 | Good | Minor gaps; address in next sprint |
| 50–69 | Needs attention | Significant drift; schedule sync sessions |
| < 50 | Unhealthy | Intent is unreliable; block AI-assisted work |

### Generating a Health Report

Store computed scores in `.idd/_data/health.json` with keys: `score`,
`computed_at`, per-dimension scores, `violations` array, and `warnings`
array. Print a one-line summary to stdout for CI logs:

```
IDD Health Score: 84/100 (Good) | Violations: 1 (blocking) | Warnings: 1
```

Archive full reports in `.idd/records/` with date-stamped filenames.

## CI/CD Integration

Run drift checks automatically to catch violations before they merge.

### GitHub Actions Step

```yaml
- name: IDD Audit
  run: |
    # Budget check — fail on blocked intents (> 500 lines)
    find .idd -name "INTENT.md" | while read f; do
      lines=$(grep -c "" "$f")
      if [ "$lines" -gt 500 ]; then
        echo "BLOCKED: $f has $lines lines"; exit 1
      fi
    done
    # Boundary violation check
    bash .idd/scripts/check-boundaries.sh
    # Freshness warning (non-blocking)
    bash .idd/scripts/check-freshness.sh --warn-only
```

### Pre-Commit Hook

Enforce budget on every commit that touches an intent file:

```bash
#!/bin/bash
# .git/hooks/pre-commit
for f in $(git diff --cached --name-only | grep "INTENT.md"); do
  lines=$(grep -c "" "$f")
  if [ "$lines" -gt 500 ]; then
    echo "ERROR: $f exceeds 500-line budget. Run critique first."
    exit 1
  fi
done
```

### When to Block Merges

| Condition | Action |
|-----------|--------|
| Any intent file > 500 lines | Block merge |
| Any boundary violation detected | Block merge |
| Health score < 50 | Block merge |
| Freshness gap > 30 days | Warn only |
| Coverage < 80% | Warn only |

Block on violations that indicate architectural regression. Warn on
conditions that indicate documentation lag.

## Automated Detection Patterns

### Boundary Violation Detection

Parse each module's `boundaries.md` for forbidden import patterns, then
grep the source tree. Any match is a blocking violation.

```bash
# Check for forbidden auth → payments imports
result=$(grep -r "from.*payments" src/auth/ 2>/dev/null)
[ -n "$result" ] && echo "VIOLATION: auth imports from payments" && exit 1
```

Store the full check logic in `.idd/scripts/check-boundaries.sh`.

### Freshness Check

Compare git timestamps: last commit touching `INTENT.md` vs. last commit
touching the corresponding `src/` directory.

```bash
intent_ts=$(git log -1 --format="%ct" -- .idd/modules/auth/INTENT.md)
code_ts=$(git log -1 --format="%ct" -- src/auth/)
gap=$(( (code_ts - intent_ts) / 86400 ))
[ "$gap" -gt 14 ] && echo "STALE: auth intent is ${gap}d behind source"
```

### Dependency Validation

Extract `Depends:` tags from each intent, then verify actual imports exist
in the source tree. Zero results means the declared dependency is dead intent.

```bash
# Declared: auth depends on database — verify actual imports exist
grep -r "from.*database" src/auth/ --include="*.ts" | wc -l
```

### Orphan Detection

```bash
for intent in .idd/modules/*/INTENT.md; do
  module=$(basename $(dirname "$intent"))
  [ ! -d "src/$module" ] && echo "ORPHAN: $intent has no src/$module"
done
```

## Common Drift Patterns and Fixes

| Pattern | Cause | Detection | Fix |
|---------|-------|-----------|-----|
| Signature drift | Refactor without intent update | Compare exported types to API section | Update API section; add sync marker |
| Phantom constraint | Constraint removed under pressure | grep for forbidden pattern; find nothing | Remove constraint or restore enforcement |
| Ghost function | Function deleted; intent not updated | grep for function name in source | Delete from intent; note in sync report |
| Structure sprawl | New files added without updating tree | `find src/module -type f` vs. intent tree | Update ASCII diagram |
| Dependency creep | New import added without declaring | grep imports vs. `Depends:` tag | Add to `Depends:` or refactor import |
| Stale example | Return type changed; example not updated | Run example as test | Update example table |
| Orphan intent | Module renamed or deleted | Compare `.idd/modules/X` to `src/X` | Delete or move intent file |
| Budget overflow | Scope expanded without critique | Line count check | Run critique; split or trim |

For budget enforcement rules and critique procedures, see
`references/quality-enforcement.md`.

For the full IDD lifecycle including when to trigger sync and audit,
see `references/idd-lifecycle.md`.
