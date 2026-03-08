# Testing and Build Tooling Migration

Sources: Angular Blog (announcing-angular-v21, meet-angular-v19), angular.dev/guide/testing, yeou.dev upgrade guide, AngularUX playbook, community Vitest migration guides

Covers: Karma to Vitest migration, build system changes (webpack to esbuild), Angular Material/CDK updates, HMR behavior, and monorepo/workspace considerations.

## Build System Evolution

| Version | Default Builder | Webpack Status | esbuild Status |
|---------|----------------|---------------|----------------|
| v15 | `@angular-devkit/build-angular` (webpack) | Primary | N/A |
| v16-v17 | `@angular-devkit/build-angular` | Primary | Opt-in (dev) |
| v18 | `@angular-devkit/build-angular` (application builder) | Available | Default |
| v19 | `@angular-devkit/build-angular` (application builder) | Deprecated | Default |
| v20 | `@angular/build` | Removed from default | Default (only option) |
| v21 | `@angular/build` | Removed | Default |

### Key Change: v20 Builder Package

In v20, the default build package changed from `@angular-devkit/build-angular`
to `@angular/build`. The new package:

- Uses esbuild for all builds (dev and prod)
- Uses Vite for dev server
- Does NOT include Karma support
- Faster builds (2-4x improvement reported)
- Better tree-shaking and smaller bundles

### Migration: Verify Builder in angular.json

```json
{
  "projects": {
    "my-app": {
      "architect": {
        "build": {
          "builder": "@angular/build:application"
        },
        "serve": {
          "builder": "@angular/build:dev-server"
        }
      }
    }
  }
}
```

If you see `@angular-devkit/build-angular:application`, the build works
the same — the package name change is the main difference.

### Custom Webpack Configuration

If your project uses custom webpack config (via `@angular-builders/custom-webpack`
or similar), you must either:

1. Port webpack customizations to esbuild plugins
2. Stay on `@angular-devkit/build-angular` (deprecated, limited lifespan)
3. Use Angular CLI's `--define` flag for simple substitutions

## Test Runner Evolution

| Version | Default Runner | Karma Status | Vitest Status |
|---------|---------------|-------------|---------------|
| v18 | Karma + Jasmine | Default | N/A |
| v19 | Karma + Jasmine | Default | Experimental |
| v20 | Karma (via bridge) | Removed from `@angular/build` | Experimental |
| v21 | Vitest | Not supported | Stable (default) |

## Karma to Vitest Migration

### Phase 1: Install Vitest (v20+)

The Angular CLI provides experimental Vitest support:

```bash
# If using @angular/build (v20+), Karma is gone
# Install the old builder as a bridge if needed:
npm install @angular-devkit/build-angular --save-dev
```

### Phase 2: Run Migration Schematic (v21+)

```bash
ng g @schematics/angular:refactor-jasmine-vitest
```

This converts Jasmine syntax to Vitest:

| Jasmine | Vitest |
|---------|--------|
| `describe()` | `describe()` (same) |
| `it()` | `it()` (same) |
| `beforeEach()` | `beforeEach()` (same) |
| `expect(x).toBe(y)` | `expect(x).toBe(y)` (same) |
| `expect(x).toEqual(y)` | `expect(x).toEqual(y)` (same) |
| `jasmine.createSpy()` | `vi.fn()` |
| `spyOn(obj, 'method')` | `vi.spyOn(obj, 'method')` |
| `jasmine.objectContaining()` | `expect.objectContaining()` |
| `jasmine.any(Number)` | `expect.any(Number)` |
| `done()` callback | `async/await` or return Promise |

### Phase 3: Update angular.json Test Target

```json
{
  "test": {
    "builder": "@angular/build:unit-test",
    "options": {
      "tsConfig": "tsconfig.spec.json",
      "runner": "vitest"
    }
  }
}
```

### Phase 4: Update Test Configuration

Create `vitest.config.ts` if custom configuration needed:

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.spec.ts'],
  },
});
```

### Phase 5: Fix Manual Conversion Items

The schematic doesn't handle everything:

| Pattern | Manual Fix Required |
|---------|-------------------|
| Custom Jasmine matchers | Rewrite as Vitest matchers or plugins |
| `done()` callback async | Convert to `async/await` |
| Jasmine clock | Use `vi.useFakeTimers()` |
| `jasmine.createSpyObj()` | Create object with `vi.fn()` methods |
| Karma-specific config | Remove karma.conf.js, add vitest config |
| Test harnesses | Verify Angular CDK test harnesses work |

### Common Vitest Migration Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `Cannot find module 'vitest'` | Vitest not installed | `npm install vitest --save-dev` |
| `ReferenceError: describe is not defined` | Globals not enabled | Add `globals: true` to vitest config |
| Angular DI fails in tests | TestBed not configured | Ensure `TestBed.configureTestingModule` runs in `beforeEach` |
| `HttpClientTestingModule` not found | Import changed | Use `provideHttpClientTesting()` |
| Slow test startup | Missing optimization | Ensure test target uses `@angular/build:unit-test` |

## Alternative: Karma Bridge (Temporary)

For teams not ready to migrate tests, keep Karma working in v20+:

```bash
npm install @angular-devkit/build-angular --save-dev
```

Update angular.json test target:

```json
{
  "test": {
    "builder": "@angular-devkit/build-angular:karma",
    "options": {
      "polyfills": ["zone.js", "zone.js/testing"],
      "tsConfig": "tsconfig.spec.json",
      "karmaConfig": "karma.conf.js"
    }
  }
}
```

This is a temporary bridge — plan for Vitest migration.

## Alternative: Jest Migration

Jest is also supported but not the official recommendation:

```bash
npm install jest @angular-builders/jest --save-dev
```

Angular's direction is clearly Vitest. Jest works but won't receive
first-party support.

## Hot Module Replacement (HMR)

### v19: HMR for Styles (New)

Enabled by default in dev server. CSS/SCSS changes apply without
full page reload — component state is preserved.

Implementation: Styles use `<link>` tags instead of inline `<style>`.

### v19: HMR for Templates (Experimental)

Template changes trigger component reload. Component state is NOT
preserved (unlike style HMR).

### Known Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Style flickering on initial load | `<link>` tag loading delay | Disable HMR: `ng serve --no-hmr` |
| State lost on template change | Template HMR reloads component | Expected behavior |
| Styles not applying | HMR style injection failed | Full page reload (`Ctrl+Shift+R`) |

### Disabling HMR

```bash
ng serve --no-hmr
```

Or in `angular.json`:

```json
{
  "serve": {
    "options": {
      "hmr": false
    }
  }
}
```

## Angular Material and CDK Updates

### Version Alignment

Angular Material follows the same major versioning. Always update together:

```bash
ng update @angular/cli@{ver} @angular/core@{ver} @angular/material@{ver}
```

### Material Design 3 (M3)

Starting with Material v20, M3 is the default design system:

- Visual appearance changes (colors, shapes, typography)
- Some component APIs changed
- Custom themes may need updating

### Material Migration Schematics

Material runs its own schematics during `ng update`:

- Component API updates
- Theme system updates
- Deprecated component removals

### CDK Test Harnesses

CDK component test harnesses work with both Karma and Vitest.
No migration needed for harness-based tests.

```typescript
import { HarnessLoader } from '@angular/cdk/testing';
import { TestbedHarnessEnvironment } from '@angular/cdk/testing/testbed';

let loader: HarnessLoader;

beforeEach(() => {
  const fixture = TestBed.createComponent(MyComponent);
  loader = TestbedHarnessEnvironment.loader(fixture);
});

it('should work', async () => {
  const button = await loader.getHarness(MatButtonHarness);
  await button.click();
});
```

## Monorepo and Workspace Considerations

### Nx Workspaces

Use `nx migrate` instead of `ng update`:

```bash
# Generate migrations
nx migrate @angular/core@21

# Run migrations
nx migrate --run-migrations

# Verify
nx run-many --target=build --all
nx run-many --target=test --all
```

Nx handles:
- Cross-project dependency updates
- Workspace-level configuration
- Parallel builds and tests
- Affected project detection

### Multi-App Workspaces

For Angular CLI workspaces with multiple projects:

```bash
# Update applies to all projects
ng update @angular/core@21 @angular/cli@21

# Run schematics per project
ng generate @angular/core:standalone --project=app1
ng generate @angular/core:standalone --project=app2

# Or target all with --path
ng generate @angular/core:signal-input-migration --path=projects/
```

### Library Considerations

If you maintain Angular libraries:

- Libraries should support at least 2 Angular major versions
- Use peer dependencies with range: `"@angular/core": ">=20.0.0"`
- Test against multiple Angular versions in CI
- Keep `NgZone.run()` / `NgZone.runOutsideAngular()` for Zone.js
  compatibility (even if your library is zoneless)
- Consider providing migration schematics for breaking changes

## CI/CD Pipeline Updates

After upgrading, update CI configuration:

```yaml
# Example: GitHub Actions
- uses: actions/setup-node@v4
  with:
    node-version: '20'  # v20+ required for Angular 20+

# Build
- run: ng build --configuration production

# Test (v21+ with Vitest)
- run: ng test --watch=false --browsers=ChromeHeadless

# Or Vitest
- run: ng test
```

Ensure CI uses:
- Node.js >= 20.11.1
- Correct test runner (Vitest or Karma bridge)
- Updated cache keys (package-lock.json changes)
