# Performance and Deployment

Sources: Flutter official documentation (performance, DevTools, build modes, deployment), Dart docs, Fastlane docs, Codemagic docs, community Flutter release engineering patterns from 2024-2026

Covers: Flutter performance profiling, rebuild optimization, rendering and paint tuning, DevTools usage, app size considerations, flavors, CI/CD, Android/iOS/web deployment, and release engineering patterns.

## Profile Before You Guess

Flutter performance work should begin with measurement, not folklore.

| Tool | Use |
|-----|-----|
| Flutter DevTools | frame chart, rebuild stats, memory, CPU |
| performance overlay | quick frame pacing check |
| timeline tracing | animation and jank investigation |
| app size analysis | package and asset bloat |

Do not optimize just because a pattern “sounds expensive”. Measure the real bottleneck first.

## Rebuild Optimization

| Technique | Why |
|----------|-----|
| `const` constructors | skip rebuild work where possible |
| extract smaller widgets | reduce rebuild scope |
| `select` / `BlocSelector` | watch narrow slices of state |
| avoid broad `setState` on large trees | shrink recomposition |

### Rule of thumb

Optimize the rebuild boundary before reaching for lower-level paint tricks.

## Paint and Render Optimization

| Concern | Tool |
|--------|------|
| expensive custom paint | profile with DevTools frame chart |
| isolated heavy repaint area | `RepaintBoundary` |
| huge scrolling lists | `ListView.builder`, slivers, item virtualization |
| oversized images | resize/compress/cache appropriately |

Use `RepaintBoundary` surgically. Wrapping everything creates overhead without benefit.

## Common Performance Smells

| Smell | Why it hurts |
|------|--------------|
| rebuilding giant screens for tiny state changes | frame work spikes |
| too many nested layout passes | expensive build/layout |
| large unoptimized images | memory and raster cost |
| synchronous heavy work on main isolate | visible UI jank |

## Isolates and Background Work

Use isolates for truly heavy CPU-bound work.

| Good fit | Example |
|---------|---------|
| JSON parsing of massive payloads | large offline data sync |
| image processing | media-heavy apps |
| expensive computation | local analytics/crypto-like tasks |

Do not move tiny work to an isolate just because you can.

## Flavors and Environments

Flavors separate environments and product variants cleanly.

| Flavor | Typical use |
|-------|-------------|
| dev | local/debug backend |
| staging | QA/test backend |
| prod | release backend |

Keep bundle IDs/package names, app names, and API endpoints explicit per flavor.

## CI/CD Patterns

| Step | Purpose |
|-----|---------|
| `flutter test` | unit/widget confidence |
| static analysis | `flutter analyze` |
| build artifacts | apk/aab/ipa/web outputs |
| signing + distribution | release delivery |

Fastlane and Codemagic are useful when mobile release automation becomes frequent enough to justify standardization.

## Android and iOS Release Concerns

| Concern | Recommendation |
|--------|----------------|
| signing keys/certificates | manage securely outside repo |
| versioning | automate build number updates |
| store metadata | keep reproducible release notes/assets |
| crash reporting | integrate before broad launch |

## Web and Desktop Considerations

| Target | Watch out for |
|-------|----------------|
| web | bundle size, DOM/canvas performance, SEO limits |
| desktop | windowing/platform conventions, file system integration |

Do not assume one Flutter target behaves like another just because the widget code is shared.

## Common Deployment Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| releasing without flavor separation | wrong backend/config leaks | define env strategy early |
| no profile-mode testing | debug assumptions hide real bottlenecks | test in profile/release |
| giant unoptimized asset bundles | slow installs/startup | audit assets and dependencies |
| ad hoc store release steps | brittle delivery | script or automate with CI/Fastlane |

## Release Readiness Checklist

- [ ] App is profiled in profile/release mode, not only debug
- [ ] Rebuild hotspots have been reduced with widget extraction or selective watching
- [ ] Large lists, images, and paints are measured and optimized where needed
- [ ] Flavor and environment configuration is explicit
- [ ] CI/CD runs tests, analysis, and build steps reproducibly
- [ ] Store signing and release metadata are managed securely
