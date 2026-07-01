# New Architecture

Sources: React Native Documentation (2025-2026), Expo New Architecture guide, React Native blog (0.82-0.83 releases), React Conf 2025 keynote

Covers: Fabric renderer, TurboModules, JSI (JavaScript Interface), bridgeless mode, migration from legacy architecture, library compatibility, and Expo Modules API for New Architecture-native development.

## Architecture Overview

The New Architecture replaces the legacy bridge-based communication between JavaScript and native with synchronous, type-safe interfaces. Three pillars:

| Component | Replaces | Purpose |
|-----------|----------|---------|
| Fabric | Legacy Renderer | Synchronous, concurrent-capable UI rendering |
| TurboModules | Native Modules (Bridge) | Lazy-loaded, type-safe native module access |
| JSI | JSON Bridge | Direct C++ interface between JS and native |

### Legacy vs New Architecture

| Dimension | Legacy (Bridge) | New Architecture (JSI) |
|-----------|----------------|----------------------|
| Communication | Async JSON serialization over bridge | Synchronous C++ bindings |
| Module loading | All modules loaded at startup | Lazy loading via TurboModules |
| Rendering | Shadow tree in JS, async commit | Fabric: C++ shadow tree, synchronous layout |
| Threading | JS thread, main thread, shadow thread | Concurrent rendering, shared ownership |
| Type safety | Runtime JSON parsing | Codegen from typed specs |
| React features | Limited Suspense support | Full Suspense, concurrent features, transitions |

### JSI (JavaScript Interface)

JSI is the foundation layer. It provides:

- Direct memory sharing between JS and native (no serialization)
- Synchronous function calls from JS to C++
- Host objects accessible from JavaScript
- Engine-agnostic (works with Hermes, JSC, V8)

```
JavaScript <--JSI--> C++ <--JNI/ObjC--> Native Platform
```

JSI eliminates the async bridge bottleneck. Native calls that previously required message queuing and JSON serialization now execute as direct function calls.

## Fabric Renderer

Fabric is the New Architecture's rendering system. It replaces the legacy renderer with a C++ core that enables concurrent rendering.

### Key Improvements

| Feature | Description |
|---------|-------------|
| Synchronous layout | Layout computed in C++, no async bridge round-trips |
| Concurrent rendering | Multiple render trees in progress simultaneously |
| Priority-based updates | Urgent updates (input) prioritized over background |
| Reduced memory | Immutable shadow tree with structural sharing |
| Better Suspense | Full support for React Suspense boundaries |

### Shadow Tree

Fabric maintains an immutable shadow tree in C++:

```
React Tree (JS) --> Shadow Tree (C++) --> Native View Tree (Platform)
```

1. React commits a new tree
2. Fabric diffs old and new shadow trees in C++
3. Mutations applied to the native view tree synchronously
4. Layout calculation uses Yoga (C++ layout engine)

### Interop Layer

React Native 0.74+ includes interop layers that allow legacy components and modules to work on the New Architecture without rewriting. Most third-party libraries work through interop without changes.

| Interop | What It Does |
|---------|-------------|
| Legacy Renderer Interop | Legacy native components render inside Fabric |
| Legacy Module Interop | Bridge-based modules accessible via TurboModule system |

The interop is not perfect. Libraries with complex threading or bridge assumptions may need updates. Check [React Native Directory](https://reactnative.directory/) for compatibility status.

## TurboModules

TurboModules replace the legacy Native Modules system with lazy-loaded, type-safe modules.

### Key Differences from Legacy Modules

| Dimension | Legacy Native Modules | TurboModules |
|-----------|----------------------|-------------|
| Loading | All loaded at startup | Lazy: loaded on first use |
| Type safety | Runtime only | Codegen from Flow/TS specs |
| Communication | Async bridge (JSON) | Synchronous via JSI |
| Startup impact | All modules penalize startup | Only used modules loaded |
| Error detection | Runtime crashes | Build-time type checking |

### Creating a TurboModule Spec

Define the interface in TypeScript:

```typescript
// specs/NativeCalculator.ts
import type { TurboModule } from 'react-native';
import { TurboModuleRegistry } from 'react-native';

export interface Spec extends TurboModule {
  add(a: number, b: number): number;        // synchronous
  fetchData(url: string): Promise<string>;    // asynchronous
}

export default TurboModuleRegistry.getEnforcing<Spec>('NativeCalculator');
```

Codegen generates C++ interfaces from this spec. Implement the native side in Swift/Kotlin.

## Bridgeless Mode

Bridgeless mode removes the legacy bridge entirely. In SDK 55+, bridgeless is the only mode.

| Aspect | With Bridge (Legacy) | Bridgeless |
|--------|---------------------|------------|
| Startup | Bridge initialization adds overhead | No bridge to initialize |
| Module access | Through bridge message queue | Direct JSI bindings |
| Error handling | Bridge errors are opaque | Direct native stack traces |
| Interop | Bridge always available | Interop layer for legacy modules |

### What Bridgeless Means in Practice

- No `NativeModules` bridge object (use TurboModuleRegistry)
- No `UIManager` commands through bridge (use Fabric direct manipulation)
- Legacy `NativeEventEmitter` works through interop
- `requireNativeComponent` works through Fabric interop

## SDK and Version Timeline

| SDK | React Native | Architecture Status |
|-----|-------------|-------------------|
| SDK 51 | 0.74 | New Arch optional, off by default |
| SDK 52 | 0.76 | New Arch on by default |
| SDK 53 | 0.77 | New Arch on, all expo-* packages compatible |
| SDK 54 | 0.79 | New Arch on, last SDK allowing opt-out |
| SDK 55 | 0.83 | New Arch always on, cannot disable |

As of January 2026, approximately 83% of SDK 54 projects built with EAS Build use the New Architecture.

## Migration Guide

### Step 1: Check Library Compatibility

```bash
# Run Expo Doctor to check all dependencies
npx expo-doctor@latest
```

Expo Doctor checks against React Native Directory data. Address incompatible libraries:

| Status | Action |
|--------|--------|
| Compatible | No action needed |
| Compatible via interop | Works but may have edge cases |
| Incompatible | Find alternative or wait for update |
| Unmaintained | Replace with maintained alternative |

### Step 2: Enable New Architecture (SDK 54 and earlier)

```json
{
  "expo": {
    "newArchEnabled": true
  }
}
```

SDK 55+ has no toggle. The New Architecture is always enabled.

### Step 3: Rebuild

```bash
npx expo prebuild --clean
npx expo run:ios
# or
eas build -p ios --profile development
```

### Step 4: Test Thoroughly

Focus areas during migration testing:

| Area | What to Check |
|------|--------------|
| Native views | All custom views render correctly |
| Animations | Reanimated and Gesture Handler work |
| Navigation | All navigation transitions smooth |
| Third-party SDKs | Maps, payments, analytics function |
| Performance | No regressions in scroll, startup |

### Common Migration Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `requireNativeComponent` crash | Component not Fabric-compatible | Update library or use interop |
| Native module not found | Module not registered as TurboModule | Check library version supports New Arch |
| Layout differences | Yoga engine changes in Fabric | Adjust flex styles, test on both platforms |
| `UIManager` errors | Direct UIManager access removed | Use Fabric APIs or refs |

## Expo Modules API

Build New Architecture-native modules using the Expo Modules API in Swift and Kotlin:

```swift
// ios/MyModule.swift
import ExpoModulesCore

public class MyModule: Module {
  public func definition() -> ModuleDefinition {
    Name("MyModule")

    Function("hello") { (name: String) -> String in
      return "Hello, \(name)!"
    }

    AsyncFunction("fetchData") { (url: String) -> String in
      let data = try await URLSession.shared.data(from: URL(string: url)!)
      return String(data: data.0, encoding: .utf8) ?? ""
    }
  }
}
```

```kotlin
// android/MyModule.kt
package com.example.mymodule

import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

class MyModule : Module() {
  override fun definition() = ModuleDefinition {
    Name("MyModule")

    Function("hello") { name: String ->
      "Hello, $name!"
    }

    AsyncFunction("fetchData") { url: String ->
      // Kotlin coroutine-based async
      URL(url).readText()
    }
  }
}
```

Expo Modules API automatically supports the New Architecture. No separate Fabric/TurboModule boilerplate required.

### When to Use Expo Modules API vs Raw TurboModules

| Signal | Recommendation |
|--------|---------------|
| New module in Expo project | Expo Modules API (simpler, auto New Arch support) |
| Cross-platform library for npm | Expo Modules API or TurboModule spec |
| Performance-critical C++ module | Raw TurboModule with JSI bindings |
| Wrapping existing native SDK | Expo Modules API with config plugin |

## Performance Gains

The New Architecture delivers measurable performance improvements:

| Metric | Improvement | Mechanism |
|--------|------------|-----------|
| Startup time | 10-30% faster | Lazy TurboModule loading, no bridge init |
| Interaction latency | Synchronous native calls | JSI eliminates async bridge round-trips |
| Memory usage | Reduced | Immutable shadow tree, structural sharing |
| Scroll performance | Smoother | Synchronous layout, priority rendering |
| Concurrent features | Enabled | Suspense, transitions, useTransition |

## Library Compatibility Quick Reference

| Library | Status (2026) |
|---------|--------------|
| All `expo-*` packages | Fully compatible |
| react-native-reanimated | Fully compatible |
| react-native-gesture-handler | Fully compatible |
| react-native-screens | Fully compatible |
| react-native-svg | Fully compatible |
| @react-navigation/* | Fully compatible |
| react-native-maps | v1.20+ via interop, v1.21+ native |
| @stripe/react-native | v0.45.0+ compatible |
| react-native-firebase | Fully compatible |
