---
name: "@tank/flutter-widget-architecture"
description: |
  Master Flutter's widget tree architecture, rendering pipeline, and composition patterns for production apps.
  Covers StatelessWidget vs StatefulWidget vs InheritedWidget, BuildContext/Element internals, Key strategies,
  widget lifecycle, layout constraints, and performance anti-patterns. Based on Flutter framework source code,
  official documentation, and production patterns from Google and community best practices.

  Trigger phrases: "Flutter widget architecture", "StatefulWidget vs StatelessWidget", "BuildContext Element tree",
  "Flutter Key types", "widget lifecycle", "const widgets performance", "Flutter layout constraints",
  "composition over inheritance Flutter", "GlobalKey when to use", "didChangeDependencies",
  "RenderBox constraints", "Flutter anti-patterns", "responsive layout Flutter", "Material 3 design system"
---

# Flutter Widget Architecture & Composition Patterns

## Core Philosophy

1. **Composition Over Inheritance** — Build complex UIs by combining simple, focused widgets rather than creating deep inheritance hierarchies. Each widget should have a single responsibility.

2. **Immutability as Default** — Widgets are immutable configuration objects. State lives in State classes, not widgets. This enables efficient rebuilds and predictable behavior.

3. **BuildContext is Scope** — BuildContext represents a location in the widget tree. Use it to access ancestors (Theme, MediaQuery, InheritedWidgets) and manage lifecycle. Never store BuildContext across frames.

4. **Keys Solve Identity** — Keys explicitly tell Flutter which widget corresponds to which Element when the tree changes. Use them strategically for lists, reordering, and state preservation.

5. **Constraints Flow Down, Sizes Flow Up** — The layout system is unidirectional. Parent constraints determine child possibilities; children report their sizes. Understand this to debug layout issues.

## Quick-Start: Common Problems

### "My widget rebuilds too often"
1. Extract expensive builds into separate `const` widgets
2. Use `const` constructors everywhere possible
3. Wrap expensive subtrees in `RepaintBoundary` or `SingleChildRenderObjectWidget`
4. Consider `ChangeNotifier` + `Consumer` instead of `setState` for fine-grained updates
-> See `references/widget-lifecycle.md` and `references/performance-patterns.md`

### "State is lost when I reorder list items"
1. Add `Key` to each list item widget (use `ValueKey(item.id)` not `ValueKey(index)`)
2. Understand Element identity: Keys preserve State across tree mutations
3. Never use index as a key for dynamic lists
-> See `references/key-strategies.md`

### "My layout is broken on different screen sizes"
1. Use `LayoutBuilder` to get parent constraints
2. Use `MediaQuery.of(context).size` for device dimensions
3. Define breakpoints and use `ConstrainedBox` + `SizedBox` strategically
4. Prefer `Flex` (Row/Column) over fixed sizes
-> See `references/layout-system.md` and `references/responsive-patterns.md`

### "I don't know when to use InheritedWidget"
1. Use for read-only data accessed by many descendants (Theme, Locale, AppState)
2. Prefer `Provider` or `Riverpod` for complex state management
3. InheritedWidget is low-level; higher-level packages wrap it
-> See `references/widget-types.md`

## Decision Trees

| Scenario | Widget Type | Rationale |
|----------|-------------|-----------|
| Static UI, no state | `StatelessWidget` | Simplest, most efficient. No lifecycle overhead. |
| UI changes based on internal state | `StatefulWidget` | Manages mutable state via State class. Use `setState()` for updates. |
| Multiple widgets need same data | `InheritedWidget` | Efficient broadcast to descendants. Triggers rebuilds only of dependents. |
| Complex state, multiple sources | `Provider`/`Riverpod` | Higher-level abstractions over InheritedWidget. Better testability. |
| Conditional rendering based on parent | `Builder` | Access BuildContext from parent without creating new widget. |
| Custom rendering/layout | `CustomPaint`/`RenderObjectWidget` | Direct access to Canvas or RenderObject. Low-level control. |

| Key Type | Use Case | Example |
|----------|----------|---------|
| `ValueKey<T>` | Stable, comparable data | `ValueKey(user.id)` for list items with unique IDs |
| `ObjectKey` | Object identity matters | `ObjectKey(item)` when object equality is unreliable |
| `GlobalKey` | Cross-widget access, form validation | `GlobalKey<FormState>()` to call `validate()` from parent |
| `UniqueKey` | Force rebuild every frame | Rarely needed; use only when you need guaranteed uniqueness |
| No key | Static lists, single-child widgets | Default for most widgets |

| Layout Problem | Solution | Details |
|---|---|---|
| Child too big for parent | `Constraints` + `ConstrainedBox` | Parent passes max constraints; child respects them. |
| Need flexible sizing | `Flex` (Row/Column) with `Expanded`/`Flexible` | Flex distributes space; Expanded takes all available. |
| Overlapping widgets | `Stack` with `Positioned` | Stack layers children; Positioned places them absolutely. |
| Scrollable content | `ListView`/`GridView` or `CustomScrollView` + `Sliver*` | Slivers are efficient for large lists. |
| Custom multi-child layout | `CustomMultiChildLayout` | Full control over child positioning and sizing. |

## Reference Index

| File | Contents |
|------|----------|
| `references/widget-types.md` | StatelessWidget, StatefulWidget, InheritedWidget, Builder patterns with code examples |
| `references/widget-lifecycle.md` | Complete lifecycle (initState, didChangeDependencies, build, deactivate, dispose) with timing diagrams |
| `references/key-strategies.md` | Key types, when to use each, list reordering patterns, GlobalKey pitfalls |
| `references/layout-system.md` | Constraints, RenderBox, Flex, Stack, Sliver, CustomMultiChildLayout with visual examples |
| `references/performance-patterns.md` | const widgets, RepaintBoundary, build() optimization, memory profiling |
| `references/composition-patterns.md` | Composition over inheritance, widget extraction, builder patterns, dependency injection |
| `references/responsive-patterns.md` | LayoutBuilder, MediaQuery, breakpoints, adaptive layouts for mobile/tablet/web |
| `references/design-systems.md` | Material 3 and Cupertino design system usage, theming, component patterns |
