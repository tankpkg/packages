# Testing

Sources: Flutter official documentation (testing, widget tests, integration tests, golden tests), Dart testing docs, mocktail package docs, Riverpod and flutter_bloc testing guidance, community production practices

Covers: widget tests, integration tests, golden tests, Riverpod and BLoC testing patterns, mocking, async rendering, and practical testing strategy for Flutter apps.

## Prefer Widget Tests as the Default

Widget tests give high confidence at good speed.

| Test type | Best for |
|----------|----------|
| unit test | pure functions and domain logic |
| widget test | UI behavior and rendering |
| integration test | full app flows, plugins, navigation |
| golden test | visual regression for stable components |

Do not jump straight to integration tests for behavior that widget tests can cover faster.

## Widget Test Basics

```dart
testWidgets('increments counter', (tester) async {
  await tester.pumpWidget(const MyApp());
  await tester.tap(find.text('Increment'));
  await tester.pump();
  expect(find.text('1'), findsOneWidget);
});
```

### Good widget-test targets

| Target | Why |
|-------|-----|
| form validation | UI + logic boundary |
| loading/error/data states | rendering correctness |
| button interactions | user-visible behavior |
| navigation triggers | routing intent |

## `pump`, `pumpAndSettle`, and Time

| Method | Use |
|-------|-----|
| `pump()` | render one frame / short update |
| `pump(Duration(...))` | advance animations/timers deliberately |
| `pumpAndSettle()` | wait until animations/futures settle |

Do not abuse `pumpAndSettle()` when a targeted `pump(Duration...)` is more precise.

## Testing Riverpod

Wrap widgets in `ProviderScope` and override providers when needed.

```dart
await tester.pumpWidget(
  ProviderScope(
    overrides: [
      currentUserProvider.overrideWith((ref) => fakeUser),
    ],
    child: const MyApp(),
  ),
);
```

### Riverpod test rules

| Rule | Why |
|-----|-----|
| override providers, don’t rewire app code | test isolation |
| test providers separately for business logic | faster feedback |
| watch selected state only where relevant | less brittle assertions |

## Testing BLoC / Cubit

Use real or mocked cubits/blocs at the boundary depending on what is under test.

| Goal | Pattern |
|-----|---------|
| test bloc logic | bloc unit tests |
| test widget with bloc state | `BlocProvider.value` + fake bloc |
| test end-to-end flow | integration or widget + real bloc wiring |

## Golden Tests

Golden tests help catch visual regressions in stable, presentation-heavy widgets.

| Good fit | Example |
|---------|---------|
| design-system components | buttons, cards, nav bars |
| complex static visual states | empty/error/list variants |
| marketing-like Flutter screens | hero/banner cards |

Golden tests are less useful for highly dynamic or unstable pixel output.

## Integration Tests

Use integration tests for real navigation, plugin behavior, auth flows, and app-wide interactions.

| Flow | Why integration matters |
|-----|--------------------------|
| login flow | text fields, navigation, async auth |
| deep linking | router + state restore |
| camera/file plugins | device/runtime integration |
| multi-screen checkout/onboarding | full app shell behavior |

Keep the suite lean and focused on critical journeys.

## Mocking Strategy

| Boundary | Mock? |
|---------|-------|
| HTTP client / repository | yes in widget tests |
| provider/bloc state source | often |
| pure widget child | only if unrelated and noisy |
| platform channels | fake when plugin not needed |

Mock external boundaries, not the Flutter framework itself.

## Finder Strategy

| Finder | Use |
|-------|-----|
| `find.text` | visible text |
| `find.byType` | widget class presence |
| `find.byKey` | stable test targeting |
| semantic/finder patterns | accessibility-aware targeting |

Keys are useful when text and structure are unstable, but do not add meaningless keys everywhere.

## Async and Loading State Tests

| Scenario | Pattern |
|---------|---------|
| provider future loading | initial `pump`, then settle/advance |
| delayed animation | `pump(Duration(...))` |
| retry flow | trigger action, pump, assert next state |

Explicitly test loading, success, and error states for async widgets.

## Golden Test Workflow

| Step | Purpose |
|-----|---------|
| stabilize fonts/assets | reduce flaky diffs |
| pump deterministic state | consistent render |
| capture baseline | visual reference |
| review diff intentionally | catch real regressions |

Golden tests work best when the component is stable and intentionally visual.

## Navigation and Router Testing

| Need | Pattern |
|-----|---------|
| route push/pop | widget/integration test with router shell |
| deep link handling | integration test |
| guarded redirect | integration or high-level widget test |

Routing bugs often show up only when multiple providers, auth state, and async loading interact.

## Test Data Strategy

| Pattern | Benefit |
|--------|---------|
| small builders / fixtures | readable setup |
| named fake states | clear intent |
| provider overrides | isolate only what matters |

Avoid huge hand-authored test trees that no one understands six weeks later.

## Accessibility Testing Notes

Check semantic labels and interactions for high-value widgets.

| Concern | Example |
|--------|---------|
| button labels | discoverable actions |
| text field hints/labels | form clarity |
| focus order | keyboard/device navigation |

## State-Driven Test Matrix

| State kind | Minimum test surface |
|-----------|----------------------|
| initial/default | renders correctly |
| loading | progress / skeleton / disabled UI |
| success | expected data shown |
| empty | friendly fallback |
| error | retry or error messaging |

If your widget has five states, write tests that prove all five.

## CI Strategy for Flutter Tests

| Step | Why |
|-----|-----|
| `flutter test` | fast behavior coverage |
| targeted golden tests | visual regressions |
| selected integration suite | critical journey confidence |

Keep CI focused enough to stay fast, but broad enough to catch regressions before release.

## Practical Test Layer Selection

| Scenario | Best layer |
|---------|------------|
| text formatter, mapper, parser | unit |
| reusable button/form widget | widget |
| auth flow across screens | integration |
| visual design-system component | golden + widget |

Choose the layer that proves the risk with the least runtime cost.

## Test Harness Patterns

| Need | Pattern |
|-----|---------|
| app theme/media setup | wrap in `MaterialApp` / app shell |
| provider injection | `ProviderScope` / `MultiBlocProvider` |
| localization | test harness with delegates/locales |

Build a reusable harness for app-wide test setup rather than copying wrappers in every file.

## Failure Diagnostics

When tests fail, make the signal useful.

| Technique | Benefit |
|----------|---------|
| named test cases | easier triage |
| explicit state assertions | less ambiguity |
| smaller widget surfaces | failures isolate faster |

Test readability is a maintenance feature, not just nicety.

## Common Testing Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| testing implementation details | brittle tests | assert user-visible behavior |
| too many integration tests | slow feedback | move most checks to widget tests |
| relying only on golden tests | weak behavioral confidence | add interaction tests |
| not testing empty/error/loading states | production blind spots | cover all major states |

## Release Readiness Checklist

- [ ] Core UI behavior is covered by widget tests
- [ ] Async widgets test loading, success, and error states
- [ ] Riverpod/BLoC boundaries are isolated cleanly in tests
- [ ] Integration tests cover only the highest-value full-app flows
- [ ] Golden tests are used for stable visual surfaces where they add value
