# Widget Architecture

Sources: Flutter official documentation (flutter.dev 2025-2026), Flutter architectural overview, Dart language specification, Flutter API reference (api.flutter.dev)

Covers: widget tree vs Element tree vs RenderObject tree, BuildContext, widget lifecycle, Key types, composition patterns, and common anti-patterns.

## Three Trees

Flutter maintains three parallel trees. Misunderstanding their relationship causes most performance and state-preservation bugs.

| Tree | Object | Role | Lifetime |
|------|--------|------|----------|
| Widget tree | `Widget` | Immutable configuration / blueprint | Recreated every `build()` |
| Element tree | `Element` | Mutable instance managing widget-to-render binding | Persistent across frames |
| RenderObject tree | `RenderObject` | Handles layout, painting, hit testing | Persistent, updated in-place |

### How They Interact

1. `Widget.createElement()` creates an `Element` on first inflation
2. Element holds a reference to both its `Widget` and its `RenderObject`
3. On rebuild, framework calls `Element.update(newWidget)` — if `widget.runtimeType` and `key` match, the Element is reused; otherwise it is unmounted and a new one created
4. `RenderObject` is updated in place (no recreation) unless the Element itself is replaced

### Why This Matters

Widgets are cheap — recreate them freely. Elements are the real cost. When the framework can reuse an Element, it skips the entire subtree recreation. This is why `const` constructors and proper Keys are performance-critical.

## BuildContext

`BuildContext` is the Element. The `context` parameter in `build(BuildContext context)` IS the widget's Element cast to the `BuildContext` interface.

### Common Uses

```dart
// Look up inherited data (theme, media query, providers)
final theme = Theme.of(context);
final size = MediaQuery.sizeOf(context);

// Navigate (if not using GoRouter)
Navigator.of(context).push(...);

// Find ancestor state
Scaffold.of(context).openDrawer();

// Show overlays
showDialog(context: context, builder: (_) => ...);
```

### Rules

- Never store `BuildContext` in a field — it becomes stale after unmount
- Never use `context` across async gaps without checking `mounted`
- `Theme.of(context)` registers a dependency — the widget rebuilds when theme changes
- Use `Theme.of(context)` (rebuilds on change) vs `context.read()` (does not) deliberately

```dart
// WRONG: context used after async gap
Future<void> _save() async {
  await repository.save(data);
  Navigator.of(context).pop(); // context may be stale
}

// CORRECT: check mounted
Future<void> _save() async {
  await repository.save(data);
  if (!mounted) return;
  Navigator.of(context).pop();
}
```

## Widget Types

### StatelessWidget

Pure function of its configuration. No mutable state. Preferred default.

```dart
class PriceTag extends StatelessWidget {
  const PriceTag({super.key, required this.amount, this.currency = 'USD'});
  final double amount;
  final String currency;

  @override
  Widget build(BuildContext context) {
    return Text(
      '${amount.toStringAsFixed(2)} $currency',
      style: Theme.of(context).textTheme.titleMedium,
    );
  }
}
```

Use when: display-only widgets, layout wrappers, widgets that derive everything from parameters or inherited data.

### StatefulWidget

Owns mutable state that outlives a single `build()` call.

```dart
class SearchField extends StatefulWidget {
  const SearchField({super.key, required this.onChanged});
  final ValueChanged<String> onChanged;

  @override
  State<SearchField> createState() => _SearchFieldState();
}

class _SearchFieldState extends State<SearchField> {
  late final TextEditingController _controller;
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _onChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () {
      widget.onChanged(value);
    });
  }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: _controller,
      onChanged: _onChanged,
      decoration: const InputDecoration(hintText: 'Search...'),
    );
  }
}
```

Use when: animations, form controllers, timers, listeners, any mutable local state.

### InheritedWidget

Provides data to descendants without passing through every constructor. Foundation of `Theme.of()`, `MediaQuery.of()`, and Provider.

```dart
class AppConfig extends InheritedWidget {
  const AppConfig({
    super.key,
    required this.apiBaseUrl,
    required super.child,
  });
  final String apiBaseUrl;

  static AppConfig of(BuildContext context) {
    return context.dependOnInheritedWidgetOfExactType<AppConfig>()!;
  }

  @override
  bool updateShouldNotify(AppConfig oldWidget) {
    return apiBaseUrl != oldWidget.apiBaseUrl;
  }
}
```

Use when: injecting configuration, custom themes, or feature flags down the tree. For state management, prefer Riverpod or BLoC over raw InheritedWidget.

## Lifecycle Methods

Methods called in order during a StatefulWidget's life:

| Method | When Called | Use For |
|--------|-----------|---------|
| `createState()` | Widget first inserted | Framework calls this; return State instance |
| `initState()` | State created, once | Controllers, subscriptions, one-time setup |
| `didChangeDependencies()` | After `initState`, and when InheritedWidget changes | Reading InheritedWidget values that need initialization |
| `build()` | Every frame that needs rebuild | Return widget tree; keep pure |
| `didUpdateWidget(old)` | Parent rebuilds with new widget instance | Compare old and new config, update controllers |
| `deactivate()` | Element removed from tree (may reinsert) | Rare; clean up tree-position-dependent state |
| `dispose()` | Element permanently removed | Cancel subscriptions, dispose controllers, release resources |

### Critical Rules

- Call `super.initState()` first, `super.dispose()` last
- Never call `setState` in `dispose`
- `build` must be pure — no side effects, no async calls
- Dispose every controller and subscription created in `initState`

## Keys

Keys control Element reuse. Without keys, Flutter matches widgets by position in the child list. With keys, it matches by key identity.

### When Keys Are Required

- Items in a list that can be reordered, added, or removed
- Widgets that hold state and move in the tree
- Forcing a full state reset (new key = new Element = new State)

### Key Types

| Key | Identity | Use Case |
|-----|----------|----------|
| `ValueKey<T>(value)` | Value equality | List items with unique IDs: `ValueKey(item.id)` |
| `ObjectKey(object)` | Object identity | When the object reference itself is the identity |
| `UniqueKey()` | Always unique (new instance each build) | Force Element recreation every build |
| `GlobalKey<T>()` | Global uniqueness across the tree | Access State from outside, move widgets between trees |

### GlobalKey Warnings

- Expensive: framework does global lookup
- Only one widget in the tree can hold a given GlobalKey at a time
- Use for: accessing `FormState` (`_formKey.currentState?.validate()`), moving a widget to a different parent while preserving state
- Do not use as a substitute for proper state management

```dart
// Correct: GlobalKey to access form state
final _formKey = GlobalKey<FormState>();

Form(
  key: _formKey,
  child: Column(children: [/* fields */]),
);

void _submit() {
  if (_formKey.currentState?.validate() ?? false) {
    _formKey.currentState!.save();
  }
}
```

## Composition Patterns

### Extract, Do Not Nest

Split large `build` methods into separate widget classes, not helper methods.

```dart
// WRONG: helper method — no separate Element, no rebuild optimization
Widget _buildHeader() {
  return Container(...);
}

// CORRECT: separate widget — own Element, const-optimizable, testable
class OrderHeader extends StatelessWidget {
  const OrderHeader({super.key, required this.order});
  final Order order;

  @override
  Widget build(BuildContext context) => Container(...);
}
```

### Builder Pattern for Deferred Build

Use `Builder` or `LayoutBuilder` when you need a fresh `BuildContext` inside a subtree:

```dart
Scaffold(
  body: Builder(
    builder: (scaffoldContext) {
      // scaffoldContext is below Scaffold, so Scaffold.of works
      return ElevatedButton(
        onPressed: () => Scaffold.of(scaffoldContext).openDrawer(),
        child: const Text('Open Drawer'),
      );
    },
  ),
);
```

### Slot Pattern

Define named slots for customizable subwidgets:

```dart
class AppCard extends StatelessWidget {
  const AppCard({super.key, required this.title, this.trailing, required this.child});
  final Widget title;
  final Widget? trailing;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        children: [
          Row(children: [Expanded(child: title), if (trailing != null) trailing!]),
          child,
        ],
      ),
    );
  }
}
```

## Common Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| State in `build()` method | Recreated every frame, causes flicker | Move to `initState` or state management |
| `setState(() {})` with empty callback | Rebuilds entire widget for nothing | Only call when state actually changes |
| Deeply nested widget trees in one class | Hard to test, hard to optimize | Extract into separate widget classes |
| Using `GlobalKey` for state access | Global lookup, fragile, expensive | Use Riverpod/BLoC for cross-widget state |
| Missing `const` on static widgets | Prevents framework rebuild optimization | Add `const` to every possible constructor |
| Storing `BuildContext` in fields | Stale after unmount, causes crashes | Use `mounted` check, pass context locally |
| Creating `ScrollController` in `build` | New controller per frame, scroll position lost | Create in `initState`, dispose in `dispose` |
| Heavy computation in `build` | Jank on every rebuild | Move to `initState`, compute once, or use `FutureBuilder` |
