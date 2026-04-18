# Widget Lifecycle: initState, didChangeDependencies, build, dispose

Sources: Flutter framework source code, official State lifecycle documentation, production debugging patterns

Covers: Complete State lifecycle with timing, when each method is called, and production patterns.

## State Lifecycle Overview

The State lifecycle has distinct phases:

```
1. initState()
   ↓
2. didChangeDependencies()
   ↓
3. build() ← Called multiple times
   ↓
4. didUpdateWidget() ← Only if parent rebuilds with new widget
   ↓
5. deactivate()
   ↓
6. dispose()
```

## initState()

Called once when the State is created, before the first build.

### When to Use

- Initialize controllers (TextEditingController, AnimationController)
- Load initial data from storage or API
- Set up listeners or subscriptions
- Initialize mutable state variables

### Important Rules

- Must call `super.initState()` first
- Cannot use `async/await` directly; use `Future.then()` or create async method
- `mounted` is always true at this point
- `context` is available and valid

### Pattern: Initializing Controllers

```dart
class MyForm extends StatefulWidget {
  @override
  State<MyForm> createState() => _MyFormState();
}

class _MyFormState extends State<MyForm> {
  late TextEditingController _nameController;
  late TextEditingController _emailController;
  late FocusNode _nameFocus;
  late FocusNode _emailFocus;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController();
    _emailController = TextEditingController();
    _nameFocus = FocusNode();
    _emailFocus = FocusNode();
    
    // Add listeners
    _nameController.addListener(_onNameChanged);
  }

  void _onNameChanged() {
    print('Name: ${_nameController.text}');
  }

  @override
  void dispose() {
    _nameController.removeListener(_onNameChanged);
    _nameController.dispose();
    _emailController.dispose();
    _nameFocus.dispose();
    _emailFocus.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        TextField(controller: _nameController, focusNode: _nameFocus),
        TextField(controller: _emailController, focusNode: _emailFocus),
      ],
    );
  }
}
```

### Pattern: Loading Data in initState

```dart
class UserProfile extends StatefulWidget {
  final String userId;

  const UserProfile({required this.userId});

  @override
  State<UserProfile> createState() => _UserProfileState();
}

class _UserProfileState extends State<UserProfile> {
  User? _user;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadUser();
  }

  Future<void> _loadUser() async {
    try {
      final user = await UserService.fetchUser(widget.userId);
      if (mounted) {
        setState(() {
          _user = user;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return CircularProgressIndicator();
    if (_error != null) return Text('Error: $_error');
    return Text(_user?.name ?? '');
  }
}
```

## didChangeDependencies()

Called when the widget's dependencies change. This includes:
- First time after initState()
- When an InheritedWidget that this widget depends on changes
- When the widget is moved in the tree

### When to Use

- Accessing InheritedWidgets (Theme, MediaQuery, etc.)
- Reacting to changes in InheritedWidget data
- Expensive operations that depend on context data

### Important Rules

- Called after initState() and before build()
- Can be called multiple times
- Must call `super.didChangeDependencies()`
- `context` is available and valid

### Pattern: Reacting to Theme Changes

```dart
class ThemeAwareWidget extends StatefulWidget {
  @override
  State<ThemeAwareWidget> createState() => _ThemeAwareWidgetState();
}

class _ThemeAwareWidgetState extends State<ThemeAwareWidget> {
  late Color _primaryColor;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Called when Theme changes
    _primaryColor = Theme.of(context).primaryColor;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: _primaryColor,
      child: Text('Themed widget'),
    );
  }
}
```

### Pattern: Reacting to Widget Parameter Changes

```dart
class DataDisplay extends StatefulWidget {
  final String dataId;

  const DataDisplay({required this.dataId});

  @override
  State<DataDisplay> createState() => _DataDisplayState();
}

class _DataDisplayState extends State<DataDisplay> {
  late String _cachedDataId;
  late Future<String> _dataFuture;

  @override
  void initState() {
    super.initState();
    _cachedDataId = widget.dataId;
    _dataFuture = _loadData(widget.dataId);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Reload if dataId changed
    if (widget.dataId != _cachedDataId) {
      _cachedDataId = widget.dataId;
      _dataFuture = _loadData(widget.dataId);
    }
  }

  Future<String> _loadData(String id) async {
    return await DataService.fetch(id);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<String>(
      future: _dataFuture,
      builder: (context, snapshot) {
        if (snapshot.hasData) return Text(snapshot.data!);
        if (snapshot.hasError) return Text('Error: ${snapshot.error}');
        return CircularProgressIndicator();
      },
    );
  }
}
```

## didUpdateWidget()

Called when the parent widget rebuilds with a new widget instance. The old widget is passed as a parameter.

### When to Use

- Comparing old and new widget properties
- Updating state based on widget parameter changes
- Canceling old subscriptions and creating new ones

### Important Rules

- Only called if the parent rebuilds with a new widget
- Must call `super.didUpdateWidget(oldWidget)`
- `context` is available and valid
- Called before build()

### Pattern: Updating on Widget Parameter Change

```dart
class DataListener extends StatefulWidget {
  final String dataId;
  final Function(String) onDataLoaded;

  const DataListener({
    required this.dataId,
    required this.onDataLoaded,
  });

  @override
  State<DataListener> createState() => _DataListenerState();
}

class _DataListenerState extends State<DataListener> {
  late StreamSubscription _subscription;

  @override
  void initState() {
    super.initState();
    _subscribeToData(widget.dataId);
  }

  @override
  void didUpdateWidget(DataListener oldWidget) {
    super.didUpdateWidget(oldWidget);
    // If dataId changed, update subscription
    if (oldWidget.dataId != widget.dataId) {
      _subscription.cancel();
      _subscribeToData(widget.dataId);
    }
  }

  void _subscribeToData(String dataId) {
    _subscription = DataService.stream(dataId).listen((data) {
      widget.onDataLoaded(data);
    });
  }

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox.shrink(); // This widget doesn't render anything
  }
}
```

## build()

Called to create the widget tree. Can be called many times.

### When to Use

- Creating the UI based on current state
- Accessing context to get Theme, MediaQuery, etc.
- Composing child widgets

### Important Rules

- Must return a Widget
- Should be pure (no side effects)
- Can be called multiple times per frame
- Never call setState() in build()
- Never access mutable state that might change

### Anti-Pattern: Side Effects in build()

```dart
// WRONG: Side effects in build()
class BadWidget extends State<MyWidget> {
  @override
  Widget build(BuildContext context) {
    print('Building'); // Called multiple times!
    _saveToDatabase(); // Side effect!
    return Text('Hello');
  }
}

// CORRECT: Side effects in initState or didChangeDependencies
class GoodWidget extends State<MyWidget> {
  @override
  void initState() {
    super.initState();
    _saveToDatabase(); // Called once
  }

  @override
  Widget build(BuildContext context) {
    return Text('Hello');
  }
}
```

## deactivate()

Called when the State is removed from the tree but might be reinserted.

### When to Use

- Pausing animations or timers
- Stopping expensive operations that can be resumed
- Cleaning up resources that might be needed again

### Important Rules

- Must call `super.deactivate()`
- Called before dispose()
- `context` is still available
- The widget might be reinserted into the tree

### Pattern: Pausing Animations

```dart
class AnimatedCounter extends StatefulWidget {
  @override
  State<AnimatedCounter> createState() => _AnimatedCounterState();
}

class _AnimatedCounterState extends State<AnimatedCounter>
    with TickerProviderStateMixin {
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
  void deactivate() {
    _controller.stop(); // Pause animation
    super.deactivate();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: Tween<double>(begin: 0.5, end: 1.0).animate(_controller),
      child: Text('Animated'),
    );
  }
}
```

## dispose()

Called when the State is permanently removed from the tree.

### When to Use

- Disposing controllers (TextEditingController, AnimationController)
- Canceling subscriptions and streams
- Releasing resources (file handles, database connections)
- Removing listeners

### Important Rules

- Must call `super.dispose()` last
- Called only once
- `context` is still available but should not be used
- Never call setState() in dispose()

### Pattern: Complete Resource Cleanup

```dart
class ResourceManager extends StatefulWidget {
  @override
  State<ResourceManager> createState() => _ResourceManagerState();
}

class _ResourceManagerState extends State<ResourceManager> {
  late TextEditingController _controller;
  late AnimationController _animController;
  late StreamSubscription _subscription;
  late Timer _timer;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _animController = AnimationController(
      duration: Duration(seconds: 1),
      vsync: this,
    );
    _subscription = DataService.stream().listen((_) {});
    _timer = Timer.periodic(Duration(seconds: 1), (_) {});
  }

  @override
  void dispose() {
    // Dispose in reverse order of creation
    _timer.cancel();
    _subscription.cancel();
    _animController.dispose();
    _controller.dispose();
    super.dispose(); // Call last
  }

  @override
  Widget build(BuildContext context) {
    return Text('Resource manager');
  }
}
```

## Lifecycle Timing Diagram

```
Widget Creation
    ↓
initState() ← Initialize once
    ↓
didChangeDependencies() ← React to InheritedWidget changes
    ↓
build() ← Create UI (can be called many times)
    ↓
[Parent rebuilds with new widget?]
    ├─ Yes → didUpdateWidget() → build()
    └─ No → [Widget removed from tree?]
           ├─ Yes → deactivate() → dispose()
           └─ No → [Wait for next rebuild]
```

## Common Patterns

### Pattern: Debounced Search

```dart
class SearchField extends StatefulWidget {
  final Function(String) onSearch;

  const SearchField({required this.onSearch});

  @override
  State<SearchField> createState() => _SearchFieldState();
}

class _SearchFieldState extends State<SearchField> {
  late TextEditingController _controller;
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _controller.addListener(_onSearchChanged);
  }

  void _onSearchChanged() {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(Duration(milliseconds: 500), () {
      widget.onSearch(_controller.text);
    });
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _controller.removeListener(_onSearchChanged);
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: _controller,
      decoration: InputDecoration(hintText: 'Search...'),
    );
  }
}
```

### Pattern: Mounted Check

Always check `mounted` before calling `setState()` in async callbacks:

```dart
Future<void> _loadData() async {
  try {
    final data = await api.fetchData();
    if (mounted) { // Check if widget is still in tree
      setState(() => _data = data);
    }
  } catch (e) {
    if (mounted) {
      setState(() => _error = e.toString());
    }
  }
}
```

### Pattern: Lifecycle Logging

For debugging, log lifecycle methods:

```dart
class DebugState extends State<MyWidget> {
  @override
  void initState() {
    super.initState();
    print('${runtimeType}.initState');
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    print('${runtimeType}.didChangeDependencies');
  }

  @override
  void didUpdateWidget(MyWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    print('${runtimeType}.didUpdateWidget');
  }

  @override
  void deactivate() {
    print('${runtimeType}.deactivate');
    super.deactivate();
  }

  @override
  void dispose() {
    print('${runtimeType}.dispose');
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    print('${runtimeType}.build');
    return SizedBox.shrink();
  }
}
```
