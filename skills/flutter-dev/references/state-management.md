# State Management

Sources: Riverpod official documentation (riverpod.dev 2025-2026), flutter_bloc documentation (bloclibrary.dev), Flutter official state management guide (flutter.dev), Provider package documentation

Covers: Riverpod provider types and ref patterns, BLoC/Cubit architecture, Provider (legacy), selection decision framework, and common mistakes per approach.

## Ephemeral vs App State

| State Type | Scope | Tool |
|-----------|-------|------|
| Ephemeral / UI state | Single widget (form input, animation, tab index) | `setState` |
| Feature state | Shared across a feature's widgets | Riverpod provider or BLoC scoped to feature |
| App state | Global (auth, theme, user profile, cart) | Riverpod or BLoC at app scope |
| Server cache | Data fetched from API, needs caching/invalidation | Riverpod `AsyncNotifierProvider` or BLoC + repository |

Rule: use `setState` until you need to share state between widgets. Then reach for Riverpod or BLoC.

## Riverpod

Riverpod is the recommended state management solution for new Flutter projects. It is compile-safe (no runtime errors from missing providers), supports autoDispose, and works without BuildContext.

### Provider Types

| Provider | Use Case | Returns |
|----------|----------|---------|
| `Provider` | Computed/derived values, dependency injection | Synchronous value |
| `NotifierProvider` | Mutable synchronous state with methods | Notifier class |
| `AsyncNotifierProvider` | Mutable async state (API calls, DB) | AsyncNotifier class |
| `FutureProvider` | Read-only async data (simple fetch) | `AsyncValue<T>` |
| `StreamProvider` | Real-time streams (WebSocket, Firestore) | `AsyncValue<T>` |
| `StateProvider` | Simple mutable primitive (counter, toggle) | `T` directly |

Prefer `NotifierProvider` and `AsyncNotifierProvider` for anything beyond trivial state. They centralize mutation logic in the Notifier class.

### AsyncNotifierProvider Pattern

The production workhorse for API-backed state:

```dart
final todosProvider = AsyncNotifierProvider<TodosNotifier, List<Todo>>(
  TodosNotifier.new,
);

class TodosNotifier extends AsyncNotifier<List<Todo>> {
  @override
  Future<List<Todo>> build() async {
    // Called on first read and after invalidation
    final repository = ref.watch(todoRepositoryProvider);
    return repository.fetchAll();
  }

  Future<void> add(String title) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final repository = ref.read(todoRepositoryProvider);
      await repository.add(title);
      return repository.fetchAll();
    });
  }

  Future<void> toggle(String id) async {
    final previous = state;
    // Optimistic update
    state = AsyncData([
      for (final todo in previous.valueOrNull ?? [])
        if (todo.id == id) todo.copyWith(completed: !todo.completed)
        else todo,
    ]);
    try {
      await ref.read(todoRepositoryProvider).toggle(id);
    } catch (e, st) {
      state = previous; // Rollback on failure
    }
  }
}
```

### ref Patterns

| Method | When | Rebuilds? |
|--------|------|-----------|
| `ref.watch(provider)` | In `build` or provider body | Yes |
| `ref.read(provider)` | In callbacks, event handlers, one-time reads | No |
| `ref.listen(provider, callback)` | Side effects (show snackbar, navigate) | No (fires callback) |
| `ref.invalidate(provider)` | Force provider to rebuild lazily | Marks stale |
| `ref.refresh(provider)` | Force rebuild and return new value immediately | Returns new value |

### autoDispose and family

```dart
// autoDispose: provider disposed when no widget watches it
final searchProvider = FutureProvider.autoDispose<List<Result>>((ref) async {
  final query = ref.watch(searchQueryProvider);
  return api.search(query);
});

// family: parameterized providers
final userProvider = FutureProvider.autoDispose.family<User, String>(
  (ref, userId) async {
    return ref.watch(apiClientProvider).getUser(userId);
  },
);

// Consume family provider
final user = ref.watch(userProvider('user-123'));

// Multiple parameters with records
final filteredProvider = Provider.family<List<Item>, ({String query, bool active})>(
  (ref, params) {
    final items = ref.watch(allItemsProvider);
    return items.where((i) => i.name.contains(params.query)).toList();
  },
);
```

### Riverpod Testing

```dart
void main() {
  test('TodosNotifier fetches todos on build', () async {
    final container = ProviderContainer(
      overrides: [
        todoRepositoryProvider.overrideWithValue(MockTodoRepository()),
      ],
    );
    addTearDown(container.dispose);

    // Wait for async provider to complete
    await container.read(todosProvider.future);

    final todos = container.read(todosProvider).valueOrNull;
    expect(todos, isNotEmpty);
  });
}
```

### ConsumerWidget vs Consumer

```dart
// Full widget — use for most cases
class TodoList extends ConsumerWidget {
  const TodoList({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final todosAsync = ref.watch(todosProvider);
    return todosAsync.when(
      data: (todos) => ListView.builder(
        itemCount: todos.length,
        itemBuilder: (_, i) => TodoTile(todo: todos[i]),
      ),
      loading: () => const CircularProgressIndicator(),
      error: (e, _) => Text('Error: $e'),
    );
  }
}

// Scoped rebuild — use to limit rebuild surface
class BigScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const ExpensiveHeader(), // Does NOT rebuild
        Consumer(
          builder: (context, ref, child) {
            final count = ref.watch(counterProvider);
            return Text('$count'); // Only this rebuilds
          },
        ),
      ],
    );
  }
}
```

## BLoC / Cubit

BLoC (Business Logic Component) separates UI from business logic using streams. Cubit is a simplified BLoC without explicit events.

### When BLoC vs Cubit

| Signal | Use |
|--------|-----|
| Need to trace/log every state change trigger | BLoC (events are objects, loggable) |
| Complex async workflows (debounce, throttle, concurrent) | BLoC (event transformers) |
| Simple state mutations | Cubit (direct method calls) |
| Team prefers explicit event classes | BLoC |
| Minimal boilerplate wanted | Cubit |

### Cubit Pattern

```dart
class CounterCubit extends Cubit<int> {
  CounterCubit() : super(0);
  void increment() => emit(state + 1);
  void decrement() => emit(state - 1);
}
```

### BLoC Pattern with Sealed Events

```dart
sealed class AuthEvent {}
class AuthLoginRequested extends AuthEvent {
  final String email;
  final String password;
  AuthLoginRequested({required this.email, required this.password});
}
class AuthLogoutRequested extends AuthEvent {}

sealed class AuthState {}
class AuthInitial extends AuthState {}
class AuthLoading extends AuthState {}
class AuthAuthenticated extends AuthState {
  final User user;
  AuthAuthenticated(this.user);
}
class AuthFailure extends AuthState {
  final String message;
  AuthFailure(this.message);
}

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthRepository _repo;

  AuthBloc(this._repo) : super(AuthInitial()) {
    on<AuthLoginRequested>(_onLogin);
    on<AuthLogoutRequested>(_onLogout);
  }

  Future<void> _onLogin(AuthLoginRequested event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      final user = await _repo.login(event.email, event.password);
      emit(AuthAuthenticated(user));
    } catch (e) {
      emit(AuthFailure(e.toString()));
    }
  }

  Future<void> _onLogout(AuthLogoutRequested event, Emitter<AuthState> emit) async {
    await _repo.logout();
    emit(AuthInitial());
  }
}
```

### BLoC Widgets

| Widget | Use |
|--------|-----|
| `BlocBuilder<B, S>` | Rebuild UI on state change |
| `BlocListener<B, S>` | Side effects (navigation, snackbar) — no rebuild |
| `BlocConsumer<B, S>` | Both rebuild and side effects |
| `BlocSelector<B, S, T>` | Rebuild only when selected value changes |

### BLoC Testing

```dart
blocTest<AuthBloc, AuthState>(
  'emits [AuthLoading, AuthAuthenticated] on successful login',
  build: () => AuthBloc(mockRepo),
  act: (bloc) => bloc.add(AuthLoginRequested(email: 'a@b.com', password: 'pw')),
  expect: () => [
    isA<AuthLoading>(),
    isA<AuthAuthenticated>(),
  ],
);
```

## Provider (Legacy)

Still widely used in existing codebases. Not recommended for new projects — use Riverpod instead.

```dart
ChangeNotifierProvider(
  create: (_) => CartModel(),
  child: const MyApp(),
);

// Consume
Consumer<CartModel>(
  builder: (context, cart, child) => Text('${cart.totalItems}'),
);

// Read without rebuilding
context.read<CartModel>().addItem(item);

// Select specific field (rebuild only when that field changes)
context.select<CartModel, int>((cart) => cart.totalItems);
```

## Decision Framework

| Factor | Riverpod | BLoC | Provider |
|--------|----------|------|----------|
| Learning curve | Medium | Medium-High | Low |
| Boilerplate | Low (with codegen) | Medium-High | Low |
| Testability | Excellent (ProviderContainer) | Excellent (blocTest) | Good |
| Compile safety | Yes (no runtime missing-provider errors) | Partial | No |
| DevTools support | Riverpod DevTools | BLoC Observer | Provider DevTools |
| Event traceability | Manual logging | Built-in (events are objects) | Manual logging |
| Async handling | AsyncValue (loading/data/error built-in) | Manual with state classes | Manual |
| Code generation | Optional (riverpod_generator) | Optional (freezed for states) | None |

## Common Mistakes

| Mistake | Approach | Fix |
|---------|----------|-----|
| `ref.watch` in callbacks | Riverpod | Use `ref.read` in onPressed/onTap |
| Creating provider inside `build` | Riverpod | Define providers as top-level globals |
| Giant monolithic BLoC | BLoC | Split into feature-scoped BLoCs |
| Not using `Equatable` on states | BLoC | Extend Equatable or use Freezed for state equality |
| Nested `ChangeNotifierProvider` 5+ levels | Provider | Migrate to Riverpod (flat provider graph) |
| Mixing `setState` and state management for same data | All | Pick one source of truth per piece of state |
| Not disposing streams/subscriptions | All | Use autoDispose (Riverpod) or close in `dispose()` |
