# Tools and Automation

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Spinellis on Unix tools and version control; Horstmann on automation; Tank ast-linter-codemod, bdd-e2e-testing, and tank-package-publisher skills

Covers: choosing tools, automating coding standards, keeping the build clean, version control discipline, deployment practices, and bug-tracker hygiene.

## Operating Standard

Tools are part of the system. They are not a layer on top of "the real work" — they are the substrate that decides whether the real work is repeatable, reviewable, and deployable. A team that lets its tools rot is a team that pays compounding interest on every change.

Two failure modes dominate. First, treating tools as personal preference: "I like this formatter; you like that one; let's argue in the PR." This wastes attention that should go to design and correctness. Second, adopting tools faster than the team can absorb them: every new linter, type checker, codemod, and CI step adds maintenance, and tools that are never updated become brittle traps.

A coding agent's job in this domain is to make quality repeatable: automate what should not require willpower, treat warnings as work rather than wallpaper, write commit messages that explain why, keep deployments boring, and make sure the next bug report has enough information to be acted on.

## Quick Routing

| Situation | Principle to apply |
| --------- | ------------------ |
| Reviewer left a comment about formatting | Principle 1: Automate style; reserve humans for design |
| Build emits 200 warnings, 199 of them ignored | Principle 2: Treat warnings as work |
| Commit message is "wip" or "fix stuff" | Principle 3: Commit messages explain why |
| Build is broken on main and nobody noticed | Principle 4: A broken build is everybody's problem |
| Deployment is described in a Slack thread | Principle 5: Make deployments boring |
| Bug report has no reproduction steps | Principle 6: Bug reports without repro are not bugs |

## Principle 1: Automate style; reserve humans for design

State: any rule a tool can enforce should be enforced by a tool. Human attention in code review is a scarce resource; spending it on whitespace, import order, or quote style is malpractice.

### What goes wrong without it

PRs accumulate review comments about indentation, single vs double quotes, semicolon placement, and import order. Each comment costs an exchange between reviewer and author, plus a context switch. Meanwhile, the actual design and correctness questions get less attention because the comment threads are already long. Reviewers who care about design get tired of the noise and start rubber-stamping; reviewers who care about style start leaving the design to others.

### Anti-pattern

```javascript
// PR review comments on a 10-line change:
"Should use single quotes here (we use single quotes in this file)."
"Add a space after the comma."
"Imports should be grouped: external, then internal."
"This should be a const, not a let."
"Trailing comma missing."
"4-space indent, not 2."
"Use === not ==."
"Wrap this line, it's too long."
```

Eight comments on a 10-line change. Zero of them are about whether the change is correct, well-designed, or properly tested.

### Better approach

```json
// .prettierrc.json
{
  "singleQuote": true,
  "trailingComma": "all",
  "tabWidth": 2,
  "printWidth": 100
}
```

```yaml
# .github/workflows/ci.yml — runs on every PR
- name: Lint and format check
  run: |
    npm run lint
    npm run format:check
```

```json
// package.json — runs locally before commit
{
  "scripts": {
    "format": "prettier --write .",
    "lint": "eslint . --max-warnings=0"
  },
  "lint-staged": {
    "*.{ts,tsx,js,jsx}": ["prettier --write", "eslint --fix --max-warnings=0"]
  }
}
```

Now style is enforced by the tool chain. The author runs `npm run format` (or has it run automatically on save). CI fails fast on any deviation. Reviewers never see a formatting issue because the PR cannot reach them with one. Review comments shift entirely to design and correctness.

### Why this wins

- Reviewers spend their attention on the questions only humans can answer.
- Style decisions stop being a recurring social negotiation; they are written down once and enforced uniformly.
- New contributors learn the project's conventions automatically — running the formatter locally is the convention.

### Why the alternative loses

- Style debates burn social capital that should be spent on real disagreements.
- Reviewers who care about both style and design can only hold one in their head at a time, so one suffers.
- Inconsistent style across the codebase compounds: every new file is another negotiation.

### When this principle yields

When the tool genuinely cannot enforce the rule (a naming convention that depends on domain context, e.g., "use 'invoice' not 'bill' in finance code"), human review is appropriate. The test is whether the rule is mechanical. If yes, automate. If it requires judgment, document and review.

### Verification

A grep through PR review history shows few or no style comments. The CI failure on a style deviation is fast and clear, and the developer can reproduce and fix locally with one command.

## Principle 2: Treat warnings as work

State: a build with N warnings will eventually have N+1, then N+2. Each ignored warning trains the team to ignore the next one. Real signals get buried in noise.

### What goes wrong without it

The build has 247 warnings — most of them years old. A new deprecation warning appears for a real bug; nobody notices because it scrolls past with the others. Three months later, the deprecated API stops working, and the team is surprised. The signal was there for 90 days; the team had trained itself to ignore it.

### Anti-pattern

```bash
$ npm run build
# (build succeeds)
warning: 'someFunction' is deprecated, use 'newFunction' instead
warning: implicit any in 'request' parameter
warning: unused variable 'x'
warning: 'any' type used
... (240 more warnings)
✓ Build succeeded
```

The build "succeeds" but emits 247 warnings, every time, on every commit. New developers see the wall of warnings and assume that's normal. Real warnings about new bugs are indistinguishable from background noise.

### Better approach

Two complementary moves: ratchet existing warnings down, and fail on any new ones.

```yaml
# CI configuration: zero new warnings allowed.
- name: Build
  run: |
    npm run build 2>&1 | tee build.log
    # Compare warning count against the committed baseline.
    # If higher, fail the build.
    ./scripts/check-warning-count.sh build.log .ci/warning-baseline.txt
```

```bash
# .ci/warning-baseline.txt
247
```

Now the rule is: the count cannot go up. New code introducing a warning fails CI. Existing warnings are tracked in a single dashboard or issue, owned by someone, and decremented over time.

```bash
# Periodic cleanup PRs:
# "chore: fix 12 'unused variable' warnings (baseline 247 -> 235)"
# "chore: replace deprecated `legacyAuth` with `auth` (baseline 235 -> 220)"
```

### Why this wins

- The signal-to-noise ratio improves immediately: any new warning is a real signal, not background.
- The baseline trends down, not up. Each cleanup PR is small and reviewable.
- Deprecation warnings — which often signal real, near-future failures — become visible and actionable.

### Why the alternative loses

- A wall of ignored warnings is a wall of ignored signals. The next real bug is in there somewhere, and nobody will see it.
- New contributors learn that warnings don't matter, which is exactly the wrong lesson.
- When a deprecated API actually breaks, the team had every chance to know in advance and didn't.

### When this principle yields

When a warning is a confirmed false positive in a third-party library that cannot be fixed at the source, suppressing it locally with a clear reason (`# noqa: B007 — pylint false positive on enumerate, see issue #1234`) is the right move. The test is whether the warning will ever be acted on. If yes, fix it. If no, suppress it with a tracked reason.

### Verification

CI fails when the warning count exceeds the baseline. A monthly metric shows the baseline trending down or held flat. Any net increase requires a deliberate decision and a justification in the PR description.

## Principle 3: Commit messages explain why

State: a commit message's job is to tell the next reader (often you, six months later) why this change was necessary, not what changed. The diff already shows what changed.

### What goes wrong without it

Six months after a tricky change, you `git blame` a line and find a commit message that says `"fix"` or `"updated handler"`. The change works, but you have no way to know whether it was necessary, what edge case prompted it, or whether the constraint that justified it still applies. Refactoring becomes guesswork: "is this load-bearing or vestigial?"

### Anti-pattern

```
$ git log --oneline src/auth/middleware.ts
e3a1b2c fix
c9f4d8a updates
9d2e7f1 wip
4f8c1a3 stuff
2b6d9e8 v2
8a3f2c1 oops
```

Each commit changed something important. None of them say what or why. Six months later, you have no narrative — just a sequence of changes that may or may not still be load-bearing.

### Better approach

```
$ git log src/auth/middleware.ts

fix(auth): treat expired refresh tokens as logged-out, not as 500

Previously, an expired refresh token threw a JwtExpiredError that wasn't
caught by the error middleware, surfacing as 500 to the client. The
correct behavior is to clear the cookie and return 401 so the client
redirects to login.

Reproduces with: a refresh token whose `exp` is in the past.
Test: tests/auth/expired_refresh_token_test.ts.
Customer report: SUPPORT-4521.

---

refactor(auth): extract token-validation to its own helper

The middleware was doing three things (parse, validate, check user
exists). Extracting validation makes the middleware readable and lets
us add structured logging at the validation step without entangling
parsing and user lookup.

No behavior change; same tests pass.

---

feat(auth): require re-authentication for sensitive routes

The /admin and /billing routes now require the session to have been
authenticated within the last 30 minutes, regardless of token validity.
This was requested by Security as part of the SOC2 audit (SEC-118).

Sensitive routes are listed in src/auth/sensitive-routes.ts.
The 30-minute threshold is configurable via SENSITIVE_REAUTH_MINUTES.
```

Each commit message explains: what user-visible behavior changed (or didn't), why the change was necessary, what test or evidence proves it, and what external context (ticket, customer report, audit requirement) drove the decision.

### Why this wins

- A future maintainer can answer "why was this done?" without phoning the original author.
- `git blame` on a single line gives the full story, including external constraints.
- Refactors become safer because load-bearing requirements are documented in the commits that established them.

### Why the alternative loses

- "fix" and "updates" force every future maintainer to either dig (cost) or guess (risk).
- External context (ticket numbers, audit requirements, customer reports) gets lost.
- Refactoring decisions become "I'm afraid to touch this; nobody knows why it works this way."

### When this principle yields

For genuinely trivial changes (a typo fix, a one-line dependency bump, a comment fix), a one-line commit message is fine. The test is whether a future maintainer might wonder "why was this done?" If yes, write the why.

### Verification

`git log` on any module's history reads like a coherent narrative. Pick a random line and `git blame` it: the resulting commit message answers "why does this line exist?"

## Principle 4: A broken build is everybody's problem

State: when the build is broken on the main branch, no one merges anything else until it's fixed. The team owns the build collectively.

### What goes wrong without it

The build breaks on main. Engineers continue merging on top of the breakage because "my change isn't related." The breakage compounds — now there are five overlapping changes on top of the original bug, and isolating the root cause requires bisecting through all of them. The fix takes hours instead of minutes. Meanwhile, deployment is blocked, integration tests are unreliable, and the team's confidence in CI drops.

### Anti-pattern

```
Engineer A merges to main: build fails (timeout in test #47).
Engineer A: "Probably flaky, I'll look at it later."

Engineer B merges 30 minutes later: build still failing.
Engineer B: "Build's already broken, mine's fine, I'll just merge."

Engineer C merges 1 hour later: build still failing.
Engineer C: "Same here, my change is unrelated."

End of day: 14 commits on a broken build. Nobody knows which break what.
A's "flaky" test was actually a real bug introduced by A. Everyone else's
work is now harder to ship until A's bug is fixed.
```

### Better approach

A simple rule, enforced socially and (where possible) by tooling:

```yaml
# .github/branch-protection rules
main:
  require_status_checks: true
  required_checks: [build, tests, lint]
  block_merge_on_failure: true
```

Plus a team agreement:

> If the build is broken on main, the highest priority for everyone is fixing it. Either revert the breaking commit, or land the fix immediately. No new merges on top of a broken main.

When A's build fails, the responses are: (1) A reverts immediately, (2) A pushes a hotfix immediately, or (3) the team helps A diagnose. None of those involve B and C piling on.

### Why this wins

- Bugs are isolated to the commit that introduced them. Bisecting takes seconds, not hours.
- The team's trust in CI stays high because a green main means a working main.
- The cost of a broken build stays low because it gets fixed immediately rather than buried.

### Why the alternative loses

- Once main is broken, every merge on top of it interacts with the breakage in unpredictable ways.
- Bisecting becomes expensive because multiple unrelated changes have to be untangled.
- Deployment from main becomes a coin flip: is today's broken main shippable or not?

### When this principle yields

It does not. A broken main is always a higher priority than the next merge. The closest exception is when the breakage is provably a CI infrastructure issue (the test runner itself is down) — in which case the fix is at the infrastructure level and merges that don't touch the affected paths might still be safe.

### Verification

A green main is the steady state. When red, the team's conversation immediately shifts to "who's fixing it?" The mean time to recover from a broken main is measured in minutes, not hours.

## Principle 5: Make deployments boring

State: deployment should be a one-button operation that anyone on the team can run, with a known rollback procedure. If deployment requires tribal knowledge, the system is one vacation away from being unshippable.

### What goes wrong without it

Deployment is documented as "ssh into the prod box, run `./deploy.sh`, then run the migration manually if needed, then check the logs for errors, then restart the worker fleet." It works when the senior engineer is around; it doesn't work on weekends. A bug that needs an urgent fix sits unshipped for two days because nobody else feels confident running the procedure.

### Anti-pattern

```
# Deployment runbook (in a Notion doc someone wrote two years ago):

1. SSH into prod-app-01: ssh deploy@prod-app-01.example.com
2. cd /opt/app
3. git pull
4. ./deploy.sh
5. If migrations: ./run-migrations.sh
6. Restart workers: sudo systemctl restart app-workers
7. Check /var/log/app/error.log for the next 5 minutes
8. If errors, see "Rollback" section (which is empty)
```

Eight steps, each with implicit prerequisites. Steps 5 and 7 require judgment ("how do I know if I need migrations?"). Step 8 has no rollback procedure. Most of the team has never run this.

### Better approach

```yaml
# .github/workflows/deploy.yml — triggered by tagging a release.
on:
  push:
    tags: ["v*"]

jobs:
  deploy:
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup
      - name: Run migrations
        run: ./scripts/migrate.sh ${{ env.DATABASE_URL }}
      - name: Deploy app
        run: ./scripts/deploy.sh ${{ github.ref_name }}
      - name: Health check
        run: ./scripts/healthcheck.sh https://app.example.com
        timeout-minutes: 5
      - name: Rollback on failure
        if: failure()
        run: ./scripts/rollback.sh
```

```bash
# scripts/rollback.sh
#!/usr/bin/env bash
set -euo pipefail
PREVIOUS_VERSION=$(./scripts/previous-deployed-version.sh)
echo "Rolling back to ${PREVIOUS_VERSION}..."
./scripts/deploy.sh "${PREVIOUS_VERSION}"
./scripts/healthcheck.sh https://app.example.com
```

Deployment is now: tag a release. Everything else happens automatically, including rollback if the health check fails. Anyone on the team can deploy. Anyone can roll back. The runbook is the script — not a Notion doc that goes stale.

### Why this wins

- Deployment risk drops because the procedure is identical every time.
- Anyone can ship a fix. Vacations and weekends stop being release blockers.
- Rollback is automatic on health-check failure, so a bad deploy never lingers.
- The deployment script is checked into version control and reviewed like other code.

### Why the alternative loses

- Tribal knowledge means single points of failure. The senior engineer becomes a bottleneck.
- Manual deployment steps drift over time; the runbook stops matching reality.
- Rollback is an afterthought, which means the first time you need it is also the first time you've tried it.

### When this principle yields

In genuinely small environments where setting up CI/CD has higher cost than the value (a one-engineer prototype with one user), a clear bash script and a written rollback procedure can be enough. The test is whether anyone other than the original author would be able to deploy at 3am. If no, automate.

### Verification

A junior engineer who has never deployed before can ship a release end-to-end without supervision. A bad deploy is automatically rolled back; the team is alerted but does not need to take manual action.

## Principle 6: Bug reports without reproduction are not bugs yet

State: an actionable bug report includes observed behavior, expected behavior, environment, and steps to reproduce. Without those, it's a feeling, not a bug — and "fixing" feelings produces speculative changes.

### What goes wrong without it

A vague bug report ("the dashboard is slow sometimes") triggers a speculative fix ("let's add caching"). The cache adds a class of bugs (stale data, invalidation errors), the original "slow" complaint either resurfaces or gets attributed to "fixed" for unrelated reasons, and the team has shipped complexity without knowing whether it solved the real problem.

### Anti-pattern

```
Bug report (Slack message):
"Hey, the dashboard seems slow today, can you look into it?"

Engineer (one hour later):
"Added Redis caching for the dashboard query. Should be faster now."

Two weeks later:
- The original "slow" was a one-off database hot spot during a backup.
- The Redis cache now has stale-data bugs that take three weeks to surface.
- The team is debugging cache invalidation instead of database hotspots.
- Nobody can prove the dashboard is faster because there's no baseline.
```

### Better approach

A bug report template that the issue tracker enforces:

```markdown
## Observed behavior
What happened? (Be specific. Screenshots, error messages, timestamps.)

## Expected behavior
What should have happened?

## Steps to reproduce
1. Go to ...
2. Click ...
3. Observe that ...

## Environment
- Browser/OS:
- Account/User ID:
- Approximate time of incident:
- Build/commit (if known):

## Logs / supporting evidence
(Paste relevant log lines, network traces, or screenshots.)
```

When the dashboard slowness gets reported with this template, the engineer asks for the missing fields:

```
"Thanks for the report. Before I dig in:
1. Approximately when did you observe the slowness? (date and time, with timezone)
2. Were you on the team dashboard or the user dashboard?
3. Was it consistently slow, or only the first load?
4. Roughly how slow — 2 seconds? 10? 30?

This will let me check the metrics and database logs for the same window."
```

The reporter responds: "Yesterday around 2pm, team dashboard, only the first load, about 8 seconds." The engineer checks the database logs and finds a known issue (a backup that ran at 1:55pm). No code change needed. Feedback to the reporter, root cause logged, the next backup scheduled outside business hours.

### Why this wins

- Speculative changes do not happen. The team only changes code when there is real evidence of a problem.
- Bug reports get triaged faster because the necessary information is in the report.
- Reporters learn the format and submit better reports next time.

### Why the alternative loses

- Vague reports lead to vague fixes. The fixes add complexity without proven value.
- Engineers spend time chasing ghosts because the original signal was too weak to act on.
- Reporters get the impression that bug reports don't get fixed (because the engineer doesn't know what to fix), so they stop reporting bugs.

### When this principle yields

For internal-team reports of incidents that are still in progress (an active production outage), the reproduction can come after triage. The test is whether the bug is happening now or already happened. Active incidents skip the template; post-incident reports use it.

### Verification

The bug tracker has a template and uses it. The triage backlog rarely contains "needs more info" tickets older than a week — they get either filled in or closed.

## Routing

Use `@tank/ast-linter-codemod` when a coding standard needs to become a custom lint rule with auto-fix.

Use `@tank/bdd-e2e-testing` for end-to-end CI verification of behavior against real systems.

Use `@tank/tank-package-publisher` for the Tank skill release workflow specifically.

Use `git-master` for complex git operations: rebases, history surgery, blame archaeology, bisect.

Use `references/refactoring-and-removal.md` when the right move is to delete a tool, helper, or config rather than add one.
