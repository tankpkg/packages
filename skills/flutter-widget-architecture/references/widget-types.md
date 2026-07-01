# Widget Types: StatelessWidget, StatefulWidget, InheritedWidget

Sources: Flutter framework source code, official documentation, Google I/O talks on widget architecture

Covers: Detailed comparison of widget types with production patterns, when to use each, and common pitfalls.

## StatelessWidget

A StatelessWidget is immutable and has no mutable state. It's the simplest widget type and should be your default choice.

### When to Use

- UI that doesn't change based on internal state
- Configuration objects (buttons, text, containers)
- Presentational components that receive all data via constructor parameters
- Widgets that only rebuild when their parent rebuilds

### Pattern: Simple Presentational Widget

```dart
class UserCard extends StatelessWidget {
  final String name;
  final String email;
  final VoidCallback onTap;

  const UserCard({
    required this.name,
    required this.email,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(name, style: Theme.of(context).textTheme.titleLarge),
              SizedBox(height: 8),
              Text(email, style: Theme.of(context).textTheme.bodyMedium),
            ],
          ),
        ),
      ),
    );
  }
}
```

### Anti-Pattern: Doing Too Much in build()

```dart
// WRONG: Heavy computation in build()
class BadWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final expensiveData = computeExpensiveData(); // Called every rebuild!
    return Text(expensiveData);
  }
}

// CORRECT: Compute in constructor or pass as parameter
class GoodWidget extends StatelessWidget {
  final String data;
  
  const GoodWidget({required this.data});
  
  @override
  Widget build(BuildContext context) {
    return Text(data);
  }
}
```

## StatefulWidget

A StatefulWidget manages mutable state via a State class. The State object persists across rebuilds, allowing you to store and modify data.

### When to Use

- UI that changes based on user interaction (form inputs, toggles, counters)
- Widgets that need to manage animations or timers
- Widgets that need to initialize resources (API calls, database queries)
- Any widget where `setState()` is needed to trigger rebuilds

### Pattern: Form with Validation

```dart
class LoginForm extends StatefulWidget {
  final Function(String email, String password) onSubmit;

  const LoginForm({required this.onSubmit});

  @override
  State<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends State<LoginForm> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _emailController;
  late TextEditingController _passwordController;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _emailController = TextEditingController();
    _passwordController = TextEditingController();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _handleSubmit() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      try {
        await widget.onSubmit(
          _emailController.text,
          _passwordController.text,
        );
      } finally {
        if (mounted) setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          TextFormField(
            controller: _emailController,
            decoration: InputDecoration(labelText: 'Email'),
            validator: (value) {
              if (value?.isEmpty ?? true) return 'Email required';
              if (!value!.contains('@')) return 'Invalid email';
              return null;
            },
          ),
          SizedBox(height: 16),
          TextFormField(
            controller: _passwordController,
            decoration: InputDecoration(labelText: 'Password'),
            obscureText: true,
            validator: (value) {
              if (value?.isEmpty ?? true) return 'Password required';
              if (value!.length < 8) return 'Min 8 characters';
              return null;
            },
          ),
          SizedBox(height: 24),
          ElevatedButton(
            onPressed: _isLoading ? null : _handleSubmit,
            child: _isLoading
                ? SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text('Login'),
          ),
        ],
      ),
    );
  }
}
```

### Anti-Pattern: Storing BuildContext in State

```dart
// WRONG: BuildContext stored and used later
class BadState extends State<MyWidget> {
  late BuildContext _savedContext;

  @override
  void initState() {
    super.initState();
    _savedContext = context; // WRONG!
  }

  void _showDialog() {
    showDialog(context: _savedContext, ...); // May be stale
  }
}

// CORRECT: Use context directly in build or callbacks
class GoodState extends State<MyWidget> {
  void _showDialog() {
    showDialog(context: context, ...); // Always current
  }
}
```

## InheritedWidget

An InheritedWidget efficiently broadcasts data to all descendants in the widget tree. When data changes, only widgets that depend on it rebuild.

### When to Use

- Sharing read-only data across many descendants (Theme, Locale, AppState)
- Avoiding prop drilling (passing data through many intermediate widgets)
- Efficient updates: only dependents rebuild, not the entire subtree
- Low-level state management (higher-level packages like Provider wrap this)

### Pattern: Theme Provider

```dart
class AppTheme {
  final Color primaryColor;
  final Color accentColor;
  final TextTheme textTheme;

  const AppTheme({
    required this.primaryColor,
    required this.accentColor,
    required this.textTheme,
  });
}

class AppThemeProvider extends InheritedWidget {
  final AppTheme theme;

  const AppThemeProvider({
    required this.theme,
    required Widget child,
  }) : super(child: child);

  static AppTheme of(BuildContext context) {
    final provider = context.dependOnInheritedWidgetOfExactType<AppThemeProvider>();
    if (provider == null) {
      throw FlutterError('AppThemeProvider not found in context');
    }
    return provider.theme;
  }

  @override
  bool updateShouldNotify(AppThemeProvider oldWidget) {
    return theme != oldWidget.theme;
  }
}

// Usage
class MyButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final theme = AppThemeProvider.of(context);
    return ElevatedButton(
      style: ElevatedButton.styleFrom(
        backgroundColor: theme.primaryColor,
      ),
      onPressed: () {},
      child: Text('Press me'),
    );
  }
}
```

### Pattern: Mutable State with InheritedWidget

```dart
class AppState {
  final String userId;
  final bool isLoggedIn;
  final List<String> favorites;

  AppState({
    required this.userId,
    required this.isLoggedIn,
    required this.favorites,
  });

  AppState copyWith({
    String? userId,
    bool? isLoggedIn,
    List<String>? favorites,
  }) {
    return AppState(
      userId: userId ?? this.userId,
      isLoggedIn: isLoggedIn ?? this.isLoggedIn,
      favorites: favorites ?? this.favorites,
    );
  }
}

class AppStateProvider extends InheritedWidget {
  final AppState state;
  final Function(AppState) onStateChanged;

  const AppStateProvider({
    required this.state,
    required this.onStateChanged,
    required Widget child,
  }) : super(child: child);

  static AppStateProvider of(BuildContext context) {
    final provider = context.dependOnInheritedWidgetOfExactType<AppStateProvider>();
    if (provider == null) {
      throw FlutterError('AppStateProvider not found');
    }
    return provider;
  }

  @override
  bool updateShouldNotify(AppStateProvider oldWidget) {
    return state != oldWidget.state;
  }
}

// Usage in StatefulWidget
class AppRoot extends StatefulWidget {
  @override
  State<AppRoot> createState() => _AppRootState();
}

class _AppRootState extends State<AppRoot> {
  late AppState _state;

  @override
  void initState() {
    super.initState();
    _state = AppState(userId: '', isLoggedIn: false, favorites: []);
  }

  void _updateState(AppState newState) {
    setState(() => _state = newState);
  }

  @override
  Widget build(BuildContext context) {
    return AppStateProvider(
      state: _state,
      onStateChanged: _updateState,
      child: MaterialApp(
        home: HomeScreen(),
      ),
    );
  }
}

// Accessing state in descendants
class FavoriteButton extends StatelessWidget {
  final String itemId;

  const FavoriteButton({required this.itemId});

  @override
  Widget build(BuildContext context) {
    final provider = AppStateProvider.of(context);
    final isFavorited = provider.state.favorites.contains(itemId);

    return IconButton(
      icon: Icon(isFavorited ? Icons.favorite : Icons.favorite_border),
      onPressed: () {
        final newFavorites = List<String>.from(provider.state.favorites);
        if (isFavorited) {
          newFavorites.remove(itemId);
        } else {
          newFavorites.add(itemId);
        }
        provider.onStateChanged(
          provider.state.copyWith(favorites: newFavorites),
        );
      },
    );
  }
}
```

## Builder Pattern

The Builder widget is a simple way to access BuildContext from a parent without creating a new widget class.

### When to Use

- Accessing Theme, MediaQuery, or other InheritedWidgets from a parent
- Avoiding unnecessary widget nesting
- Creating a new scope for InheritedWidget lookups

### Pattern: Accessing Theme

```dart
// Without Builder: Theme.of(context) may not find the theme
class BadWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // This context might not have MaterialApp as ancestor
    final theme = Theme.of(context);
    return Text('Hello');
  }
}

// With Builder: Guaranteed to find theme
class GoodWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Builder(
      builder: (context) {
        final theme = Theme.of(context); // Correct context
        return Text('Hello', style: TextStyle(color: theme.primaryColor));
      },
    );
  }
}
```

## Comparison Table

| Aspect | StatelessWidget | StatefulWidget | InheritedWidget |
|--------|-----------------|----------------|-----------------|
| Mutable State | No | Yes (in State) | No (immutable) |
| Lifecycle | None | Full (initState, dispose, etc.) | updateShouldNotify |
| Rebuild Trigger | Parent rebuild only | setState() or parent rebuild | updateShouldNotify returns true |
| Use Case | Static UI | Interactive UI | Shared data |
| Performance | Best | Good | Excellent for many dependents |
| Complexity | Low | Medium | Low-Medium |

## Production Patterns

### Combining StatefulWidget with InheritedWidget

For complex apps, use StatefulWidget to manage state and InheritedWidget to broadcast it:

```dart
class AppStateManager extends StatefulWidget {
  final Widget child;

  const AppStateManager({required this.child});

  @override
  State<AppStateManager> createState() => _AppStateManagerState();
}

class _AppStateManagerState extends State<AppStateManager> {
  late AppState _state;

  @override
  void initState() {
    super.initState();
    _loadState();
  }

  Future<void> _loadState() async {
    // Load from storage, API, etc.
    final state = AppState(userId: '', isLoggedIn: false, favorites: []);
    setState(() => _state = state);
  }

  void _updateState(AppState newState) {
    setState(() => _state = newState);
    // Persist to storage
    _persistState(newState);
  }

  Future<void> _persistState(AppState state) async {
    // Save to SharedPreferences, Hive, etc.
  }

  @override
  Widget build(BuildContext context) {
    return AppStateProvider(
      state: _state,
      onStateChanged: _updateState,
      child: widget.child,
    );
  }
}
```

### Using Provider Package (Recommended for Production)

For most production apps, use the `provider` package instead of raw InheritedWidget:

```dart
// Define state
class AppNotifier extends ChangeNotifier {
  String _userId = '';
  bool _isLoggedIn = false;
  List<String> _favorites = [];

  String get userId => _userId;
  bool get isLoggedIn => _isLoggedIn;
  List<String> get favorites => _favorites;

  void login(String userId) {
    _userId = userId;
    _isLoggedIn = true;
    notifyListeners();
  }

  void addFavorite(String itemId) {
    _favorites.add(itemId);
    notifyListeners();
  }
}

// Provide it
void main() {
  runApp(
    ChangeNotifierProvider(
      create: (_) => AppNotifier(),
      child: MyApp(),
    ),
  );
}

// Consume it
class FavoriteButton extends StatelessWidget {
  final String itemId;

  const FavoriteButton({required this.itemId});

  @override
  Widget build(BuildContext context) {
    final appNotifier = context.watch<AppNotifier>();
    final isFavorited = appNotifier.favorites.contains(itemId);

    return IconButton(
      icon: Icon(isFavorited ? Icons.favorite : Icons.favorite_border),
      onPressed: () => appNotifier.addFavorite(itemId),
    );
  }
}
```
