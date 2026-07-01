---
name: "@tank/flutter-dev"
description: |
  Production Flutter and Dart development patterns for mobile, web, and desktop.
  Covers widget architecture (StatelessWidget, StatefulWidget, InheritedWidget,
  Element tree, Keys, BuildContext), state management (Riverpod, BLoC/Cubit,
  Provider), navigation (GoRouter, deep linking, guards, ShellRoute), modern
  Dart patterns (null safety, sealed classes, records, pattern matching,
  extensions, Freezed), layout systems (Flex, Stack, Sliver, responsive design,
  Material 3, Cupertino), testing (widget tests, integration tests, golden
  tests, mocking), performance profiling (DevTools, const constructors,
  RepaintBoundary), platform channels (MethodChannel, EventChannel, FFI),
  and deployment (Android/iOS/web, flavors, CI/CD, Fastlane, Codemagic).

  Synthesizes Flutter official documentation (flutter.dev 2025-2026),
  Dart language specification (Dart 3.x), Riverpod documentation,
  flutter_bloc documentation, GoRouter API reference, and pub.dev
  ecosystem patterns.

  Trigger phrases: "flutter", "flutter widget", "flutter state management",
  "flutter riverpod", "flutter bloc", "flutter navigation", "flutter testing",
  "flutter performance", "flutter deployment", "dart patterns", "go_router",
  "flutter layout", "flutter animation", "platform channel", "flutter web",
  "flutter desktop", "flutter firebase", "pub.dev", "widget test",
  "StatefulWidget", "BuildContext", "flutter best practices",
  "flutter architecture", "flutter CI/CD", "flutter app store"
---

# Flutter Development

## Core Philosophy

1. **Composition over inheritance** — Build complex UIs by combining small, focused widgets. Extract widgets into separate classes instead of adding parameters to bloated ones.
2. **Immutable widget tree, mutable state tree** — Widgets are throwaway configuration objects. The Element tree persists across frames and drives performance. Understand this distinction to avoid unnecessary rebuilds.
3. **Push state down, lift state up** — Keep state as close to where it is consumed as possible. Lift only when siblings need to share it. Use Riverpod or BLoC for app-level state, `setState` for ephemeral UI state.
4. **Declarative navigation** — Use GoRouter for URL-based, declarative routing. Imperative `Navigator.push` breaks deep linking, web URLs, and state restoration.
5. **Test the widget, not the framework** — Write widget tests that verify behavior, not Flutter internals. Use golden tests for visual regression. Test state management in isolation with unit tests.

## Quick-Start: Common Problems

### "Which state management should I use?"

| App Type | Recommended |
|----------|------------|
| New app, any size | Riverpod (NotifierProvider + AsyncNotifierProvider) |
| Existing app with Provider | Migrate incrementally to Riverpod |
| Enterprise, strict event audit | BLoC (event-driven, traceable) |
| Simple prototype / MVP | Riverpod or even plain setState |
| Legacy app with ChangeNotifier | Provider package (maintain, don't rewrite) |
-> See `references/state-management.md`

### "My widget rebuilds too often"

1. Mark constructors `const` — enables framework-level rebuild skipping
2. Extract subtrees that depend on different state into separate widgets
3. Use `select` (Riverpod) or `BlocSelector` (BLoC) to watch specific fields
4. Add `RepaintBoundary` around expensive paint operations
5. Profile with Flutter DevTools Widget Rebuild Tracker
-> See `references/performance-deployment.md`

### "How do I structure navigation with tabs and auth?"

1. Use `GoRouter` with `StatefulShellRoute` for persistent tab navigation
2. Add `redirect` for auth guards — check auth state, redirect to `/login`
3. Use `ShellRoute` for shared scaffolds (AppBar, Drawer)
4. Handle deep links by defining path parameters: `/user/:id`
-> See `references/navigation-routing.md`

### "How do I test a widget that depends on Riverpod/BLoC?"

1. Riverpod: wrap with `ProviderScope`, override providers with mock values
2. BLoC: use `BlocProvider.value` with a mock Bloc/Cubit
3. Use `pumpWidget` + `pumpAndSettle` for async rendering
4. Golden tests: `expectLater(find.byType(X), matchesGoldenFile('x.png'))`
-> See `references/testing.md`

### "When do I use which Dart pattern?"

1. Sealed classes for state unions (loading/data/error)
2. Records for returning multiple values without creating a class
3. Pattern matching with `switch` expressions for exhaustive handling
4. Extensions for adding methods to types you do not own
5. Freezed for data classes with copyWith, equality, JSON serialization
-> See `references/dart-patterns.md`

## Decision Trees

### Widget Type Selection

| Signal | Widget Type |
|--------|------------|
| No mutable state, pure UI | `StatelessWidget` (use `const`) |
| Ephemeral UI state (animation, form input) | `StatefulWidget` + `setState` |
| State shared across subtree without passing props | `InheritedWidget` (or Riverpod) |
| Needs `TickerProvider` for animations | `StatefulWidget` with `SingleTickerProviderStateMixin` |

### Layout Widget Selection

| Need | Widget |
|------|--------|
| Horizontal or vertical list of children | `Row` / `Column` (Flex) |
| Overlapping children | `Stack` + `Positioned` |
| Scrollable list of unknown length | `ListView.builder` |
| Scrollable with mixed content (headers, grids, lists) | `CustomScrollView` + `Sliver*` |
| Responsive sizing | `LayoutBuilder` or `MediaQuery` |
| Adaptive per platform (Material vs Cupertino) | Platform checks + `.adaptive` constructors |

### Key Type Selection

| Scenario | Key Type |
|----------|---------|
| Reorder items in a list | `ValueKey(item.id)` |
| Preserve state when widget moves in tree | `GlobalKey` (use sparingly) |
| Force rebuild when data identity changes | `ValueKey(dataObject)` |
| Ensure unique key for generated widgets | `UniqueKey()` |

## Reference Index

| File | Contents |
|------|----------|
| `references/widget-architecture.md` | Widget tree, Element tree, BuildContext, Keys, lifecycle methods, composition patterns, RenderObject basics |
| `references/state-management.md` | Riverpod (all provider types, ref patterns, testing), BLoC/Cubit, Provider, selection decision framework |
| `references/navigation-routing.md` | GoRouter setup, ShellRoute, StatefulShellRoute, redirect guards, deep linking, path/query parameters, nested navigation |
| `references/dart-patterns.md` | Null safety, sealed classes, records, pattern matching, extensions, mixins, Freezed, code generation |
| `references/layouts-responsive.md` | Flex system, Stack, Slivers, LayoutBuilder, MediaQuery, breakpoints, Material 3, Cupertino, adaptive design |
| `references/testing.md` | Widget tests, integration tests, golden tests, Riverpod/BLoC test patterns, mocking with Mocktail |
| `references/performance-deployment.md` | DevTools profiling, const optimization, RepaintBoundary, tree shaking, flavors, CI/CD, Fastlane, app store submission |
