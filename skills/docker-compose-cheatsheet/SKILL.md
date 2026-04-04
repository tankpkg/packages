---
name: "@tank/docker-compose-cheatsheet"
description: |
  Fast Docker Compose command and YAML reference for daily development and
  operations. Covers `docker compose` lifecycle commands, compose file service
  syntax, environment variables, volumes, networks, profiles, healthchecks,
  build vs image, dependency patterns, and common local-dev workflows.

  Synthesizes Docker Compose official documentation, Compose file reference,
  and practical container orchestration patterns for local and CI environments.

  Trigger phrases: "docker compose", "docker compose cheat sheet",
  "docker compose commands", "docker compose yaml", "docker compose build",
  "docker compose up", "docker compose down", "compose healthcheck"
---

# Docker Compose Cheat Sheet

## Core Philosophy

1. **Optimize for local workflows** — Compose is most valuable when it shortens the path to a working multi-service environment.
2. **Keep service definitions readable** — A cheat sheet should surface the fields engineers reach for most often.
3. **Separate lifecycle commands from YAML syntax** — Operators and authors need both, but not mixed chaotically.
4. **Prefer explicit dependencies and healthchecks** — Most Compose confusion comes from startup timing and hidden environment coupling.
5. **Profiles and overrides are leverage** — They keep one Compose setup usable across dev, test, and optional services.

## Quick-Start: Common Problems

### "How do I start or rebuild everything?"

1. `docker compose up -d`
2. `docker compose up --build`
3. `docker compose down`
-> See `references/commands-and-yaml.md`

### "How do I inspect logs or enter a service?"

| Need | Command |
|------|---------|
| logs | `docker compose logs -f <service>` |
| shell | `docker compose exec <service> sh` |
| one-off command | `docker compose run --rm <service> <cmd>` |
-> See `references/commands-and-yaml.md`

## Decision Trees

| Signal | Focus area |
|--------|------------|
| need lifecycle control | `up`, `down`, `ps`, `logs`, `exec` |
| need service definition help | service fields, env, volumes, networks |
| need optional services | profiles |
| need startup ordering | `depends_on` + healthchecks |

## Reference Index

| File | Contents |
|------|----------|
| `references/commands-and-yaml.md` | Docker Compose commands, core YAML fields, service patterns, healthchecks, networks, volumes, profiles, and common dev workflows |
