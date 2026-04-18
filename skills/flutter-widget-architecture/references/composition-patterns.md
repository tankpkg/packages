# Composition Patterns: Building Complex UIs Without Inheritance

Sources: Flutter design patterns, composition over inheritance principles, production architecture patterns

Covers: Widget extraction, builder patterns, dependency injection, and composable widget design.

## Composition Over Inheritance

The fundamental principle: build complex UIs by combining simple, focused widgets rather than creating deep inheritance hierarchies.

### Why Composition Wins

```dart
// WRONG: Inheritance creates tight coupling
class BaseButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;

  const BaseButton({
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

// Now you need a variant...
class PrimaryButton extends BaseButton {
  const PrimaryButton({
    required String label,
    required VoidCallback onPressed,
  }) : super(label: label, onPressed: onPressed);

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.blue,
      ),
      onPressed: onPressed,
      child: Text(label),
    );
  }
}

// And another variant...
class SecondaryButton extends BaseButton {
  // More code...
}

// CORRECT: Composition with parameters
class CustomButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final double? width;

  const CustomButton({
    required this.label,
    required this.onPressed,
    this.backgroundColor,
    this.foregroundColor,
    this.width,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: width,
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: backgroundColor,
          foregroundColor: foregroundColor,
        ),
        onPressed: onPressed,
        child: Text(label),
      ),
    );
  }
}

// Usage: Easy to create variants without inheritance
const CustomButton(
  label: 'Primary',
  onPressed: _handlePress,
  backgroundColor: Colors.blue,
)

const CustomButton(
  label: 'Secondary',
  onPressed: _handlePress,
  backgroundColor: Colors.grey,
)
```

## Widget Extraction

Extract complex widgets into separate classes for reusability and testability.

### Pattern: Extracting a Complex Widget

```dart
// WRONG: Everything in one build method
class UserProfileScreen extends StatefulWidget {
  final String userId;

  const UserProfileScreen({required this.userId});

  @override
  State<UserProfileScreen> createState() => _UserProfileScreenState();
}

class _UserProfileScreenState extends State<UserProfileScreen> {
  late User _user;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadUser();
  }

  Future<void> _loadUser() async {
    final user = await UserService.fetchUser(widget.userId);
    if (mounted) {
      setState(() {
        _user = user;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return CircularProgressIndicator();

    return Column(
      children: [
        // Header
        Container(
          padding: EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(
                backgroundImage: NetworkImage(_user.avatarUrl),
              ),
              SizedBox(width: 16),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(_user.name),
                  Text(_user.email),
                ],
              ),
            ],
          ),
        ),
        // Stats
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            Column(
              children: [
                Text('${_user.followers}'),
                Text('Followers'),
              ],
            ),
            Column(
              children: [
                Text('${_user.following}'),
                Text('Following'),
              ],
            ),
          ],
        ),
        // Bio
        Padding(
          padding: EdgeInsets.all(16),
          child: Text(_user.bio),
        ),
      ],
    );
  }
}

// CORRECT: Extract into separate widgets
class UserProfileScreen extends StatefulWidget {
  final String userId;

  const UserProfileScreen({required this.userId});

  @override
  State<UserProfileScreen> createState() => _UserProfileScreenState();
}

class _UserProfileScreenState extends State<UserProfileScreen> {
  late User _user;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadUser();
  }

  Future<void> _loadUser() async {
    final user = await UserService.fetchUser(widget.userId);
    if (mounted) {
      setState(() {
        _user = user;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return CircularProgressIndicator();

    return Column(
      children: [
        UserProfileHeader(user: _user),
        UserProfileStats(user: _user),
        UserProfileBio(user: _user),
      ],
    );
  }
}

class UserProfileHeader extends StatelessWidget {
  final User user;

  const UserProfileHeader({required this.user});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16),
      child: Row(
        children: [
          CircleAvatar(
            backgroundImage: NetworkImage(user.avatarUrl),
          ),
          SizedBox(width: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(user.name),
              Text(user.email),
            ],
          ),
        ],
      ),
    );
  }
}

class UserProfileStats extends StatelessWidget {
  final User user;

  const UserProfileStats({required this.user});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _StatColumn(count: user.followers, label: 'Followers'),
        _StatColumn(count: user.following, label: 'Following'),
      ],
    );
  }
}

class _StatColumn extends StatelessWidget {
  final int count;
  final String label;

  const _StatColumn({required this.count, required this.label});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text('$count'),
        Text(label),
      ],
    );
  }
}

class UserProfileBio extends StatelessWidget {
  final User user;

  const UserProfileBio({required this.user});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(16),
      child: Text(user.bio),
    );
  }
}
```

## Builder Pattern

Use builders to create widgets with complex configuration.

### Pattern: Dialog Builder

```dart
class DialogBuilder {
  final String title;
  final String message;
  final List<DialogAction> actions;
  final VoidCallback? onDismiss;

  const DialogBuilder({
    required this.title,
    required this.message,
    required this.actions,
    this.onDismiss,
  });

  Future<void> show(BuildContext context) {
    return showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          for (final action in actions)
            TextButton(
              onPressed: () {
                action.onPressed();
                Navigator.pop(context);
              },
              child: Text(action.label),
            ),
        ],
      ),
      barrierDismissible: onDismiss != null,
    ).then((_) => onDismiss?.call());
  }
}

class DialogAction {
  final String label;
  final VoidCallback onPressed;

  DialogAction({required this.label, required this.onPressed});
}

// Usage
DialogBuilder(
  title: 'Confirm',
  message: 'Are you sure?',
  actions: [
    DialogAction(label: 'Cancel', onPressed: () {}),
    DialogAction(label: 'OK', onPressed: () => _handleConfirm()),
  ],
).show(context);
```

## Dependency Injection

Pass dependencies through constructors rather than accessing them globally.

### Pattern: Service Injection

```dart
// WRONG: Global service access
class UserList extends StatefulWidget {
  @override
  State<UserList> createState() => _UserListState();
}

class _UserListState extends State<UserList> {
  late Future<List<User>> _users;

  @override
  void initState() {
    super.initState();
    _users = UserService.instance.fetchUsers(); // Global access
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<User>>(
      future: _users,
      builder: (context, snapshot) {
        if (snapshot.hasData) {
          return ListView(
            children: [
              for (final user in snapshot.data!)
                UserTile(user: user),
            ],
          );
        }
        return CircularProgressIndicator();
      },
    );
  }
}

// CORRECT: Inject service through constructor
class UserList extends StatefulWidget {
  final UserService userService;

  const UserList({required this.userService});

  @override
  State<UserList> createState() => _UserListState();
}

class _UserListState extends State<UserList> {
  late Future<List<User>> _users;

  @override
  void initState() {
    super.initState();
    _users = widget.userService.fetchUsers();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<User>>(
      future: _users,
      builder: (context, snapshot) {
        if (snapshot.hasData) {
          return ListView(
            children: [
              for (final user in snapshot.data!)
                UserTile(user: user),
            ],
          );
        }
        return CircularProgressIndicator();
      },
    );
  }
}

// Usage
UserList(userService: UserService())
```

## Composable Widget Patterns

### Pattern: Wrapper Widget

```dart
class PaddedContainer extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  final Color? backgroundColor;
  final BorderRadius? borderRadius;

  const PaddedContainer({
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.backgroundColor,
    this.borderRadius,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: borderRadius,
      ),
      child: child,
    );
  }
}

// Usage
PaddedContainer(
  padding: EdgeInsets.all(24),
  backgroundColor: Colors.grey[100],
  borderRadius: BorderRadius.circular(8),
  child: Text('Content'),
)
```

### Pattern: Conditional Wrapper

```dart
class ConditionalWrapper extends StatelessWidget {
  final Widget child;
  final bool condition;
  final Widget Function(Widget) wrapper;

  const ConditionalWrapper({
    required this.child,
    required this.condition,
    required this.wrapper,
  });

  @override
  Widget build(BuildContext context) {
    return condition ? wrapper(child) : child;
  }
}

// Usage
ConditionalWrapper(
  condition: isLoading,
  wrapper: (child) => Stack(
    children: [
      child,
      Positioned.fill(
        child: Container(
          color: Colors.black.withOpacity(0.3),
          child: Center(child: CircularProgressIndicator()),
        ),
      ),
    ],
  ),
  child: MyContent(),
)
```

### Pattern: Composable Form Field

```dart
class FormFieldWrapper extends StatelessWidget {
  final String label;
  final String? hint;
  final Widget child;
  final String? error;
  final bool required;

  const FormFieldWrapper({
    required this.label,
    required this.child,
    this.hint,
    this.error,
    this.required = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(label),
            if (required)
              Text('*', style: TextStyle(color: Colors.red)),
          ],
        ),
        SizedBox(height: 8),
        child,
        if (hint != null) ...[
          SizedBox(height: 4),
          Text(hint!, style: Theme.of(context).textTheme.bodySmall),
        ],
        if (error != null) ...[
          SizedBox(height: 4),
          Text(error!, style: TextStyle(color: Colors.red)),
        ],
      ],
    );
  }
}

// Usage
FormFieldWrapper(
  label: 'Email',
  hint: 'Enter your email',
  error: _emailError,
  required: true,
  child: TextField(
    decoration: InputDecoration(hintText: 'user@example.com'),
  ),
)
```

## Mixin Pattern

Use mixins to share behavior across unrelated widgets.

### Pattern: Loading State Mixin

```dart
mixin LoadingStateMixin<T extends StatefulWidget> on State<T> {
  bool _isLoading = false;

  bool get isLoading => _isLoading;

  Future<void> withLoading(Future<void> Function() callback) async {
    setState(() => _isLoading = true);
    try {
      await callback();
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }
}

// Usage
class MyForm extends StatefulWidget {
  @override
  State<MyForm> createState() => _MyFormState();
}

class _MyFormState extends State<MyForm> with LoadingStateMixin {
  void _handleSubmit() {
    withLoading(() async {
      await api.submit();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        TextField(),
        ElevatedButton(
          onPressed: isLoading ? null : _handleSubmit,
          child: isLoading ? CircularProgressIndicator() : Text('Submit'),
        ),
      ],
    );
  }
}
```

## Composition Best Practices

1. **Single Responsibility** — Each widget should do one thing well
2. **Immutability** — Widgets should be immutable configuration objects
3. **Composition Over Inheritance** — Combine widgets rather than subclass
4. **Dependency Injection** — Pass dependencies through constructors
5. **Extract Early** — Extract widgets when they become complex
6. **Use const** — Make constructors const for performance
7. **Testability** — Composable widgets are easier to test
