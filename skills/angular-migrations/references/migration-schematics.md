# Angular Migration Schematics Reference

Sources: angular.dev/reference/migrations, Angular Blog (signal-input-migrations), Angular GitHub angular/angular, ngxtension documentation

Covers: all 14 official Angular migration schematics with commands, behavior, flags, limitations, and recommended execution order.

## Complete Schematics List

| # | Schematic | Introduced | Purpose |
|---|-----------|-----------|---------|
| 1 | `standalone` | v15.2 | Convert NgModule components to standalone |
| 2 | `control-flow` | v17 | Convert `*ngIf/*ngFor/*ngSwitch` to `@if/@for/@switch` |
| 3 | `inject` | v19 | Convert constructor injection to `inject()` |
| 4 | `route-lazy-loading` | v19 | Convert eager routes to lazy-loaded |
| 5 | `signal-input-migration` | v19 | Convert `@Input()` to `input()` |
| 6 | `output-migration` | v19 | Convert `@Output()` to `output()` |
| 7 | `signal-queries-migration` | v19 | Convert `@ViewChild` etc. to signal queries |
| 8 | `cleanup-unused-imports` | v19 | Remove unused standalone imports |
| 9 | `self-closing-tags` | v20 | Convert `<comp></comp>` to `<comp />` |
| 10 | `ngclass-to-class` | v21 | Convert `[ngClass]` to `[class]` bindings |
| 11 | `ngstyle-to-style` | v21 | Convert `[ngStyle]` to `[style]` bindings |
| 12 | `router-testing-module-migration` | v21 | Convert `RouterTestingModule` to `RouterModule` |
| 13 | `common-to-standalone` | v21 | Replace `CommonModule` with individual imports |
| 14 | `refactor-jasmine-vitest` | v21 | Convert Jasmine tests to Vitest |

## Recommended Execution Order

Run schematics in this order after each version upgrade. Each builds
on the previous — standalone first because signal migrations work
best with standalone components.

```bash
# 1. Module structure
ng generate @angular/core:standalone
ng generate @angular/core:common-to-standalone

# 2. Template syntax
ng generate @angular/core:control-flow
ng generate @angular/core:self-closing-tags
ng generate @angular/core:ngclass-to-class
ng generate @angular/core:ngstyle-to-style

# 3. Component API
ng generate @angular/core:inject
ng generate @angular/core:signal-input-migration
ng generate @angular/core:output-migration
ng generate @angular/core:signal-queries-migration

# 4. Routing
ng generate @angular/core:route-lazy-loading

# 5. Cleanup
ng generate @angular/core:cleanup-unused-imports

# 6. Testing (v21+)
ng generate @angular/core:router-testing-module-migration
ng g @schematics/angular:refactor-jasmine-vitest
```

## Schematic 1: Standalone Migration

```bash
ng generate @angular/core:standalone
```

### What It Does

1. Converts components/directives/pipes to standalone
2. Adds required imports to each standalone entity
3. Updates NgModule declarations/imports/exports
4. Can optionally remove empty NgModules

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--path` | Project root | Target specific directory |
| `--mode` | `convert-to-standalone` | One of: `convert-to-standalone`, `prune-modules`, `standalone-bootstrap` |

### Modes

- `convert-to-standalone` — Converts declarations to standalone, adds imports
- `prune-modules` — Removes NgModules that are no longer needed
- `standalone-bootstrap` — Converts app bootstrap from NgModule to standalone

Run in order: convert → prune → bootstrap.

### Limitations

- Cannot handle dynamic module loading patterns
- May miss imports if modules re-export from other modules
- Complex circular dependencies may need manual resolution

## Schematic 2: Control Flow Migration

```bash
ng generate @angular/core:control-flow
```

### What It Does

Converts structural directives to built-in control flow:

| Before | After |
|--------|-------|
| `*ngIf="condition"` | `@if (condition) { ... }` |
| `*ngIf="x; else tpl"` | `@if (x) { ... } @else { ... }` |
| `*ngFor="let item of items; trackBy: trackFn"` | `@for (item of items; track item.id) { ... }` |
| `*ngSwitch / *ngSwitchCase` | `@switch / @case` |

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--path` | Project root | Target specific directory |
| `--format` | N/A | Code formatting |

### Important: `@for` Requires `track`

The `track` expression is mandatory in `@for`. The schematic converts
`trackBy` functions but may need manual adjustment:

```html
<!-- Schematic output — verify track expression -->
@for (item of items; track item.id) {
  <div>{{ item.name }}</div>
} @empty {
  <div>No items</div>
}
```

### `@empty` Block

`@for` supports `@empty` for empty collections — this is new
functionality not available with `*ngFor`. The schematic does NOT
add `@empty` blocks (it only converts existing code).

## Schematic 3: inject() Migration

```bash
ng generate @angular/core:inject
```

### What It Does

Converts constructor-based dependency injection to the `inject()` function:

```typescript
// Before
constructor(private http: HttpClient, @Optional() private logger: Logger) {}

// After
private http = inject(HttpClient);
private logger = inject(Logger, { optional: true });
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--path` | Project root | Target specific directory |

### Limitations

- Cannot convert constructors with complex logic beyond DI
- Constructor parameters used in `super()` calls need manual handling
- Some decorator combinations may not convert cleanly

## Schematic 4: Route Lazy Loading

```bash
ng generate @angular/core:route-lazy-loading
```

### What It Does

Converts eagerly loaded component routes to lazy-loaded ones:

```typescript
// Before
{ path: 'users', component: UsersComponent }

// After
{ path: 'users', loadComponent: () => import('./users').then(m => m.UsersComponent) }
```

### Limitations

- Only converts component routes (not module routes)
- Cannot determine if lazy loading is appropriate for all routes
- Guard and resolver imports may need manual adjustment

## Schematic 5: Signal Input Migration

```bash
ng generate @angular/core:signal-input-migration
```

### What It Does

1. Converts `@Input()` declarations to `input()` / `input.required()`
2. Updates template references (adds `()` for reads)
3. Updates host binding references
4. Preserves types, defaults, aliases, transforms

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--path` | Project root | Target specific directory |
| `--best-effort-mode` | false | Continue despite partial failures |
| `--insert-todos` | false | Add TODO comments for manual fixes |
| `--analysis-dir` | N/A | Save analysis results |

### VSCode Integration

The migration is also available as a code refactor action in VSCode.
Install the latest Angular Language Service extension and click
the lightbulb on `@Input()` decorators.

### Known Limitations

- Inputs accessed via string-based APIs (like `@HostListener` arguments)
  may not be migrated
- Inputs used in `ngOnChanges` need manual conversion (signals don't
  trigger `ngOnChanges`)
- Type narrowing in templates may need `!` operator

## Schematic 6: Output Migration

```bash
ng generate @angular/core:output-migration
```

### What It Does

Converts `@Output() + EventEmitter` to `output()`:

```typescript
// Before
@Output() clicked = new EventEmitter<void>();

// After
clicked = output<void>();
```

### Limitations

- Outputs subscribed to with `.subscribe()` need manual migration
  (anti-pattern, but exists in some codebases)
- Complex EventEmitter subclasses may not convert

## Schematic 7: Signal Queries Migration

```bash
ng generate @angular/core:signal-queries-migration
```

### What It Does

Converts decorator-based queries to signal queries:

```typescript
// Before
@ViewChild('ref') ref!: ElementRef;
@ViewChildren(MyComp) comps!: QueryList<MyComp>;

// After
ref = viewChild.required<ElementRef>('ref');
comps = viewChildren(MyComp);
```

### Limitations

- `QueryList`-specific APIs (`.changes`, `.toArray()`, `.first`, `.last`)
  need manual conversion — signal queries return `Signal<readonly T[]>`
- Code using `ngAfterViewInit` to access queries may need refactoring

## Schematic 8: Cleanup Unused Imports

```bash
ng generate @angular/core:cleanup-unused-imports
```

### What It Does

Removes unused imports from standalone component `imports` arrays.
Also removes unused TypeScript imports.

## Schematic 9: Self-Closing Tags

```bash
ng generate @angular/core:self-closing-tags
```

### What It Does

Converts component tags with no content to self-closing:

```html
<!-- Before -->
<app-header></app-header>

<!-- After -->
<app-header />
```

## Schematics 10-11: NgClass/NgStyle to Bindings

```bash
ng generate @angular/core:ngclass-to-class
ng generate @angular/core:ngstyle-to-style
```

### What They Do

Convert directive-based class/style bindings to native bindings:

```html
<!-- Before -->
<div [ngClass]="{'active': isActive}">
<div [ngStyle]="{'color': textColor}">

<!-- After -->
<div [class.active]="isActive">
<div [style.color]="textColor">
```

Reduces dependency on `CommonModule`.

## Schematic 12: RouterTestingModule Migration

```bash
ng generate @angular/core:router-testing-module-migration
```

### What It Does

Converts `RouterTestingModule` to `RouterModule` + `provideLocationMocks()`:

```typescript
// Before
TestBed.configureTestingModule({
  imports: [RouterTestingModule.withRoutes(routes)]
});

// After
TestBed.configureTestingModule({
  imports: [RouterModule.forRoot(routes)],
  providers: [provideLocationMocks()]
});
```

## Schematic 13: CommonModule to Standalone

```bash
ng generate @angular/core:common-to-standalone
```

### What It Does

Replaces `CommonModule` import with individual directive/pipe imports:

```typescript
// Before
@Component({
  imports: [CommonModule]
})

// After
@Component({
  imports: [NgIf, NgFor, AsyncPipe]  // only what's used
})
```

Best combined with control-flow migration — after converting `*ngIf` to
`@if`, the `NgIf` import is no longer needed.

## Schematic 14: Jasmine to Vitest

```bash
ng g @schematics/angular:refactor-jasmine-vitest
```

Note: This uses `@schematics/angular`, not `@angular/core`.

### What It Does

- Converts Jasmine test syntax to Vitest equivalents
- Updates imports (`describe`, `it`, `expect` from `vitest`)
- Converts Jasmine matchers to Vitest matchers

### Limitations

- Custom Jasmine matchers need manual conversion
- `done()` callback patterns may need manual conversion
- Jasmine spies → Vitest spies syntax differs

## Third-Party Migration Tools

### ngxtension

Community schematics that complement official ones:

```bash
npx ng add ngxtension

# Signal inputs (alternative to official)
npx ng g ngxtension:convert-signal-inputs

# Signal outputs (alternative to official)
npx ng g ngxtension:convert-outputs

# Per-file targeting
npx ng g ngxtension:convert-signal-inputs --path=libs/feature-xyz/my-comp.ts
```

### Nx Migrate

For Nx workspaces, use `nx migrate` instead of `ng update`:

```bash
nx migrate @angular/core@21
nx migrate --run-migrations
```

Nx handles workspace-level concerns and runs Angular schematics
automatically during migration.
