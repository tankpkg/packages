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

Riverpod is the recommended state management for new Flutter projects. Compile-safe, supports autoDispose, works without BuildContext.

### Provider Types

| Provider | Use Case | Returns |
|----------|----------|---------|
| `Provider` | Computed/derived values, dependency injection | Synchronous value |
| `NotifierProvider` | Mutable synchronous state with methods | Notifier class |
| `AsyncNotifierProvider` | Mutable async state (API calls, DB) | AsyncNotifier class |
| `FutureProvider` | Read-only async data (simple fetch) | `AsyncValue<T>` |
| `StreamProvider` | Real-time streams (WebSocket, Firestore) | `AsyncValue<T>` |
| `StateProvider` | Simple mutable primitive (counter, toggle) | `T` directly |

Prefer `NotifierProvider` and `AsyncNotifierProvider` for anything beyond trivial state.

### AsyncNotifierProvider Pattern

```dart
final todosProvider = AsyncNotifierProvider<TodosNotifier, List<Todo>>(
  TodosNotifier.new,
);

class TodosNotifier extends AsyncNotifier<List<Todo>> {
  @override
  Future<List<Todo>> build() async {
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
| `ref.read(provider)` | In callbacks, event handlers | No |
| `ref.listen(provider, callback)` | Side effects (snackbar, navigate) | No (fires callback) |
| `ref.invalidate(provider)` | Force lazy rebuild | Marks stale |
| `ref.refresh(provider)` | Force rebuild, return new value | Returns new value |

### autoDispose and family

```dart
// autoDispose: disposed when no widget watches it
final searchProvider = FutureProvider.autoDispose<List<Result>>((ref) async {
  final query = ref.watch(searchQueryProvider);
  return api.search(query);
});

// family: parameterized providers
final userProvider = FutureProvider.autoDispose.family<User, String>(
  (ref, userId) async => ref.watch(apiClientProvider).getUser(userId),
);

// Consume: ref.watch(userProvider('user-123'))

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
test('TodosNotifier fetches todos on build', () async {
  final container = ProviderContainer(
    overrides: [
      todoRepositoryProvider.overrideWithValue(MockTodoRepository()),
    ],
  );
  addTearDown(container.dispose);

  await container.read(todosProvider.future);
  final todos = container.read(todosProvider).valueOrNull;
  expect(todos, isNotEmpty);
});
```

### ConsumerWidget vs Consumer

```dart
// Full widget - most cases
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

// Scoped rebuild - limit rebuild surface
class BigScreen extends StatelessWidget {
  const BigScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return Column(children: [
      const ExpensiveHeader(), // Does NOT rebuild
      Consumer(builder: (context, ref, child) {
        final count = ref.watch(counterProvider);
        return Text('$count'); // Only this rebuilds
      }),
    ]);
  }
}
```

## BLoC / Cubit

BLoC separates UI from business logic using streams. Cubit is simplified BLoC without events.

### When BLoC vs Cubit

| Signal | Use |
|--------|-----|
| Trace/log every state change trigger | BLoC (events are loggable objects) |
| Complex async (debounce, throttle, concurrent) | BLoC (event transformers) |
| Simple state mutations | Cubit (direct method calls) |
| Minimal boilerplate | Cubit |

### BLoC Pattern with Sealed Events

```dart
sealed class AuthEvent {}
class AuthLoginRequested extends AuthEvent {
  final String email, password;
  AuthLoginRequested({required this.email, required this.password});
}
class AuthLogoutRequested extends AuthEvent {}

sealed class AuthState {}
class AuthInitial extends AuthState {}
class AuthLoading extends AuthState {}
class AuthAuthenticated extends AuthState { final User user; AuthAuthenticated(this.user); }
class AuthFailure extends AuthState { final String message; AuthFailure(this.message); }

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
| `BlocListener<B, S>` | Side effects without rebuild |
| `BlocConsumer<B, S>` | Both rebuild and side effects |
| `BlocSelector<B, S, T>` | Rebuild only when selected value changes |

### BLoC Testing

```dart
blocTest<AuthBloc, AuthState>(
  'emits [AuthLoading, AuthAuthenticated] on login success',
  build: () => AuthBloc(mockRepo),
  act: (bloc) => bloc.add(AuthLoginRequested(email: 'a@b.com', password: 'pw')),
  expect: () => [isA<AuthLoading>(), isA<AuthAuthenticated>()],
);
```

## Provider (Legacy)

Still used in existing codebases. Not recommended for new projects.

```dart
ChangeNotifierProvider(create: (_) => CartModel(), child: const MyApp());

Consumer<CartModel>(builder: (context, cart, child) => Text('${cart.totalItems}'));
context.read<CartModel>().addItem(item);
context.select<CartModel, int>((cart) => cart.totalItems);
```

## Decision Framework

| Factor | Riverpod | BLoC | Provider |
|--------|----------|------|----------|
| Learning curve | Medium | Medium-High | Low |
| Boilerplate | Low (with codegen) | Medium-High | Low |
| Testability | Excellent (ProviderContainer) | Excellent (blocTest) | Good |
| Compile safety | Yes | Partial | No |
| Event traceability | Manual | Built-in | Manual |
| Async handling | AsyncValue built-in | Manual state classes | Manual |
| Code generation | Optional (riverpod_generator) | Optional (freezed) | None |

## Common Mistakes

| Mistake | Approach | Fix |
|---------|----------|-----|
| `ref.watch` in callbacks | Riverpod | Use `ref.read` in onPressed |
| Creating provider inside `build` | Riverpod | Define as top-level globals |
| Giant monolithic BLoC | BLoC | Split into feature-scoped BLoCs |
| Not using `Equatable` on states | BLoC | Extend Equatable or use Freezed |
| Nested ChangeNotifierProvider 5+ levels | Provider | Migrate to Riverpod |
| Mixing setState and state management | All | Pick one source of truth |
| Not disposing streams | All | Use autoDispose or close in `dispose()` |
