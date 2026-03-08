# Angular Zoneless Migration

Sources: angular.dev/guide/zoneless, Angular Blog (announcing-angular-v21, meet-angular-v19), community zoneless migration guides (2024-2026)

Covers: Zone.js removal strategy, zoneless compatibility requirements, change detection behavior, testing, SSR considerations, and incremental migration path.

## Zoneless Timeline

| Version | Zone.js Status | API |
|---------|---------------|-----|
| v18 | Required (default) | `provideExperimentalZonelessChangeDetection()` (experimental) |
| v19 | Required (default) | Same experimental API |
| v20 | Optional | `provideZonelessChangeDetection()` (stable in v20.2) |
| v21 | Not included by default | Zoneless is the default for new apps |

## Why Go Zoneless

Zone.js patches browser async APIs (setTimeout, Promise, fetch, DOM events)
and triggers change detection whenever any async operation completes. This
creates problems:

- **Performance**: Change detection runs far more often than necessary because
  Zone.js cannot know whether state actually changed
- **Bundle size**: Zone.js adds ~13KB gzipped to every application
- **Startup cost**: Patching all browser APIs adds initialization overhead
- **Debugging**: Stack traces become harder to read with Zone.js monkey-patching
- **Compatibility**: Some browser APIs can't be patched (async/await), and some
  libraries conflict with Zone.js patching

Zoneless Angular uses signals and explicit notifications instead — change
detection runs only when something actually changed.

## Enabling Zoneless

### For New Apps (v21+)

Zoneless is the default. Verify `provideZoneChangeDetection` is NOT used
anywhere to override the default.

### For Existing Apps (v20+)

```typescript
// app.config.ts
import { provideZonelessChangeDetection } from '@angular/core';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    // ... other providers
  ]
};
```

### For NgModule-Based Apps

```typescript
@NgModule({
  providers: [provideZonelessChangeDetection()],
})
export class AppModule {}
```

### Removing Zone.js from Build

After enabling zoneless, remove Zone.js from the build:

1. Remove from `angular.json` polyfills (both `build` and `test` targets):

```json
{
  "architect": {
    "build": {
      "options": {
        "polyfills": []
      }
    },
    "test": {
      "options": {
        "polyfills": []
      }
    }
  }
}
```

2. Remove from `polyfills.ts` if it exists:

```typescript
// Remove these lines:
// import 'zone.js';
// import 'zone.js/testing';
```

3. Uninstall the package:

```bash
npm uninstall zone.js
```

If Zone.js is still loaded when zoneless is enabled, Angular throws
warning `NG0914`.

## Compatibility Requirements

Angular requires explicit change detection notifications in zoneless mode.
These notifications tell Angular when to check for updates:

### Notification Mechanisms

| Mechanism | Description |
|-----------|-------------|
| Signal update | Updating a signal read in a template |
| `ChangeDetectorRef.markForCheck()` | Manual notification (called by `AsyncPipe`) |
| `ComponentRef.setInput()` | Programmatic input setting |
| Bound host/template listener callbacks | Event handlers |
| Attaching a dirty view | View marked dirty by above mechanisms |

### OnPush Compatibility

`OnPush` components are already compatible with zoneless because they
rely on the same notification mechanisms. Making all components OnPush
is the recommended first step toward zoneless.

OnPush is recommended but not required. Components can use `Default`
strategy as long as they notify Angular of changes via the mechanisms
above.

### What Must Be Removed

| Pattern | Why It Breaks | Replacement |
|---------|--------------|-------------|
| `NgZone.onMicrotaskEmpty` | Never emits in zoneless | `afterNextRender()` |
| `NgZone.onUnstable` | Never emits | Remove or use signals |
| `NgZone.onStable` | Never emits | `afterNextRender()` / `afterEveryRender()` |
| `NgZone.isStable` | Always `true` | Remove condition |
| Implicit async change detection | Zone.js not patching | Use signals or `markForCheck()` |

### What Still Works

| Pattern | Status |
|---------|--------|
| `NgZone.run()` | Works (no-op but compatible) |
| `NgZone.runOutsideAngular()` | Works (no-op but compatible) |
| `AsyncPipe` | Works (calls `markForCheck()` internally) |
| Manual `markForCheck()` | Works |
| Signal-based templates | Works (primary mechanism) |

Keep `NgZone.run()` and `NgZone.runOutsideAngular()` in library code —
removing them can cause regressions for consumers still using Zone.js.

## Pre-Migration Compatibility Audit

Before enabling zoneless, audit your codebase:

### Step 1: Find Zone.js Dependencies

Search for these patterns in your codebase:

```
NgZone.onMicrotaskEmpty
NgZone.onUnstable
NgZone.onStable
NgZone.isStable
```

Each must be replaced before going zoneless.

### Step 2: Find Implicit Change Detection

Look for patterns that rely on Zone.js triggering CD:

```typescript
// BREAKS in zoneless — no Zone.js to detect the setTimeout
setTimeout(() => {
  this.data = newData;  // UI won't update
}, 1000);

// FIX: Use signals
private _data = signal(initialData);
setTimeout(() => {
  this._data.set(newData);  // Signal notifies Angular
}, 1000);
```

```typescript
// BREAKS in zoneless — Promise completion not detected
async loadData() {
  this.data = await fetchData();  // UI won't update
}

// FIX: Use signals
private _data = signal(initialData);
async loadData() {
  this._data.set(await fetchData());  // Signal notifies
}
```

### Step 3: Check Third-Party Libraries

Libraries that assume Zone.js patches async operations will not trigger
change detection in zoneless mode. Common issues:

- UI libraries that modify DOM outside Angular
- State management libraries that use Zone.js for change notification
- Animation libraries that use requestAnimationFrame

For incompatible libraries, options:
1. Update to a version that supports zoneless
2. Wrap with `ChangeDetectorRef.markForCheck()`
3. Fall back to Zone.js temporarily

### Step 4: Verify OnPush Coverage

Components using `ChangeDetectionStrategy.Default` without signals
will not update in zoneless mode unless they use `markForCheck()`.

Recommended: Convert all components to OnPush as an intermediate step.

## SSR Considerations

### PendingTasks for Server Rendering

Without Zone.js, Angular cannot automatically determine when async work
is complete for SSR serialization. Use `PendingTasks`:

```typescript
const taskService = inject(PendingTasks);

// Option 1: run() wraps async work
taskService.run(async () => {
  const result = await loadDataForSSR();
  this.state.set(result);
});

// Option 2: Manual add/remove for complex cases
const cleanup = taskService.add();
try {
  await doWork();
} finally {
  cleanup();
}
```

### pendingUntilEvent for Observables

```typescript
import { pendingUntilEvent } from '@angular/core/rxjs-interop';

readonly data = someObservable.pipe(pendingUntilEvent());
```

Keeps the application "unstable" (prevents serialization) until the
observable emits, completes, errors, or is unsubscribed.

## Testing in Zoneless Mode

### TestBed Configuration

When `zone.js` is not loaded, TestBed runs zoneless by default.
To force zoneless when `zone.js` is loaded:

```typescript
TestBed.configureTestingModule({
  providers: [provideZonelessChangeDetection()],
});

const fixture = TestBed.createComponent(MyComponent);
await fixture.whenStable();  // Preferred over fixture.detectChanges()
```

### Prefer `whenStable()` Over `detectChanges()`

In zoneless mode, prefer `await fixture.whenStable()` instead of
`fixture.detectChanges()`. This lets Angular decide when to run CD
based on notifications — matching production behavior.

`fixture.detectChanges()` still works but forces CD regardless of
whether Angular would have scheduled it.

### ExpressionChangedAfterItHasBeenCheckedError

TestBed in zoneless mode enforces OnPush compatibility. If a test
updates a component property without notification:

```typescript
// This will throw ExpressionChangedAfterItHasBeenChecked:
fixture.componentInstance.someValue = 'newValue';
fixture.detectChanges();

// Fix: Use signals
fixture.componentInstance.someSignal.set('newValue');
await fixture.whenStable();

// Or: Mark for check explicitly
fixture.componentInstance.someValue = 'newValue';
fixture.changeDetectorRef.markForCheck();
await fixture.whenStable();
```

### Debug Mode: Exhaustive Change Check

For development, enable periodic checks that catch missed notifications:

```typescript
provideCheckNoChangesConfig({
  exhaustive: true,
  interval: 500 // milliseconds
});
```

Throws `ExpressionChangedAfterItHasBeenCheckedError` if bindings
updated without notification.

## Incremental Migration Path

### Phase 1: Add OnPush Everywhere

Convert all components to `ChangeDetectionStrategy.OnPush`. This is
compatible with Zone.js and prepares for zoneless.

### Phase 2: Convert to Signals

Run migration schematics for signal inputs, outputs, queries.
Convert service state to signals. See `references/signals-migration.md`.

### Phase 3: Eliminate Zone.js Dependencies

Remove `NgZone.onMicrotaskEmpty`, `NgZone.onStable`, etc.
Replace implicit async detection with signal updates.

### Phase 4: Enable Zoneless

```typescript
providers: [provideZonelessChangeDetection()]
```

Keep Zone.js in polyfills initially — test thoroughly.

### Phase 5: Remove Zone.js

Remove from polyfills, uninstall package. Test again.

### Fallback

If issues arise, revert to Zone.js:

```typescript
providers: [
  provideZoneChangeDetection({ eventCoalescing: true })
]
```

Add `zone.js` back to polyfills.

## Common Zoneless Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| UI doesn't update after async op | No signal/markForCheck | Use signal or call `markForCheck()` |
| NG0914 warning | Zone.js still loaded | Remove from polyfills |
| Third-party component doesn't render | Library expects Zone.js | Update library or wrap with `markForCheck()` |
| SSR hangs indefinitely | Async task not tracked | Use `PendingTasks` |
| Tests fail with ExpressionChanged | Property set without notification | Use signals or `markForCheck()` |
| `NgZone.isStable` always true | Expected — zoneless has no zone | Remove isStable checks |
