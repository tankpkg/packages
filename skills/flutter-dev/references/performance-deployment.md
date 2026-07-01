# Performance and Deployment

Sources: Flutter performance documentation (flutter.dev 2025-2026), Flutter DevTools documentation, Fastlane documentation, Codemagic documentation, Google Play Console and App Store Connect guidelines

Covers: DevTools profiling, rebuild optimization, const and RepaintBoundary, isolates, platform channels, flavors, CI/CD pipelines, app store submission, and release engineering.

## Profile Before Guessing

| Tool | Use |
|------|-----|
| Flutter DevTools | Frame chart, rebuild stats, memory, CPU |
| Performance overlay | Quick frame pacing check |
| Timeline tracing | Animation and jank investigation |
| App size analysis | Package and asset bloat |

Measure the real bottleneck. Do not optimize based on folklore.

## Rebuild Optimization

### const Constructors

Mark widget constructors `const` to enable framework-level rebuild skipping. When a parent rebuilds, `const` children are identity-equal — the framework skips their entire subtree.

```dart
// WRONG: new instance every build
return Padding(padding: EdgeInsets.all(16), child: Text('Static'));

// CORRECT: same instance reused
return const Padding(padding: EdgeInsets.all(16), child: Text('Static'));
```

### Extract Subtrees

Split widgets that depend on different state into separate classes:

```dart
// WRONG: entire screen rebuilds when counter changes
class MyScreen extends ConsumerWidget {
  Widget build(context, ref) {
    final count = ref.watch(counterProvider);
    return Column(children: [
      const ExpensiveChart(),  // Rebuilds unnecessarily
      Text('$count'),
    ]);
  }
}

// CORRECT: only CounterDisplay rebuilds
class MyScreen extends StatelessWidget {
  Widget build(context) {
    return Column(children: [
      const ExpensiveChart(),
      const CounterDisplay(),  // Own widget, own rebuild scope
    ]);
  }
}
```

### Selective Watching

```dart
// Riverpod: select specific field
final userName = ref.watch(userProvider.select((u) => u.name));

// BLoC: BlocSelector
BlocSelector<UserBloc, UserState, String>(
  selector: (state) => state.name,
  builder: (context, name) => Text(name),
)
```

## RepaintBoundary

Isolate expensive paint operations to prevent repainting the entire subtree:

```dart
RepaintBoundary(
  child: CustomPaint(painter: ExpensiveChartPainter(data)),
)
```

Use surgically — wrapping everything creates overhead without benefit. Profile first to identify the actual repaint hotspot.

## Isolates

Move CPU-heavy work off the main isolate to prevent UI jank:

```dart
// Simple: compute function
final result = await compute(parseJson, rawString);

// Complex: Isolate.spawn for long-running work
final receivePort = ReceivePort();
await Isolate.spawn(_heavyWork, receivePort.sendPort);
```

| Good Fit | Example |
|---------|---------|
| JSON parsing of large payloads | Offline data sync |
| Image processing | Media-heavy apps |
| Expensive computation | Local analytics, crypto |

Do not move trivial work to isolates — the marshalling overhead exceeds the savings.

## Platform Channels

Communicate between Dart and native code (Kotlin/Swift):

### MethodChannel (Request-Response)

```dart
// Dart side
const channel = MethodChannel('com.example/battery');
final level = await channel.invokeMethod<int>('getBatteryLevel');
```

```kotlin
// Android (Kotlin)
MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "com.example/battery")
  .setMethodCallHandler { call, result ->
    when (call.method) {
      "getBatteryLevel" -> result.success(getBatteryLevel())
      else -> result.notImplemented()
    }
  }
```

```swift
// iOS (Swift)
let channel = FlutterMethodChannel(name: "com.example/battery",
  binaryMessenger: controller.binaryMessenger)
channel.setMethodCallHandler { (call, result) in
  switch call.method {
    case "getBatteryLevel": result(getBatteryLevel())
    default: result(FlutterMethodNotImplemented)
  }
}
```

### EventChannel (Continuous Streams)

Use for sensor data, location updates, or any continuous native event stream:

```dart
const eventChannel = EventChannel('com.example/sensors');
eventChannel.receiveBroadcastStream().listen((event) {
  // Handle continuous native events
});
```

### Channel Best Practices

| Rule | Reason |
|------|--------|
| Name channels with reverse-domain | Avoid collisions |
| Handle errors on both sides | Prevent silent failures |
| Use `BasicMessageChannel` for simple data | Lower overhead |
| Check platform before invoking | Prevent crashes on unsupported platforms |

## Flavors and Environments

Separate environments cleanly:

| Flavor | Use |
|--------|-----|
| dev | Local/debug backend, verbose logging |
| staging | QA/test backend |
| prod | Release backend, analytics enabled |

```bash
# Run with flavor
flutter run --flavor dev -t lib/main_dev.dart
flutter run --flavor prod -t lib/main_prod.dart

# Build with flavor
flutter build apk --flavor prod -t lib/main_prod.dart
flutter build ipa --flavor prod -t lib/main_prod.dart
```

Keep bundle IDs, app names, and API endpoints explicit per flavor.

## CI/CD Pipeline

| Step | Command | Purpose |
|------|---------|---------|
| Analyze | `flutter analyze` | Static analysis |
| Test | `flutter test` | Unit + widget tests |
| Build Android | `flutter build appbundle --release` | AAB for Play Store |
| Build iOS | `flutter build ipa --release` | IPA for App Store |
| Build Web | `flutter build web --release` | Web deployment |

### Fastlane

Automate signing, screenshots, and store submission:

```ruby
# fastlane/Fastfile (iOS)
lane :release do
  build_flutter_app(flavor: "prod")
  upload_to_app_store(skip_metadata: true)
end
```

### Codemagic

Cloud CI/CD built for Flutter — handles signing, provisioning profiles, and store deployment without local setup.

### GitHub Actions

```yaml
name: Flutter CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with: { flutter-version: '3.x' }
      - run: flutter pub get
      - run: flutter analyze
      - run: flutter test
```

## App Store Submission

### Android (Google Play)

| Step | Action |
|------|--------|
| Signing | Generate keystore, configure `key.properties` |
| Build | `flutter build appbundle --release` |
| Upload | Google Play Console or Fastlane |
| Testing | Internal > Closed > Open > Production tracks |

### iOS (App Store)

| Step | Action |
|------|--------|
| Certificates | Apple Developer portal provisioning profiles |
| Build | `flutter build ipa --release` |
| Upload | Xcode Organizer or Transporter |
| Review | TestFlight beta > App Store submission |

### Web

```bash
flutter build web --release
# Deploy dist to CDN, Firebase Hosting, Vercel, etc.
```

## App Size Optimization

| Technique | Impact |
|-----------|--------|
| `--split-per-abi` on Android | 30-50% smaller per device |
| Remove unused packages | Varies |
| Compress images/assets | 10-30% |
| Tree shaking (automatic in release) | Removes dead code |
| Deferred components | On-demand feature loading |

```bash
flutter build apk --analyze-size  # Size breakdown
```

## Common Performance Smells

| Smell | Fix |
|-------|-----|
| Rebuilding giant screens for tiny state changes | Extract widgets, selective watch |
| Large unoptimized images | Resize, compress, cache |
| Synchronous heavy work on main isolate | Move to `compute` or `Isolate.spawn` |
| Startup initializing everything | Defer non-critical initialization |

## Release Readiness

- Profile in release mode (not debug)
- Rebuild hotspots reduced with extraction and selective watching
- Large lists use `ListView.builder` (virtualized)
- Flavor configuration is explicit per environment
- CI/CD runs analysis, tests, and builds reproducibly
- Store signing and metadata managed securely
- Crash reporting wired before broad launch

## Monitoring After Release

1. Watch crash-free session rate
2. Review startup time on real devices
3. Monitor API errors by app version
4. Compare frame metrics across releases

Performance is not finished at submission — release telemetry closes the loop.
