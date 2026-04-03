# Dart Patterns

Sources: Dart language specification (Dart 3.x, dart.dev 2025-2026), Effective Dart guide (dart.dev/effective-dart), Freezed package documentation, Dart API reference

Covers: null safety, sealed classes, records, pattern matching, extensions, mixins, Freezed code generation, and idiomatic Dart conventions.

## Null Safety

Dart's sound null safety guarantees that a non-nullable variable can never be `null` at runtime.

### Core Rules

| Type | Nullable? | Example |
|------|-----------|---------|
| `String` | No | Cannot be null, ever |
| `String?` | Yes | Can be null |
| `late String` | No, but deferred initialization | Must be assigned before first read |
| `required String name` | No, required named parameter | Caller must provide |

### Operators

```dart
String? name;

// Null-aware access
final length = name?.length;         // int? — null if name is null
final upper = name?.toUpperCase();   // String? — null if name is null

// Null coalescing
final display = name ?? 'Anonymous'; // String — fallback if null

// Null assertion (throws if null — avoid in production)
final forced = name!;               // String — throws TypeError if null

// Null-aware assignment
name ??= 'Default';                 // Assigns only if currently null

// Null-aware cascade
list?..add(1)..add(2);              // Skips cascade if list is null
```

### Late Variables

Use `late` for variables that are expensive to initialize or depend on runtime conditions:

```dart
class ApiService {
  late final HttpClient _client;

  void init(String baseUrl) {
    _client = HttpClient(baseUrl);
  }
}
```

Rules:
- `late final` — assigned once, then immutable. Use for dependency injection
- `late` (non-final) — assigned later, reassignable. Rare in practice
- Never use `late` as a substitute for proper null handling — if the variable might genuinely be absent, use `?`

## Sealed Classes

Sealed classes restrict which classes can extend or implement them. Combined with pattern matching, they enable exhaustive `switch` expressions — the compiler verifies every subtype is handled.

```dart
sealed class Result<T> {
  const Result();
}
class Success<T> extends Result<T> {
  final T data;
  const Success(this.data);
}
class Failure<T> extends Result<T> {
  final String message;
  final Exception? exception;
  const Failure(this.message, [this.exception]);
}
class Loading<T> extends Result<T> {
  const Loading();
}
```

### Exhaustive Switch

```dart
Widget buildResult(Result<User> result) {
  return switch (result) {
    Success(:final data) => UserProfile(user: data),
    Failure(:final message) => ErrorDisplay(message: message),
    Loading() => const CircularProgressIndicator(),
  };
  // Adding a new Result subtype causes a compile error here until handled
}
```

### Use Cases

| Use Case | Pattern |
|----------|---------|
| API response states (loading/data/error) | `sealed class AsyncState` |
| Navigation events | `sealed class NavigationEvent` |
| BLoC events and states | `sealed class AuthEvent`, `sealed class AuthState` |
| Form validation results | `sealed class ValidationResult` |
| Union types for config | `sealed class Environment` (dev/staging/prod) |

## Records

Records are anonymous, immutable, structural types for returning multiple values without creating a class.

```dart
// Named fields
(String name, int age) getUser() {
  return ('Alice', 30);
}

// Named record fields (preferred for readability)
({String name, int age}) getUserNamed() {
  return (name: 'Alice', age: 30);
}

// Destructuring
final (name, age) = getUser();
final (:name, :age) = getUserNamed();  // Shorthand destructuring
```

### When Records vs Classes

| Signal | Use Record | Use Class |
|--------|-----------|-----------|
| Returning multiple values from a function | Yes | Overkill |
| Temporary grouping (map key, cache key) | Yes | Overkill |
| Data model with behavior (methods) | No | Yes |
| Data model used in API serialization | No | Yes (with Freezed/json_serializable) |
| Need named constructors or factories | No | Yes |

Records are structural — two records with the same shape and values are equal:

```dart
final a = (name: 'Alice', age: 30);
final b = (name: 'Alice', age: 30);
assert(a == b); // true — structural equality
```

## Pattern Matching

Dart 3 patterns enable destructuring, type checking, and value extraction in `switch`, `if-case`, and variable declarations.

### Switch Expressions

```dart
// Return value from switch
final label = switch (status) {
  Status.active => 'Active',
  Status.inactive => 'Inactive',
  Status.suspended => 'Suspended',
};

// Guard clauses
String describe(num value) => switch (value) {
  < 0 => 'negative',
  == 0 => 'zero',
  > 0 && < 100 => 'small positive',
  >= 100 => 'large positive',
  _ => 'unknown',
};
```

### If-Case

```dart
final json = {'name': 'Alice', 'age': 30};

if (json case {'name': String name, 'age': int age}) {
  print('$name is $age years old');
}
```

### Object Destructuring

```dart
sealed class Shape {}
class Circle extends Shape { final double radius; Circle(this.radius); }
class Rectangle extends Shape { final double w, h; Rectangle(this.w, this.h); }

double area(Shape shape) => switch (shape) {
  Circle(:final radius) => 3.14159 * radius * radius,
  Rectangle(:final w, :final h) => w * h,
};
```

### List and Map Patterns

```dart
final list = [1, 2, 3, 4, 5];

// Destructure first and rest
if (list case [var first, ...var rest]) {
  print('First: $first, Rest: $rest');
}

// Map pattern
final config = {'debug': true, 'port': 8080};
if (config case {'debug': true, 'port': int port}) {
  print('Debug mode on port $port');
}
```

## Extensions

Add methods to existing types without modifying them:

```dart
extension StringX on String {
  String get capitalize => isEmpty ? '' : '${this[0].toUpperCase()}${substring(1)}';
  bool get isEmail => RegExp(r'^[\w-.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(this);
}

extension DateTimeX on DateTime {
  String get timeAgo {
    final diff = DateTime.now().difference(this);
    if (diff.inDays > 365) return '${diff.inDays ~/ 365}y ago';
    if (diff.inDays > 30) return '${diff.inDays ~/ 30}mo ago';
    if (diff.inDays > 0) return '${diff.inDays}d ago';
    if (diff.inHours > 0) return '${diff.inHours}h ago';
    if (diff.inMinutes > 0) return '${diff.inMinutes}m ago';
    return 'just now';
  }
}

extension ContextX on BuildContext {
  ThemeData get theme => Theme.of(this);
  TextTheme get textTheme => Theme.of(this).textTheme;
  ColorScheme get colorScheme => Theme.of(this).colorScheme;
  MediaQueryData get mediaQuery => MediaQuery.of(this);
  double get screenWidth => MediaQuery.sizeOf(this).width;
}
```

### Naming Convention

Name extension files `{type}_extensions.dart` and extension classes `{Type}X`:

```
lib/extensions/
  string_extensions.dart
  context_extensions.dart
  datetime_extensions.dart
```

## Mixins

Mixins add behavior to classes without inheritance hierarchy constraints:

```dart
mixin LoggableMixin {
  void log(String message) => print('[${runtimeType}] $message');
}

mixin ValidatableMixin {
  Map<String, String> validate();
  bool get isValid => validate().isEmpty;
}

class LoginForm with LoggableMixin, ValidatableMixin {
  final String email;
  final String password;
  LoginForm({required this.email, required this.password});

  @override
  Map<String, String> validate() {
    final errors = <String, String>{};
    if (!email.isEmail) errors['email'] = 'Invalid email';
    if (password.length < 8) errors['password'] = 'Too short';
    return errors;
  }
}
```

### Mixin Constraints

Restrict which classes can use a mixin:

```dart
mixin AnimatableMixin on StatefulWidget {
  // Only StatefulWidget subclasses can use this mixin
}
```

## Freezed

Freezed generates data classes with immutability, `copyWith`, equality, JSON serialization, and union types.

```dart
// pubspec.yaml: freezed, freezed_annotation, json_serializable, build_runner

@freezed
class User with _$User {
  const factory User({
    required String id,
    required String name,
    required String email,
    @Default(false) bool isAdmin,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}

// Usage
final user = User(id: '1', name: 'Alice', email: 'a@b.com');
final updated = user.copyWith(name: 'Bob');  // Immutable copy
print(user == updated); // false — value equality

// Union types with Freezed
@freezed
sealed class NetworkState<T> with _$NetworkState<T> {
  const factory NetworkState.idle() = _Idle;
  const factory NetworkState.loading() = _Loading;
  const factory NetworkState.data(T value) = _Data;
  const factory NetworkState.error(String message) = _Error;
}

// Pattern match Freezed unions
Widget build(NetworkState<User> state) {
  return state.when(
    idle: () => const SizedBox(),
    loading: () => const CircularProgressIndicator(),
    data: (user) => Text(user.name),
    error: (msg) => Text(msg),
  );
}
```

Run code generation:

```bash
dart run build_runner build --delete-conflicting-outputs
# Or watch mode during development
dart run build_runner watch --delete-conflicting-outputs
```

## Idiomatic Conventions

| Convention | Rule |
|-----------|------|
| File naming | `snake_case.dart` |
| Class naming | `UpperCamelCase` |
| Variable/function naming | `lowerCamelCase` |
| Constants | `lowerCamelCase` (not SCREAMING_SNAKE) |
| Private members | Prefix with `_` (enforced by analyzer) |
| Library-private | Prefix with `_` at top level |
| Trailing commas | Add on last argument for better diffs and formatting |
| `const` constructors | Use whenever possible for widgets |
| `final` variables | Prefer `final` over `var` for local variables |
| Relative imports | Use for within-package imports |
| Package imports | Use `package:` for cross-package imports |
