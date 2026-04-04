# Syntax

Sources: GitHub Actions official documentation, workflow syntax reference, reusable workflow docs, community CI/CD workflow examples

Covers: workflow structure, triggers, jobs, steps, matrices, expressions, contexts, env/secrets, reusable workflows, artifacts, and common GitHub Actions YAML snippets.

## Basic Workflow Shape

```yaml
name: CI

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test
```

## Trigger Syntax

| Need | Syntax |
|-----|--------|
| push trigger | `on: push` |
| PR trigger | `on: pull_request` |
| manual trigger | `workflow_dispatch` |
| schedule | `schedule:` + cron |

## Jobs and Steps

| Concern | Syntax |
|--------|--------|
| runner | `runs-on:` |
| dependent job | `needs:` |
| step command | `run:` |
| step action | `uses:` |

## Matrix Syntax

```yaml
strategy:
  matrix:
    node: [18, 20]
    os: [ubuntu-latest, windows-latest]
```

## Expressions and Contexts

| Concern | Example |
|--------|---------|
| expression | `${{ github.ref }}` |
| conditional | `if: ${{ github.event_name == 'pull_request' }}` |
| matrix value | `${{ matrix.node }}` |
| secrets | `${{ secrets.MY_SECRET }}` |

## Env and Secrets

| Scope | Syntax |
|------|--------|
| workflow env | top-level `env:` |
| job env | under job `env:` |
| step env | under step `env:` |

## Reusable Workflows

| Need | Syntax |
|-----|--------|
| define reusable workflow | `on: workflow_call` |
| call reusable workflow | `uses: org/repo/.github/workflows/file.yml@ref` |

## Artifacts and Outputs

| Task | Pattern |
|-----|---------|
| upload artifact | `actions/upload-artifact` |
| download artifact | `actions/download-artifact` |
| job outputs | `outputs:` + step IDs |

## Common Snippets

| Need | Snippet focus |
|-----|---------------|
| checkout code | `actions/checkout` |
| setup Node | `actions/setup-node` |
| cache deps | cache or setup-* built-ins |
| conditionals | `if:` with contexts |

## Trigger Patterns

| Need | Example |
|-----|---------|
| branch-restricted push | `push.branches` |
| path-filtered workflow | `paths:` |
| tag release | `push.tags` |
| manual input workflow | `workflow_dispatch.inputs` |

Triggers should match the release/event model precisely enough to avoid noisy or missing runs.

## Job Structure Patterns

| Concern | Example |
|--------|---------|
| dependency chain | `needs: [build]` |
| timeout | `timeout-minutes:` |
| permissions | `permissions:` |
| environment | `environment:` |

## Matrix Expansion Notes

| Pattern | Benefit |
|--------|---------|
| OS × runtime matrix | broad compatibility checks |
| include/exclude | shape the matrix intentionally |
| fail-fast control | manage flaky/expensive jobs |

### Matrix review questions

1. Is this matrix testing useful dimensions or just making CI slower?
2. Should any combinations be excluded explicitly?
3. Does one job really need the full matrix or just part of it?

## Expressions and `if:` Notes

| Concern | Example |
|--------|---------|
| branch check | `github.ref == 'refs/heads/main'` |
| event check | `github.event_name == 'pull_request'` |
| previous job output | `needs.build.outputs.version` |
| step success/failure | `success()`, `failure()`, `cancelled()` |

Expressions are the sharp edge of Actions syntax — subtle quoting and context mistakes are common.

## Context Quick Reference

| Context | Use |
|--------|-----|
| `github` | event metadata, refs, actor |
| `env` | environment vars |
| `secrets` | secret values |
| `matrix` | matrix-expanded values |
| `needs` | upstream job outputs/results |
| `steps` | prior step outputs |

## Reusable Workflows vs Composite Actions

| Need | Better fit |
|-----|-------------|
| reuse whole job/workflow logic | reusable workflow |
| reuse a repeated step sequence | composite action |

Use the smallest reusable abstraction that matches the duplication.

## Artifact and Output Patterns

| Need | Pattern |
|-----|---------|
| pass files between jobs | artifact upload/download |
| pass small values between jobs | job outputs |
| keep build products for debugging | artifact retention |

## Secrets and Env Heuristics

| Rule | Why |
|-----|-----|
| use `secrets.*` only where needed | limit exposure |
| prefer workflow/job env for repeated constants | reduce repetition |
| keep secret names stable across repos/envs where practical | easier maintenance |

## Common Syntax Smells

| Smell | Why it matters |
|------|----------------|
| giant single workflow with many unrelated concerns | poor reuse and readability |
| duplicated setup blocks across jobs | missing reusable abstraction |
| no explicit permissions | accidental over-privilege |

## Minimal Snippets by Need

| Need | Snippet idea |
|-----|--------------|
| run on PR only | `on: pull_request` |
| deploy after build | `needs: build` |
| matrix Node versions | `strategy.matrix.node` |
| skip unless path changed | `paths:` filter or `if:` logic |

## Review Questions

1. Is the workflow triggered by the exact events we intend?
2. Are jobs separated cleanly by purpose?
3. Could this be clearer as a reusable workflow or composite action?
4. Are expressions and contexts explicit enough to avoid syntax traps?

## Permissions and Security

| Concern | Pattern |
|--------|---------|
| restrict token scope | `permissions:` |
| job-specific permission | set under the job |
| no write access needed | read-only permissions |

Actions security starts with not giving `GITHUB_TOKEN` more than the workflow needs.

## Concurrency and Cancellation

| Need | Syntax |
|-----|--------|
| one deploy at a time | `concurrency:` group |
| cancel superseded runs | `cancel-in-progress: true` |

Concurrency is often the missing piece in clean deployment workflows.

## Reusable Workflow Inputs and Secrets

| Concern | Syntax |
|--------|--------|
| declare inputs | `on.workflow_call.inputs` |
| declare secrets | `on.workflow_call.secrets` |
| pass inputs | `with:` |
| pass secrets | `secrets:` |

## Artifact Review Questions

1. Should this data be an artifact or a job output?
2. How long does the artifact need to live?
3. Is this artifact necessary or just leftover debugging noise?

## Release Workflow Heuristics

| Need | Pattern |
|-----|---------|
| build → test → deploy | separate jobs with `needs` |
| environment approval | `environment:` gated deploy |
| reusable deploy logic | reusable workflow |

## Common CI/CD Smells

| Smell | Why it matters |
|------|----------------|
| every step inline in one mega-job | hard maintenance |
| no permissions block | weak security posture |
| duplicated deploy logic across repos | missed reuse opportunity |

## Final Cheat-Sheet Questions

1. Can a user reconstruct a valid workflow from this page quickly?
2. Are the highest-friction syntax areas easy to find?
3. Are reusable workflows, permissions, and conditionals represented clearly?

## Common Actions Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| expressions quoted wrong | syntax confusion | keep `${{ }}` precise |
| giant workflows without reuse | duplication | reusable workflow/composite action |
| no matrix where clearly needed | duplicated jobs | use matrix |

## Final Actions Checklist

- [ ] workflow shape is easy to reconstruct quickly
- [ ] trigger, job, matrix, and expression syntax are easy to find
- [ ] reusable workflow and artifact patterns are included
- [ ] snippets are minimal and copyable

## Workflow Review Questions

1. Can someone reconstruct a working CI file from this cheat sheet fast?
2. Are the risky syntax areas — expressions, matrices, permissions, reuse — easy to find?
3. Would this be enough under pressure during a broken CI incident?
