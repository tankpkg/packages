# Testing

Sources: Flutter testing documentation (flutter.dev 2025-2026), flutter_test API reference, integration_test package, bloc_test documentation, Mocktail package documentation

Covers: widget tests, integration tests, golden tests, finder/matcher patterns, Riverpod and BLoC testing, mocking with Mocktail, and test organization.

## Test Pyramid

| Level | Speed | Scope | Tool |
|-------|-------|-------|------|
| Unit | Fast (ms) | Function, class, provider | `test` package |
| Widget | Medium (ms-s) | Single widget or small tree | `flutter_test` |
| Integration | Slow (s-min) | Full app or feature flow | `integration_test` |
| Golden | Medium | Visual regression | `flutter_test` + `matchesGoldenFile` |

Many unit tests, moderate widget tests, few integration tests. Test logic with unit tests, UI behavior with widget tests, critical journeys with integration tests.

## Widget Tests

### Basic Structure

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('shows greeting with name', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: GreetingCard(name: 'Alice')),
    );
    expect(find.text('Hello, Alice!'), findsOneWidget);
    expect(find.byIcon(Icons.person), findsOneWidget);
  });
}
```

### Finders

| Finder | Use |
|--------|-----|
| `find.text('Hello')` | Exact text |
| `find.textContaining('Hell')` | Partial text |
| `find.byType(ElevatedButton)` | Widget type |
| `find.byIcon(Icons.add)` | Icon data |
| `find.byKey(Key('submit'))` | By Key (most reliable) |
| `find.descendant(of: parent, matching: child)` | Scoped search |
| `find.ancestor(of: child, matching: parent)` | Upward search |

### Matchers

| Matcher | Asserts |
|---------|---------|
| `findsOneWidget` | Exactly one |
| `findsNothing` | Zero |
| `findsNWidgets(n)` | Exactly n |
| `findsAtLeast(n)` | At least n |

### Interactions

```dart
testWidgets('submits form on tap', (tester) async {
  await tester.pumpWidget(MaterialApp(home: LoginForm()));

  await tester.enterText(find.byKey(Key('email')), 'alice@example.com');
  await tester.enterText(find.byKey(Key('password')), 'secret123');
  await tester.tap(find.byType(FilledButton));
  await tester.pumpAndSettle();

  expect(find.text('Welcome'), findsOneWidget);
});
```

### pump vs pumpAndSettle

| Method | Behavior | Use When |
|--------|----------|----------|
| `pump()` | One frame | Synchronous state change |
| `pump(Duration(seconds: 1))` | One frame at offset | Animations at specific points |
| `pumpAndSettle()` | Until no pending frames | Async, animations |

`pumpAndSettle` throws if animations never settle (e.g., infinite repeat). Use `pump` with explicit durations.

### Scrolling

```dart
testWidgets('scrolls to find item', (tester) async {
  await tester.pumpWidget(MaterialApp(home: LongList()));
  await tester.scrollUntilVisible(
    find.text('Item 50'), 500.0,
    scrollable: find.byType(Scrollable),
  );
});
```

## Golden Tests

Compare rendering against reference images. Detect unintended visual changes.

```dart
testWidgets('button matches golden', (tester) async {
  tester.view.physicalSize = const Size(400, 300);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);

  await tester.pumpWidget(
    MaterialApp(home: Scaffold(body: Center(child: PrimaryButton(label: 'Submit')))),
  );
  await expectLater(
    find.byType(PrimaryButton),
    matchesGoldenFile('goldens/primary_button.png'),
  );
});
```

### Golden Workflow

```bash
flutter test --update-goldens  # Generate/update reference images
flutter test                   # Compare against references
```

### Best Practices

- Store in `test/goldens/` and commit to version control
- Platform-dependent rendering — generate on CI platform
- Set explicit `physicalSize` and `devicePixelRatio` for deterministic output
- Use `Tags('golden')` to separate from unit tests

## Testing with Riverpod

### Override Providers

```dart
testWidgets('displays user name', (tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        userProvider.overrideWith((ref) => AsyncData(User(name: 'Alice'))),
      ],
      child: const MaterialApp(home: ProfileScreen()),
    ),
  );
  await tester.pumpAndSettle();
  expect(find.text('Alice'), findsOneWidget);
});
```

### Unit Test with ProviderContainer

```dart
test('todosNotifier fetches from repository', () async {
  final container = ProviderContainer(
    overrides: [
      todoRepositoryProvider.overrideWithValue(FakeTodoRepository()),
    ],
  );
  addTearDown(container.dispose);

  await container.read(todosProvider.future);
  final todos = container.read(todosProvider).valueOrNull;
  expect(todos, hasLength(3));
});
```

### Test Loading/Error States

```dart
testWidgets('shows loading indicator', (tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [todosProvider.overrideWith(() => _NeverCompletesNotifier())],
      child: const MaterialApp(home: TodoListScreen()),
    ),
  );
  expect(find.byType(CircularProgressIndicator), findsOneWidget);
});
```

## Testing with BLoC

### blocTest

```dart
import 'package:bloc_test/bloc_test.dart';

blocTest<AuthBloc, AuthState>(
  'emits [Loading, Authenticated] on login success',
  setUp: () {
    when(() => mockRepo.login(any(), any()))
        .thenAnswer((_) async => testUser);
  },
  build: () => AuthBloc(mockRepo),
  act: (bloc) => bloc.add(
    AuthLoginRequested(email: 'a@b.com', password: 'pw')),
  expect: () => [
    isA<AuthLoading>(),
    isA<AuthAuthenticated>()
        .having((s) => s.user.email, 'email', 'a@b.com'),
  ],
  verify: (_) {
    verify(() => mockRepo.login('a@b.com', 'pw')).called(1);
  },
);
```

### Widget Test with BLoC

```dart
testWidgets('shows user name from BLoC', (tester) async {
  final mockBloc = MockUserBloc();
  when(() => mockBloc.state).thenReturn(UserLoaded(testUser));

  await tester.pumpWidget(MaterialApp(
    home: BlocProvider<UserBloc>.value(
      value: mockBloc, child: const UserScreen()),
  ));
  expect(find.text(testUser.name), findsOneWidget);
});
```

## Mocking with Mocktail

No code generation required (unlike Mockito with build_runner).

```dart
import 'package:mocktail/mocktail.dart';

class MockUserRepository extends Mock implements UserRepository {}

void main() {
  late MockUserRepository mockRepo;
  setUp(() { mockRepo = MockUserRepository(); });

  test('fetches user by id', () async {
    when(() => mockRepo.getUser('123'))
        .thenAnswer((_) async => User(id: '123', name: 'Alice'));

    final user = await mockRepo.getUser('123');
    expect(user.name, 'Alice');
    verify(() => mockRepo.getUser('123')).called(1);
  });
}

// Register fallback values for non-nullable params in any()
setUpAll(() {
  registerFallbackValue(User(id: '', name: ''));
});
```

## Integration Tests

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:my_app/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('full login flow', (tester) async {
    app.main();
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(Key('email')), 'alice@example.com');
    await tester.enterText(find.byKey(Key('password')), 'password123');
    await tester.tap(find.byKey(Key('login_button')));
    await tester.pumpAndSettle();

    expect(find.text('Dashboard'), findsOneWidget);
  });
}
```

```bash
flutter test integration_test/app_test.dart -d <device-id>
```

## Test Organization

```
test/
  unit/
    models/
    providers/
    blocs/
  widget/
    screens/
    components/
  goldens/
  helpers/
    pump_app.dart
    mocks.dart
integration_test/
  flows/
```

### Shared Helper

```dart
extension PumpApp on WidgetTester {
  Future<void> pumpApp(Widget widget, {List<Override>? overrides}) async {
    await pumpWidget(ProviderScope(
      overrides: overrides ?? [],
      child: MaterialApp(home: widget),
    ));
  }
}
```

## State-Driven Test Matrix

| State | Minimum Test |
|-------|-------------|
| Initial/default | Renders correctly |
| Loading | Progress / skeleton |
| Success | Expected data shown |
| Empty | Friendly fallback |
| Error | Retry or message |

If a widget has five states, write tests for all five.
