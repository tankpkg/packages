# Dart Patterns

Sources: Dart language specification (Dart 3.x, dart.dev 2025-2026), Effective Dart guide (dart.dev/effective-dart), Freezed package documentation, Dart API reference

Covers: null safety, sealed classes, records, pattern matching, extensions, mixins, Freezed code generation, and idiomatic Dart conventions.

## Null Safety

Dart's sound null safety guarantees that a non-nullable variable can never be `null` at runtime.

### Core Rules

| Type | Nullable? | Example |
|------|-----------|---------|
| `String` | No | Cannot be null |
| `String?` | Yes | Can be null |
| `late String` | No, deferred init | Must be assigned before first read |
| `required String name` | No, required param | Caller must provide |

### Operators

```dart
String? name;

final length = name?.length;         // int? - null if name is null
final display = name ?? 'Anonymous'; // String - fallback if null
final forced = name!;               // String - throws if null (avoid in prod)
name ??= 'Default';                 // Assigns only if currently null
```

### Late Variables

```dart
class ApiService {
  late final HttpClient _client; // Assigned once, then immutable
  void init(String baseUrl) { _client = HttpClient(baseUrl); }
}
```

Rules: `late final` for dependency injection. Never use `late` as a substitute for proper null handling — if the variable might be absent, use `?`.

## Sealed Classes

Sealed classes restrict subtyping. Combined with pattern matching, they enable exhaustive `switch` — the compiler verifies every subtype is handled.

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
  // Adding a new subtype causes a compile error until handled
}
```

### Use Cases

| Use Case | Pattern |
|----------|---------|
| API response states | `sealed class AsyncState` |
| Navigation events | `sealed class NavigationEvent` |
| BLoC events and states | `sealed class AuthEvent` |
| Form validation | `sealed class ValidationResult` |
| Environment config | `sealed class Environment` (dev/staging/prod) |

## Records

Anonymous, immutable, structural types for returning multiple values:

```dart
// Positional fields
(String, int) getUser() => ('Alice', 30);

// Named fields (preferred)
({String name, int age}) getUserNamed() => (name: 'Alice', age: 30);

// Destructuring
final (name, age) = getUser();
final (:name, :age) = getUserNamed();
```

### When Records vs Classes

| Signal | Use Record | Use Class |
|--------|-----------|-----------|
| Returning multiple values | Yes | Overkill |
| Temporary grouping (cache key) | Yes | Overkill |
| Data with behavior (methods) | No | Yes |
| API serialization | No | Yes (Freezed/json_serializable) |
| Named constructors / factories | No | Yes |

Records are structural — same shape and values = equal:

```dart
final a = (name: 'Alice', age: 30);
final b = (name: 'Alice', age: 30);
assert(a == b); // true
```

## Pattern Matching

### Switch Expressions

```dart
final label = switch (status) {
  Status.active => 'Active',
  Status.inactive => 'Inactive',
  Status.suspended => 'Suspended',
};

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
if (list case [var first, ...var rest]) {
  print('First: $first, Rest: $rest');
}

final config = {'debug': true, 'port': 8080};
if (config case {'debug': true, 'port': int port}) {
  print('Debug on port $port');
}
```

## Extensions

Add methods to existing types without modifying them:

```dart
extension StringX on String {
  String get capitalize =>
      isEmpty ? '' : '${this[0].toUpperCase()}${substring(1)}';
  bool get isEmail =>
      RegExp(r'^[\w-.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(this);
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
  double get screenWidth => MediaQuery.sizeOf(this).width;
}
```

Name extension files `{type}_extensions.dart` and classes `{Type}X`.

## Mixins

Add behavior without inheritance hierarchy constraints:

```dart
mixin LoggableMixin {
  void log(String message) => print('[${runtimeType}] $message');
}

mixin ValidatableMixin {
  Map<String, String> validate();
  bool get isValid => validate().isEmpty;
}

class LoginForm with LoggableMixin, ValidatableMixin {
  final String email, password;
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

```dart
mixin AnimatableMixin on StatefulWidget {
  // Only StatefulWidget subclasses can use this mixin
}
```

## Freezed

Generates data classes with immutability, `copyWith`, equality, and JSON serialization:

```dart
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
final updated = user.copyWith(name: 'Bob');
print(user == updated); // false - value equality
```

### Freezed Union Types

```dart
@freezed
sealed class NetworkState<T> with _$NetworkState<T> {
  const factory NetworkState.idle() = _Idle;
  const factory NetworkState.loading() = _Loading;
  const factory NetworkState.data(T value) = _Data;
  const factory NetworkState.error(String message) = _Error;
}

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
dart run build_runner watch --delete-conflicting-outputs  # Dev mode
```

## Idiomatic Conventions

| Convention | Rule |
|-----------|------|
| File naming | `snake_case.dart` |
| Class naming | `UpperCamelCase` |
| Variable/function | `lowerCamelCase` |
| Constants | `lowerCamelCase` (not SCREAMING_SNAKE) |
| Private members | Prefix with `_` |
| Trailing commas | Add on last argument for better diffs |
| `const` constructors | Use whenever possible |
| `final` locals | Prefer `final` over `var` |
| Relative imports | Within-package |
| Package imports | `package:` for cross-package |
