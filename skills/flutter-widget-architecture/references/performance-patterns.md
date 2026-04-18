# Performance Patterns: const Widgets, RepaintBoundary, Build Optimization

Sources: Flutter performance documentation, DevTools profiling guides, production optimization patterns

Covers: const widgets, avoiding rebuilds, RepaintBoundary, memory profiling, and common performance anti-patterns.

## const Widgets: The Foundation

`const` widgets are immutable and reused across rebuilds. This is the single most important performance optimization.

### How const Works

```dart
// Without const: New instance created every rebuild
class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Text('Hello'); // New Text instance every time
  }
}

// With const: Same instance reused
class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return const Text('Hello'); // Reused across rebuilds
  }
}
```

### Making Widgets const

```dart
// Make constructor const
class MyButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;

  const MyButton({
    required this.label,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onPressed,
      child: Text(label),
    );
  }
}

// Use const when instantiating
const MyButton(label: 'Click me', onPressed: _handlePress)
```

### Anti-Pattern: Non-const Constructors

```dart
// WRONG: Constructor not const
class BadButton extends StatelessWidget {
  final String label;

  BadButton({required this.label}); // Not const!

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: () {},
      child: Text(label),
    );
  }
}

// CORRECT: Constructor is const
class GoodButton extends StatelessWidget {
  final String label;

  const GoodButton({required this.label}); // const!

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: () {},
      child: Text(label),
    );
  }
}
```

### Pattern: const Collections

```dart
// WRONG: New list every rebuild
class MyList extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text('Item 1'),
        Text('Item 2'),
        Text('Item 3'),
      ], // New list every time!
    );
  }
}

// CORRECT: const list
class MyList extends StatelessWidget {
  static const _items = [
    Text('Item 1'),
    Text('Item 2'),
    Text('Item 3'),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(children: _items);
  }
}
```

## Avoiding Unnecessary Rebuilds

### Extract Expensive Widgets

```dart
// WRONG: Expensive widget rebuilds with parent
class BadParent extends StatefulWidget {
  @override
  State<BadParent> createState() => _BadParentState();
}

class _BadParentState extends State<BadParent> {
  int _counter = 0;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ExpensiveWidget(), // Rebuilds every time counter changes!
        ElevatedButton(
          onPressed: () => setState(() => _counter++),
          child: Text('Count: $_counter'),
        ),
      ],
    );
  }
}

// CORRECT: Extract expensive widget
class GoodParent extends StatefulWidget {
  @override
  State<GoodParent> createState() => _GoodParentState();
}

class _GoodParentState extends State<GoodParent> {
  int _counter = 0;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const ExpensiveWidget(), // Doesn't rebuild
        ElevatedButton(
          onPressed: () => setState(() => _counter++),
          child: Text('Count: $_counter'),
        ),
      ],
    );
  }
}
```

### Use Builder for Scope

```dart
// WRONG: Entire widget rebuilds
class BadWidget extends StatefulWidget {
  @override
  State<BadWidget> createState() => _BadWidgetState();
}

class _BadWidgetState extends State<BadWidget> {
  int _counter = 0;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ExpensiveWidget(),
        Builder(
          builder: (context) {
            return Text('Count: $_counter'); // Only this rebuilds
          },
        ),
        ElevatedButton(
          onPressed: () => setState(() => _counter++),
          child: Text('Increment'),
        ),
      ],
    );
  }
}
```

## RepaintBoundary

RepaintBoundary creates a new layer for expensive paint operations.

### When to Use

- Expensive custom paint operations
- Animations that don't affect other widgets
- Large lists with complex items

### Pattern: Animated List Item

```dart
class AnimatedListItem extends StatefulWidget {
  final String title;

  const AnimatedListItem({required this.title});

  @override
  State<AnimatedListItem> createState() => _AnimatedListItemState();
}

class _AnimatedListItemState extends State<AnimatedListItem>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(seconds: 1),
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: ScaleTransition(
        scale: Tween<double>(begin: 0.9, end: 1.1).animate(_controller),
        child: ListTile(title: Text(title)),
      ),
    );
  }
}
```

## Build Method Optimization

### Don't Do Heavy Work in build()

```dart
// WRONG: Heavy computation in build()
class BadWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final expensiveData = _computeExpensiveData(); // Called every rebuild!
    return Text(expensiveData);
  }

  String _computeExpensiveData() {
    // Expensive operation
    return 'data';
  }
}

// CORRECT: Compute in constructor or cache
class GoodWidget extends StatelessWidget {
  final String data;

  const GoodWidget({required this.data});

  @override
  Widget build(BuildContext context) {
    return Text(data);
  }
}
```

### Cache Expensive Computations

```dart
class CachedComputationWidget extends StatefulWidget {
  final List<int> numbers;

  const CachedComputationWidget({required this.numbers});

  @override
  State<CachedComputationWidget> createState() =>
      _CachedComputationWidgetState();
}

class _CachedComputationWidgetState extends State<CachedComputationWidget> {
  late int _cachedSum;
  late List<int> _cachedNumbers;

  @override
  void initState() {
    super.initState();
    _cachedNumbers = widget.numbers;
    _cachedSum = _computeSum(widget.numbers);
  }

  @override
  void didUpdateWidget(CachedComputationWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.numbers != widget.numbers) {
      _cachedNumbers = widget.numbers;
      _cachedSum = _computeSum(widget.numbers);
    }
  }

  int _computeSum(List<int> numbers) {
    return numbers.fold(0, (a, b) => a + b);
  }

  @override
  Widget build(BuildContext context) {
    return Text('Sum: $_cachedSum');
  }
}
```

## Memory Profiling

### Using DevTools

1. Open DevTools: `flutter pub global run devtools`
2. Go to Memory tab
3. Take heap snapshots before and after operations
4. Look for memory leaks (objects not being garbage collected)

### Common Memory Leaks

```dart
// WRONG: Listener not removed
class BadListener extends StatefulWidget {
  @override
  State<BadListener> createState() => _BadListenerState();
}

class _BadListenerState extends State<BadListener> {
  late StreamSubscription _subscription;

  @override
  void initState() {
    super.initState();
    _subscription = DataService.stream().listen((_) {});
    // Never canceled!
  }

  @override
  Widget build(BuildContext context) {
    return Text('Listening');
  }
}

// CORRECT: Listener removed in dispose
class GoodListener extends StatefulWidget {
  @override
  State<GoodListener> createState() => _GoodListenerState();
}

class _GoodListenerState extends State<GoodListener> {
  late StreamSubscription _subscription;

  @override
  void initState() {
    super.initState();
    _subscription = DataService.stream().listen((_) {});
  }

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Text('Listening');
  }
}
```

## Profiling with DevTools

### Frame Rate Analysis

```dart
// Enable performance overlay
void main() {
  debugPrintBeginFrameBanner = true;
  debugPrintEndFrameBanner = true;
  runApp(MyApp());
}
```

### Slow Frame Detection

```dart
// Log slow frames
void main() {
  Timeline.instantSync('App Start');
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    Timeline.instantSync('MyApp.build');
    return MaterialApp(home: Home());
  }
}
```

## Production Optimization Checklist

- [ ] All widgets use `const` constructors where possible
- [ ] Expensive widgets extracted to separate classes
- [ ] No heavy computation in `build()` methods
- [ ] All listeners/subscriptions canceled in `dispose()`
- [ ] Controllers disposed properly
- [ ] No memory leaks detected in DevTools
- [ ] Frame rate stays above 60 FPS (120 FPS on high-refresh displays)
- [ ] Slivers used for large scrollable lists
- [ ] RepaintBoundary used for expensive animations
- [ ] Images cached and optimized
- [ ] Unnecessary rebuilds eliminated

## Performance Anti-Patterns Summary

| Anti-Pattern | Problem | Solution |
|---|---|---|
| Non-const widgets | Recreated every rebuild | Use `const` constructors |
| Heavy build() | Slow frame rate | Move computation to initState |
| Uncanceled listeners | Memory leaks | Cancel in dispose() |
| Deep nesting | Complex layout | Flatten widget tree |
| Large lists without Sliver | Slow scrolling | Use CustomScrollView + Slivers |
| Expensive animations | Jank | Use RepaintBoundary |
| Storing BuildContext | Stale context | Use context in build/callbacks |
| GlobalKey overuse | Performance cost | Use sparingly |
