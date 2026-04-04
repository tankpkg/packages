# APIs and HTMX

Sources: Django REST Framework documentation, Django Ninja documentation, HTMX documentation, Django official docs, community API and progressive enhancement guidance

Covers: DRF serializers and viewsets, permissions, Django Ninja, HTMX integration, mixed server-rendered/API architectures, and pragmatic boundary choices.

## Pick the Simplest Surface That Fits

| Need | Tool |
|-----|------|
| browser-first app with progressive enhancement | HTMX + Django views |
| full-featured REST API | DRF |
| lighter typed API surface | Django Ninja |
| mixed HTML + API app | explicit separation of routes and contracts |

## DRF Basics

| Concern | Tool |
|--------|------|
| request/response serialization | serializers |
| auth and authorization | authentication + permission classes |
| CRUD resources | viewsets / generic views |
| pagination/filtering | DRF pagination + filter backends |

Use DRF when you need an opinionated API framework, not just raw JSON responses.

## Serializer Rules

1. Keep serializer shape explicit
2. Avoid hidden ORM explosions from nested serializers without eager loading
3. Use read/write separation where it clarifies API contracts

## ViewSet Trade-offs

| Benefit | Cost |
|--------|------|
| rapid CRUD generation | can hide route behavior |
| router integration | less explicit than hand-written views |

Use viewsets when the resource shape is conventional. Drop down to APIView/generics when custom behavior dominates.

## Django Ninja

Django Ninja is a good fit when you want typed request/response contracts with less framework ceremony than DRF.

| Good fit | Example |
|---------|---------|
| internal APIs | lean typed endpoints |
| teams familiar with FastAPI-style schemas | easier onboarding |

## HTMX Patterns

| Good HTMX use case | Why |
|-------------------|-----|
| partial updates in server-rendered apps | minimal JS burden |
| inline create/edit/delete flows | clean HTML-first UX |
| search/filter fragments | fast progressive enhancement |

HTMX is strong when you want interactivity without inventing a SPA for no reason.

## Mixed Architecture Rules

| Concern | Recommendation |
|--------|----------------|
| shared domain logic | keep below transport layer |
| HTML and API routes | separate clearly |
| auth semantics | avoid mixing browser session assumptions into API design |

## DRF View Layer Choices

| Need | Tool |
|-----|------|
| one-off custom endpoint | APIView |
| common CRUD with light customization | generic views |
| resource-heavy standard API | viewsets + routers |

Choose the least abstract layer that still reduces repetition.

## Serializer Design Questions

1. Is this serializer for reads, writes, or both?
2. Will nested data cause hidden ORM work?
3. Should validation live here or deeper in domain logic?

## Permissions and Auth for APIs

| Concern | Pattern |
|--------|---------|
| authenticated-only API | DRF auth + permission classes |
| object-level permission | explicit permission classes or view checks |
| mixed browser and API auth | separate semantics by route surface |

## HTMX Endpoint Design

| Pattern | Why |
|--------|-----|
| return fragment template only | smaller responses |
| keep form validation server-side | progressive enhancement remains correct |
| pair with standard Django forms | simple correctness model |

## DRF Performance Questions

1. Are serializers causing relation explosions?
2. Is pagination explicit?
3. Are filters/orderings constrained intentionally?

## Django Ninja Trade-offs

| Benefit | Cost |
|--------|------|
| lighter typed API surface | smaller ecosystem than DRF |
| FastAPI-like feel | fewer batteries than DRF |

## HTMX vs Full API Review

| If the consumer is... | Prefer |
|----------------------|--------|
| your own server-rendered HTML | HTMX |
| multiple external clients | API |
| mixed but still browser-first | HTMX + selective API |

## Common API Shape Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| serializer field sprawl | unstable contracts | tighten explicit fields |
| treating HTMX as a SPA clone | unnecessary complexity | stay fragment-oriented |
| mixing API and template assumptions in one endpoint | maintenance confusion | split surfaces |

## Testing Questions for APIs/HTMX

1. Are response shapes asserted explicitly?
2. Are auth and permission failures tested?
3. Do HTMX endpoints return the minimal fragment required?

## Common API/HTMX Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| nested serializers without eager loading | huge query counts | shape queries first |
| API and HTML route responsibilities blurred | maintenance confusion | separate route surfaces |
| HTMX endpoints returning too much page shell | waste and coupling | return focused fragments |

## Serializer Boundary Questions

1. Is this serializer exposing too much model detail?
2. Are write-only and read-only concerns separated where that clarifies contracts?
3. Does nested data require explicit eager loading?

## DRF ViewSet Review

| Smell | Why it matters |
|------|----------------|
| too many custom actions on one viewset | resource boundary may be wrong |
| hidden queryset changes per action | hard reasoning |
| serializer switching with no clarity | weak contract visibility |

## HTMX Review Questions

1. Is this interaction better served by a fragment than a full SPA flow?
2. Does the endpoint return only what the browser needs to swap?
3. Is server-side validation and redirect/error behavior still correct without JS?

## API Filtering and Pagination

| Concern | Recommendation |
|--------|----------------|
| unbounded list endpoints | paginate explicitly |
| arbitrary ordering/filtering | constrain supported fields |
| expensive nested representations | shape and limit payloads |

## Mixed App/API Architecture Smells

| Smell | Problem |
|------|---------|
| one route trying to serve HTML and JSON equally | blurred responsibilities |
| browser session assumptions leaking into public API | auth confusion |
| API serializers directly reused as template data model | weak separation |

## Practical Surface Selection Questions

1. Who consumes this endpoint: browser-only, many clients, or both?
2. Is progressive enhancement enough, or is a true API surface required?
3. Does the auth model differ from the main server-rendered app?

## DRF Serializer Split Patterns

| Pattern | Use |
|--------|-----|
| one serializer for everything | simple resources only |
| separate read/write serializers | clearer complex APIs |
| nested read, flat write | common practical compromise |

## API Pagination and Filtering Discipline

| Concern | Recommendation |
|--------|----------------|
| public list endpoints | always paginate |
| filtering | whitelist supported filters |
| ordering | constrain to safe/indexed fields |

## HTMX Form Flow Notes

| Pattern | Benefit |
|--------|---------|
| server-side validated form fragment re-render | simple correctness |
| partial row/card replacement | minimal UI churn |
| progressive enhancement without SPA state complexity | maintainable UX |

## Ninja vs DRF Questions

1. Do you need DRF’s ecosystem and generic resource tooling?
2. Would typed request/response schemas with lighter ceremony be enough?
3. Are you serving many external consumers or mostly internal clients?

## Mixed Architecture Review

| Smell | Why it matters |
|------|----------------|
| same model/serializer assumptions reused everywhere | weak surface boundaries |
| API auth and session auth conflated | security confusion |
| HTMX and SPA-like JSON flows mixed randomly | maintenance drag |

## Final API/HTMX Checklist

- [ ] API surface and HTML/HTMX surface are intentionally separated
- [ ] serializer shape and query loading align
- [ ] pagination/filtering are constrained and explicit
- [ ] HTMX endpoints stay fragment-focused and server-validating

Keeping these boundaries clear prevents the app from becoming half-SPA, half-server soup.

Clean boundaries also make auth and caching decisions easier to reason about.

They also make scaling the codebase less painful.

## Release Readiness Checklist

- [ ] DRF or Ninja choice matches actual API needs
- [ ] serializer shape is explicit and query-safe
- [ ] HTMX routes return focused fragments and keep progressive enhancement intact
- [ ] mixed HTML/API apps keep boundaries clean and auth semantics explicit
- [ ] permission and pagination behavior are tested where relevant

## Release Readiness Checklist

- [ ] DRF or Ninja choice matches actual API needs
- [ ] serializer shape is explicit and query-safe
- [ ] HTMX routes return focused fragments and keep progressive enhancement intact
- [ ] mixed HTML/API apps keep boundaries clean and auth semantics explicit
