# Commands and YAML

Sources: Docker Compose official documentation, Compose file reference, Docker CLI documentation, common local-dev Compose workflows

Covers: `docker compose` commands, compose YAML structure, service definitions, build vs image, networks, volumes, profiles, healthchecks, environment handling, and common dev workflows.

## Core Lifecycle Commands

| Task | Command |
|-----|---------|
| start services | `docker compose up` |
| start detached | `docker compose up -d` |
| rebuild and start | `docker compose up --build` |
| stop and remove | `docker compose down` |
| stop without removing | `docker compose stop` |
| list running services | `docker compose ps` |

## Logs and Exec

| Task | Command |
|-----|---------|
| view logs | `docker compose logs` |
| follow logs | `docker compose logs -f <service>` |
| shell into service | `docker compose exec <service> sh` |
| one-off command | `docker compose run --rm <service> <cmd>` |

## Core YAML Structure

| Top-level key | Use |
|--------------|-----|
| `services` | container definitions |
| `volumes` | named volumes |
| `networks` | custom networks |
| `configs` / `secrets` | advanced shared config where supported |

## Service Definition Basics

| Field | Use |
|------|-----|
| `image` | use prebuilt image |
| `build` | build from Dockerfile/context |
| `ports` | host:container port mapping |
| `environment` | env vars |
| `volumes` | bind mounts or named volumes |
| `depends_on` | startup dependency hints |
| `healthcheck` | readiness/health probing |

## Build vs Image

| Use `build` when | Use `image` when |
|------------------|------------------|
| you are iterating on local code | you consume a published image |
| Dockerfile defines app build | image already exists in registry |

## Environment Patterns

| Pattern | Example |
|--------|---------|
| inline env vars | `environment: ["DEBUG=true"]` |
| map style env vars | `environment: { DEBUG: "true" }` |
| env file | `env_file: .env` |

## Volumes and Networks

| Need | Pattern |
|-----|---------|
| persist DB data | named volume |
| mount source code | bind mount |
| isolate service communication | custom network |

## Healthchecks and Dependencies

Use healthchecks when startup order truly matters.

| Concern | Recommendation |
|--------|----------------|
| app needs DB ready | add DB healthcheck and dependency awareness |
| optional service | use profile |
| long startup | tune interval/retries carefully |

## Profiles

Profiles keep optional services out of the default path.

| Use case | Example |
|---------|---------|
| optional admin UI | `profiles: ["debug"]` |
| local-only support service | profiling, mailhog, tracing |

Profiles are the easiest way to keep one Compose setup useful without forcing every engineer to boot every service every time.

## Restart and Cleanup Commands

| Task | Command |
|-----|---------|
| restart one service | `docker compose restart <service>` |
| remove stopped containers and networks | `docker compose down` |
| remove volumes too | `docker compose down -v` |
| remove orphan containers | `docker compose down --remove-orphans` |

Cleanup flags matter because persistent state and orphaned containers often explain “weird local issues.”

## Build and Image Workflow

| Need | Pattern |
|-----|---------|
| local code iteration | `build:` + bind mount |
| stable shared dependency image | `image:` |
| force rebuild | `docker compose build --no-cache` |

### Build review questions

1. Should this service rebuild from local source or consume a published image?
2. Are Dockerfile changes part of the dev workflow or only CI?
3. Is build time becoming a bottleneck that profiles or prebuilt images could reduce?

## Port Mapping Notes

| Pattern | Meaning |
|--------|---------|
| `8080:80` | host port 8080 to container port 80 |
| `127.0.0.1:5432:5432` | bind to localhost only |
| `"80"` without host mapping | expose only inside Compose network |

Be explicit when you do or do not want host access.

## Dependency and Healthcheck Discipline

`depends_on` helps start ordering, but real readiness still belongs to healthchecks or application retry logic.

| Concern | Better pattern |
|--------|----------------|
| app needs DB listening | DB healthcheck + app retry |
| app needs migration complete | explicit migration service or startup script |
| optional support service | profile it out when not needed |

## Healthcheck Patterns

| Service type | Example check |
|-------------|---------------|
| HTTP app | `curl -f http://localhost:3000/health` |
| database | native readiness command or lightweight query |
| queue/cache | service-specific ping |

### Healthcheck review questions

1. Does this check reflect usable readiness or just process existence?
2. Will the interval and retries make local startup annoying?
3. Is a healthcheck overkill for this service?

## Volume Strategy

| Pattern | Use |
|--------|-----|
| bind mount | live local code editing |
| named volume | persistent service state |
| anonymous volume | throwaway data |

### Volume review heuristics

| Question | Why |
|---------|-----|
| should data survive `down`? | persistence choice |
| should code changes reflect instantly? | bind mount decision |
| is state reset a common troubleshooting step? | cleanup ergonomics |

## Network Strategy

Compose creates a default network, but explicit networks help when segmentation matters.

| Need | Pattern |
|-----|---------|
| all services can talk freely | default network |
| isolate app and data planes | custom networks |
| external shared network | `external: true` network |

## Environment Variable Questions

1. Which variables belong in `.env`, service `environment`, or `env_file`?
2. Which values are local-only versus shared across the team?
3. Are secrets leaking into committed files by accident?

## Compose File Smells

| Smell | Why it matters |
|------|----------------|
| giant monolithic service definitions | poor readability |
| too many environment-specific hacks in one file | drift and confusion |
| hidden startup dependencies | fragile local boots |

## Common Dev Workflows Expanded

| Goal | Flow |
|-----|------|
| start clean | `docker compose down -v` → `docker compose up --build` |
| inspect failing service | `logs -f` → `exec` |
| run migration/test task | `docker compose run --rm <service> <cmd>` |

## CI/Automation Questions

| Question | Why |
|---------|-----|
| is Compose only for local dev or also CI? | config scope |
| do we need profiles to trim CI startup? | speed |
| should one-off commands run via `run --rm`? | cleaner automation |

## Final Compose Notes

Compose stays valuable when the file documents the real multi-service workflow clearly enough that a new engineer can boot, inspect, and reset the stack without asking for help.

That is what makes it a force multiplier instead of just another YAML file.

Readable orchestration is operational leverage.

## Quick Sanity Questions

1. Can a new engineer start the stack with one obvious command?
2. Can they inspect logs and get a shell without guessing?
3. Can they reset state safely when local data gets weird?

Those are the real usability tests for a Compose setup.

If they fail, the file needs simplification.

## Common Compose Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| assuming `depends_on` means app-level readiness | startup race | add healthcheck/readiness handling |
| using bind mounts where persistence is needed | data loss/confusion | use named volume |
| one giant compose file for every environment | drift and clutter | use profiles/overrides intentionally |

## Common Dev Flows

1. `docker compose up -d`
2. `docker compose logs -f <service>`
3. `docker compose exec <service> sh`
4. `docker compose down`

## Review Questions

1. Is this Compose file for local dev, CI, or production-adjacent use?
2. Are service dependencies explicit enough to avoid timing confusion?
3. Are volumes, env vars, and ports documenting the system clearly?

## Final Compose Checklist

- [ ] commands for start, logs, exec, and teardown are obvious
- [ ] service definitions emphasize the most-used keys
- [ ] healthchecks, profiles, volumes, and networks are used intentionally
- [ ] the file stays readable for day-to-day engineering use
