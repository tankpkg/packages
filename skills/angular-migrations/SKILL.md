---
name: "@tank/angular-migrations"
description: |
  Expert Angular migration guidance for version upgrades from v18 through v21.
  Covers every migration path (v18 to v19, v19 to v20, v20 to v21), breaking changes,
  official migration schematics, signals adoption, zoneless transition, and
  build/test tooling changes. Provides step-by-step upgrade procedures,
  compatibility matrices, automated schematic commands, and strategies for
  large-scale enterprise migrations. Synthesizes official Angular blog posts,
  angular.dev documentation, update.angular.dev guides, and community migration
  patterns.

  Trigger phrases: "angular migration", "angular upgrade", "ng update",
  "angular 18", "angular 19", "angular 20", "angular 21", "upgrade angular",
  "migrate angular", "angular breaking changes", "angular version upgrade",
  "angular standalone migration", "angular signals migration",
  "angular zoneless", "zone.js removal", "karma to vitest",
  "angular control flow migration", "ng generate migration",
  "angular update guide", "angular compatibility", "angular deprecation"
---
# Angular Migrations (v18 through v21)

## Core Philosophy

- Upgrade one major version at a time — skipping versions risks missing migration schematics and accumulating unresolved breaking changes.
- Run official schematics before manual fixes — Angular provides automated migrations for most breaking changes; manual work is the last resort.
- Signals, standalone, and zoneless are the destination — every migration should move closer to the modern Angular paradigm, not just fix compilation errors.
- Test at every step — run `ng build`, `ng test`, and e2e after each version bump before proceeding.
- Treat migration as architecture, not syntax — version upgrades after v18 are architectural shifts (reactivity model, change detection, module system), not just API renames.

## Quick-Start: Which Migration?

| Starting Version | Target | Key Theme | Reference |
|-----------------|--------|-----------|-----------|
| v18 | v19 | Standalone default, signals stable | `references/v18-to-v19.md` |
| v19 | v20 | Build system change, Karma removed | `references/v19-to-v20.md` |
| v20 | v21 | Zoneless default, Vitest, Signal Forms | `references/v20-to-v21.md` |
| Any | Signals | Decorator→signal function migration | `references/signals-migration.md` |
| Any | Zoneless | Zone.js removal strategy | `references/zoneless-migration.md` |

## Version Compatibility Matrix

| Angular | TypeScript | Node.js | RxJS | Zone.js |
|---------|-----------|---------|------|---------|
| v18 | 5.4 | >=18.19.1 | 6.x / 7.x | Required |
| v19 | 5.6 | >=18.19.1 | 6.x / 7.x | Required (default) |
| v20 | 5.8 | >=20.11.1 | 7.x / 8.x | Optional (stable zoneless) |
| v21 | 5.8+ | >=20.11.1 | 7.x / 8.x | Not included by default |

## Universal Upgrade Procedure

For each major version jump:

1. Create a branch: `git checkout -b upgrade/angular-{target}`
2. Ensure current tests pass: `ng build && ng test`
3. Update Angular: `ng update @angular/cli@{target} @angular/core@{target}`
4. If using Angular Material: `ng update @angular/material@{target}`
5. Run migration schematics (see reference for each version)
6. Fix remaining compiler/type errors manually
7. Run full test suite: `ng build --configuration production && ng test`
8. Review deprecation warnings and address them

## Recommended Schematic Order

Run these schematics after each version upgrade in this order — each
builds on the previous:

```
1. ng generate @angular/core:standalone
2. ng generate @angular/core:control-flow
3. ng generate @angular/core:inject
4. ng generate @angular/core:signal-input-migration
5. ng generate @angular/core:output-migration
6. ng generate @angular/core:signal-queries-migration
7. ng generate @angular/core:route-lazy-loading
8. ng generate @angular/core:cleanup-unused-imports
9. ng generate @angular/core:self-closing-tags
10. ng generate @angular/core:common-to-standalone
```

Not all schematics exist in all versions. Run what's available.
See `references/migration-schematics.md` for details on each.

## Common Migration Problems

| Problem | Version | Cause | Fix |
|---------|---------|-------|-----|
| `ng test` fails after upgrade | v20+ | Karma removed from `@angular/build` | Install `@angular-devkit/build-angular` or migrate to Vitest |
| Zoneless + Zone.js warning (NG0914) | v21 | Zone.js still in polyfills | Remove `zone.js` from `angular.json` polyfills |
| `effect()` outside injection context | v19+ | Called outside constructor/DI | Move to constructor or field initializer |
| Signal input type mismatch | v19+ | `input()` returns `InputSignal<T>` | Append `()` to read: `this.name()` not `this.name` |
| Third-party lib expects Zone.js | v21 | Library uses zone-patched async | Use `provideZoneChangeDetection()` as fallback |
| SSR hydration mismatch | v19+ | DOM differs between server/client | Use `@defer (hydrate on ...)` or fix deterministic rendering |
| Template type narrowing breaks | v19+ | Signal inputs in `@if` blocks | Add `!` to signal calls inside narrowed blocks |

## Multi-Version Jump Strategy

Jumping from v18 to v21 requires three sequential upgrades.
Do not skip versions.

```
v18 → v19 (standalone + signals stable)
     → v20 (build system + testing)
          → v21 (zoneless + signal forms)
```

At each step: upgrade → run schematics → fix errors → test → commit → next.

## Signals Adoption Roadmap

| What to Migrate | From | To | Schematic |
|----------------|------|----|-----------|
| Component inputs | `@Input()` | `input()` / `input.required()` | `signal-input-migration` |
| Component outputs | `@Output() + EventEmitter` | `output()` | `output-migration` |
| View/content queries | `@ViewChild()` / `@ContentChildren()` | `viewChild()` / `contentChildren()` | `signal-queries-migration` |
| Two-way binding | `@Input() + @Output()` | `model()` | Manual |
| Constructor DI | `constructor(private svc: Svc)` | `svc = inject(Svc)` | `inject` |
| UI state | `BehaviorSubject` | `signal()` / `computed()` | Manual |
| Async data | `subscribe()` patterns | `resource()` / `rxResource()` | Manual |

For detailed migration patterns, see `references/signals-migration.md`.

## Angular Material Considerations

Angular Material follows the same major versioning. Always update together:

```bash
ng update @angular/cli@{ver} @angular/core@{ver} @angular/material@{ver}
```

Material-specific schematics run automatically during `ng update`.
Material v20+ adopts the M3 design system — visual regressions are possible.

## Reference Files

| File | Contents |
|------|----------|
| `references/v18-to-v19.md` | Complete v18→v19 migration: standalone default, signals stable, incremental hydration, TypeScript 5.6 |
| `references/v19-to-v20.md` | Complete v19→v20 migration: build system change, Karma removal, naming conventions, TypeScript 5.8 |
| `references/v20-to-v21.md` | Complete v20→v21 migration: zoneless default, Signal Forms, Angular Aria, Vitest stable |
| `references/signals-migration.md` | Signal adoption across versions: input/output/query migration, RxJS interop, patterns |
| `references/zoneless-migration.md` | Zone.js removal: compatibility checklist, OnPush, PendingTasks, testing, SSR |
| `references/migration-schematics.md` | All 14 official schematics: commands, flags, behavior, limitations |
| `references/testing-and-build-tooling.md` | Karma→Vitest migration, build system changes, Angular Material updates |
