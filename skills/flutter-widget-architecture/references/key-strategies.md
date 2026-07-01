# Key Strategies: ValueKey, ObjectKey, GlobalKey, UniqueKey

Sources: Flutter framework source code, Element identity documentation, production list patterns

Covers: When to use each Key type, list reordering patterns, GlobalKey pitfalls, and performance implications.

## Understanding Keys and Element Identity

Keys tell Flutter which widget corresponds to which Element when the tree changes. Without keys, Flutter matches widgets by type and position.

### The Problem Without Keys

```dart
// Without keys: Flutter matches by position
class ItemList extends StatefulWidget {
  @override
  State<ItemList> createState() => _ItemListState();
}

class _ItemListState extends State<ItemList> {
  List<String> items = ['A', 'B', 'C'];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (final item in items)
          ItemWidget(item: item), // No key!
        ElevatedButton(
          onPressed: () {
            setState(() => items.insert(0, 'X'));
          },
          child: Text('Insert at start'),
        ),
      ],
    );
  }
}

class ItemWidget extends StatefulWidget {
  final String item;

  const ItemWidget({required this.item});

  @override
  State<ItemWidget> createState() => _ItemWidgetState();
}

class _ItemWidgetState extends State<ItemWidget> {
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.item);
  }

  @override
  Widget build(BuildContext context) {
    return TextField(controller: _controller);
  }
}

// Problem: When 'X' is inserted at start, Flutter reuses the first Element
// The first TextField still has 'A' in its controller, but now displays 'X'
// State is mismatched with widget!
```

## ValueKey

Use ValueKey when you have stable, comparable data (IDs, unique strings).

### When to Use

- List items with unique IDs: `ValueKey(item.id)`
- Form fields with stable identifiers
- Any widget where you have a unique, comparable value
- Most common key type in production

### Pattern: List with ValueKey

```dart
class UserList extends StatefulWidget {
  @override
  State<UserList> createState() => _UserListState();
}

class _UserListState extends State<UserList> {
  List<User> users = [
    User(id: 1, name: 'Alice'),
    User(id: 2, name: 'Bob'),
    User(id: 3, name: 'Charlie'),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (final user in users)
          UserCard(
            key: ValueKey(user.id), // Stable ID
            user: user,
            onDelete: () {
              setState(() => users.removeWhere((u) => u.id == user.id));
            },
          ),
        ElevatedButton(
          onPressed: () {
            setState(() {
              users.insert(0, User(id: 0, name: 'New User'));
            });
          },
          child: Text('Add user'),
        ),
      ],
    );
  }
}

class UserCard extends StatefulWidget {
  final User user;
  final VoidCallback onDelete;

  const UserCard({
    required Key key,
    required this.user,
    required this.onDelete,
  }) : super(key: key);

  @override
  State<UserCard> createState() => _UserCardState();
}

class _UserCardState extends State<UserCard> {
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.user.name);
  }

  @override
  void didUpdateWidget(UserCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Update controller if user changed
    if (oldWidget.user.id != widget.user.id) {
      _controller.text = widget.user.name;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                decoration: InputDecoration(labelText: 'Name'),
              ),
            ),
            IconButton(
              icon: Icon(Icons.delete),
              onPressed: widget.onDelete,
            ),
          ],
        ),
      ),
    );
  }
}

class User {
  final int id;
  final String name;

  User({required this.id, required this.name});
}
```

### Anti-Pattern: Using Index as Key

```dart
// WRONG: Index changes when list is reordered
for (int i = 0; i < items.length; i++)
  ItemWidget(key: ValueKey(i), item: items[i])

// CORRECT: Use stable ID
for (final item in items)
  ItemWidget(key: ValueKey(item.id), item: item)
```

## ObjectKey

Use ObjectKey when object identity matters more than value equality.

### When to Use

- Objects that don't implement `==` and `hashCode` properly
- When you want to track the exact object instance, not its value
- Rarely needed in production (ValueKey is usually better)

### Pattern: ObjectKey with Custom Objects

```dart
class DataItem {
  final String id;
  final String name;

  DataItem({required this.id, required this.name});
  
  // Note: No custom == or hashCode
}

class DataList extends StatefulWidget {
  @override
  State<DataList> createState() => _DataListState();
}

class _DataListState extends State<DataList> {
  List<DataItem> items = [
    DataItem(id: '1', name: 'Item 1'),
    DataItem(id: '2', name: 'Item 2'),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (final item in items)
          DataItemWidget(
            key: ObjectKey(item), // Track object instance
            item: item,
          ),
      ],
    );
  }
}

class DataItemWidget extends StatefulWidget {
  final DataItem item;

  const DataItemWidget({required Key key, required this.item})
      : super(key: key);

  @override
  State<DataItemWidget> createState() => _DataItemWidgetState();
}

class _DataItemWidgetState extends State<DataItemWidget> {
  @override
  Widget build(BuildContext context) {
    return ListTile(title: Text(widget.item.name));
  }
}
```

## GlobalKey

Use GlobalKey to access State from outside the widget tree or to preserve state across tree changes.

### When to Use

- Form validation: `GlobalKey<FormState>()`
- Accessing State methods from parent widgets
- Preserving state when moving widgets between branches
- Rarely needed; usually indicates design issues

### Important: GlobalKey Performance Cost

GlobalKey is expensive because it maintains a global registry. Use sparingly.

### Pattern: Form Validation with GlobalKey

```dart
class LoginScreen extends StatefulWidget {
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();

  void _handleSubmit() {
    if (_formKey.currentState!.validate()) {
      _formKey.currentState!.save();
      // Submit form
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        LoginForm(key: _formKey),
        ElevatedButton(
          onPressed: _handleSubmit,
          child: Text('Login'),
        ),
      ],
    );
  }
}

class LoginForm extends StatefulWidget {
  const LoginForm({required Key key}) : super(key: key);

  @override
  State<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends State<LoginForm> {
  final _formKey = GlobalKey<FormState>();
  String? _email;
  String? _password;

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          TextFormField(
            decoration: InputDecoration(labelText: 'Email'),
            validator: (value) {
              if (value?.isEmpty ?? true) return 'Email required';
              return null;
            },
            onSaved: (value) => _email = value,
          ),
          TextFormField(
            decoration: InputDecoration(labelText: 'Password'),
            obscureText: true,
            validator: (value) {
              if (value?.isEmpty ?? true) return 'Password required';
              return null;
            },
            onSaved: (value) => _password = value,
          ),
        ],
      ),
    );
  }
}
```

### Pattern: Accessing State Methods with GlobalKey

```dart
class AnimatedBox extends StatefulWidget {
  const AnimatedBox({required Key key}) : super(key: key);

  @override
  State<AnimatedBox> createState() => _AnimatedBoxState();
}

class _AnimatedBoxState extends State<AnimatedBox>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(seconds: 1),
      vsync: this,
    );
  }

  void play() => _controller.forward();
  void stop() => _controller.stop();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: Tween<double>(begin: 1.0, end: 2.0).animate(_controller),
      child: Container(width: 100, height: 100, color: Colors.blue),
    );
  }
}

class ControlPanel extends StatefulWidget {
  @override
  State<ControlPanel> createState() => _ControlPanelState();
}

class _ControlPanelState extends State<ControlPanel> {
  final _boxKey = GlobalKey<_AnimatedBoxState>();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        AnimatedBox(key: _boxKey),
        Row(
          children: [
            ElevatedButton(
              onPressed: () => _boxKey.currentState?.play(),
              child: Text('Play'),
            ),
            ElevatedButton(
              onPressed: () => _boxKey.currentState?.stop(),
              child: Text('Stop'),
            ),
          ],
        ),
      ],
    );
  }
}
```

### Anti-Pattern: Storing GlobalKey in State

```dart
// WRONG: GlobalKey stored in State
class BadWidget extends State<MyWidget> {
  late GlobalKey<FormState> _formKey;

  @override
  void initState() {
    super.initState();
    _formKey = GlobalKey<FormState>(); // Created in initState
  }

  // Problem: If State is recreated, old GlobalKey is orphaned
}

// CORRECT: GlobalKey as final field
class GoodWidget extends State<MyWidget> {
  final _formKey = GlobalKey<FormState>();

  // GlobalKey is created once and reused
}
```

## UniqueKey

Use UniqueKey to force a rebuild every time the widget is created.

### When to Use

- Rarely needed in production
- When you need guaranteed uniqueness
- When you want to force a widget to rebuild even if its properties haven't changed

### Pattern: Forcing Rebuild

```dart
class RefreshableWidget extends StatefulWidget {
  @override
  State<RefreshableWidget> createState() => _RefreshableWidgetState();
}

class _RefreshableWidgetState extends State<RefreshableWidget> {
  int _refreshCount = 0;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Force rebuild by changing key
        ExpensiveWidget(key: UniqueKey()),
        ElevatedButton(
          onPressed: () => setState(() => _refreshCount++),
          child: Text('Refresh'),
        ),
      ],
    );
  }
}

class ExpensiveWidget extends StatefulWidget {
  const ExpensiveWidget({required Key key}) : super(key: key);

  @override
  State<ExpensiveWidget> createState() => _ExpensiveWidgetState();
}

class _ExpensiveWidgetState extends State<ExpensiveWidget> {
  @override
  void initState() {
    super.initState();
    print('ExpensiveWidget initialized'); // Printed every time
  }

  @override
  Widget build(BuildContext context) {
    return Text('Expensive widget');
  }
}
```

## Key Comparison Table

| Key Type | Use Case | Performance | Stability |
|----------|----------|-------------|-----------|
| ValueKey | Stable IDs, most common | Good | Excellent |
| ObjectKey | Object identity | Good | Good |
| GlobalKey | Form validation, state access | Poor (expensive) | Excellent |
| UniqueKey | Force rebuild | Good | Poor (always unique) |
| No Key | Static lists, single children | Best | N/A |

## Production Patterns

### Pattern: Reorderable List with Keys

```dart
class ReorderableUserList extends StatefulWidget {
  @override
  State<ReorderableUserList> createState() => _ReorderableUserListState();
}

class _ReorderableUserListState extends State<ReorderableUserList> {
  List<User> users = [
    User(id: 1, name: 'Alice'),
    User(id: 2, name: 'Bob'),
    User(id: 3, name: 'Charlie'),
  ];

  @override
  Widget build(BuildContext context) {
    return ReorderableListView(
      onReorder: (oldIndex, newIndex) {
        setState(() {
          if (newIndex > oldIndex) newIndex -= 1;
          final user = users.removeAt(oldIndex);
          users.insert(newIndex, user);
        });
      },
      children: [
        for (final user in users)
          UserCard(
            key: ValueKey(user.id), // Essential for reordering
            user: user,
          ),
      ],
    );
  }
}
```

### Pattern: Dismissible List with Keys

```dart
class DismissibleUserList extends StatefulWidget {
  @override
  State<DismissibleUserList> createState() => _DismissibleUserListState();
}

class _DismissibleUserListState extends State<DismissibleUserList> {
  List<User> users = [
    User(id: 1, name: 'Alice'),
    User(id: 2, name: 'Bob'),
  ];

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: users.length,
      itemBuilder: (context, index) {
        final user = users[index];
        return Dismissible(
          key: ValueKey(user.id), // Essential for dismissible
          onDismissed: (direction) {
            setState(() => users.removeAt(index));
          },
          child: UserCard(user: user),
        );
      },
    );
  }
}
```

### Pattern: Animated List with Keys

```dart
class AnimatedUserList extends StatefulWidget {
  @override
  State<AnimatedUserList> createState() => _AnimatedUserListState();
}

class _AnimatedUserListState extends State<AnimatedUserList> {
  final _listKey = GlobalKey<AnimatedListState>();
  List<User> users = [
    User(id: 1, name: 'Alice'),
    User(id: 2, name: 'Bob'),
  ];

  void _addUser(User user) {
    users.add(user);
    _listKey.currentState?.insertItem(users.length - 1);
  }

  void _removeUser(int index) {
    final user = users.removeAt(index);
    _listKey.currentState?.removeItem(
      index,
      (context, animation) => UserCard(user: user),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedList(
      key: _listKey,
      initialItemCount: users.length,
      itemBuilder: (context, index, animation) {
        return SlideTransition(
          position: animation.drive(
            Tween<Offset>(begin: Offset(-1, 0), end: Offset.zero),
          ),
          child: UserCard(
            key: ValueKey(users[index].id),
            user: users[index],
          ),
        );
      },
    );
  }
}
```
