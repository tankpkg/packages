---
name: "@tank/react-native-expo"
description: |
  Production React Native development with Expo. Covers Expo Router
  (file-based routing, layouts, typed routes, deep linking), EAS Build/Submit/Update
  (build profiles, OTA updates, app store submission, code signing), New Architecture
  (Fabric, TurboModules, bridgeless mode), animations (Reanimated 3, Gesture Handler),
  styling (NativeWind, Unistyles, StyleSheet), state management (Zustand, TanStack Query,
  MMKV), native modules (Expo Modules API, config plugins), performance optimization
  (FlashList, Hermes, bundle splitting), testing (Jest, RNTL, Detox, Maestro),
  push notifications (expo-notifications, FCM/APNs), and app store publishing.
  Synthesizes Expo documentation (2025-2026), React Native docs, React Navigation v7,
  Reanimated docs, and production community patterns.

  Trigger phrases: "react native", "expo", "expo router", "react native navigation",
  "eas build", "eas update", "OTA update", "expo push notifications",
  "react native performance", "react native animation", "reanimated",
  "react native testing", "expo config plugin", "native module",
  "react native typescript", "expo sdk", "app store submission",
  "deep linking", "react native styling", "nativewind", "flashlist",
  "new architecture", "fabric", "turbomodules", "expo go",
  "development build", "react native debugger", "expo notifications"
---

# React Native Expo

## Core Philosophy

1. **Expo-managed by default** — Start every project with Expo managed workflow. Eject to bare only when a specific native requirement demands it. Development builds bridge the gap without full ejection.
2. **File-based routing is the standard** — Expo Router replaces manual navigation configuration with file-system conventions. Layouts, typed routes, and deep linking come for free.
3. **OTA updates separate deploy from release** — Ship JavaScript changes instantly via EAS Update without app store review. Reserve native builds for native code changes only.
4. **Animations on the UI thread** — Never animate on the JS thread. Use Reanimated worklets and Gesture Handler for 60fps interactions that survive heavy JS computation.
5. **New Architecture is mandatory** — SDK 55+ runs entirely on the New Architecture (Fabric, TurboModules, bridgeless). Legacy architecture is frozen. Build for New Architecture from day one.

## Quick-Start: Common Problems

### "How do I structure navigation?"

| Pattern | Implementation |
|---------|---------------|
| Stack screens | `_layout.tsx` returning `<Stack />` |
| Bottom tabs | `(tabs)/_layout.tsx` returning `<Tabs />` |
| Drawer | `_layout.tsx` with `expo-router/drawer` |
| Auth gate | Root layout with redirect logic |
| Modal | Route group with `presentation: 'modal'` |

-> See `references/expo-router.md`

### "How do I deploy updates without app store review?"

1. Configure `eas update:configure` in the project
2. Build with a channel: `eas build --profile production`
3. Push updates: `eas update --channel production`
4. Updates apply on second app launch by default
5. Use `expo-updates` API for immediate apply on launch

-> See `references/eas-build-deploy.md`

### "My animations are janky"

1. Confirm animation runs on UI thread — use `useAnimatedStyle` with worklets
2. Replace `Animated` API with Reanimated `useSharedValue` + `withSpring`/`withTiming`
3. Combine with Gesture Handler for gesture-driven animations
4. Use `entering`/`exiting` props for layout animations
5. Profile with React DevTools and Perf Monitor

-> See `references/animations-gestures.md`

### "Which styling approach should I use?"

| Need | Recommendation |
|------|---------------|
| Tailwind familiarity, web parity | NativeWind v4 |
| Maximum performance, type-safe | Unistyles 2 |
| Component library with themes | Tamagui |
| Simple, no deps | StyleSheet.create |

-> See `references/styling-patterns.md`

### "How do I manage state?"

1. Server state: TanStack Query (caching, refetch, optimistic updates)
2. Client state: Zustand (lightweight, no boilerplate, middleware)
3. Persistence: MMKV for synchronous storage (replaces AsyncStorage)
4. Forms: React Hook Form with Zod validation

-> See `references/state-management.md`

## Decision Trees

### Project Setup

| Signal | Recommendation |
|--------|---------------|
| New project | `npx create-expo-app@latest` (managed workflow) |
| Need custom native code | Development build + config plugins |
| Existing bare RN project | Add Expo with `npx install-expo-modules@latest` |
| Must use specific native SDK | Expo Modules API or config plugin |

### Build Strategy

| Change Type | Deploy Method |
|-------------|--------------|
| JS/TS code, assets, styles | EAS Update (OTA, instant) |
| New native module or SDK version | EAS Build (full binary) |
| App store metadata | EAS Metadata |
| Testing/preview | EAS Build --profile preview |

### Navigation Pattern

| Screen Relationship | Navigator |
|--------------------|-----------|
| Linear forward/back flow | Stack |
| Persistent bottom bar | Tabs (or NativeTabs) |
| Side menu | Drawer |
| Overlay preserving context | Modal (presentation: 'modal') |
| Auth-gated sections | Route groups with redirect |

## Reference Index

| File | Contents |
|------|----------|
| `references/expo-router.md` | File-based routing, layouts (Stack/Tabs/Drawer), typed routes, deep linking, authentication patterns, API routes, platform-specific modules |
| `references/eas-build-deploy.md` | EAS Build profiles, EAS Submit, EAS Update (OTA), code signing, eas.json configuration, CI/CD workflows, development builds vs Expo Go |
| `references/new-architecture.md` | Fabric renderer, TurboModules, JSI, bridgeless mode, migration guide, library compatibility, Expo Modules API |
| `references/animations-gestures.md` | Reanimated 3 (worklets, shared values, layout animations), Gesture Handler v2, spring/timing configs, gesture composition, performance patterns |
| `references/styling-patterns.md` | NativeWind v4, Unistyles 2, Tamagui, StyleSheet API, responsive design, dark mode, platform-specific styling, safe areas |
| `references/state-management.md` | Zustand, TanStack Query, MMKV, React Hook Form, offline-first patterns, secure storage, context patterns |
| `references/testing-debugging.md` | Jest + RNTL unit/component tests, Detox E2E, Maestro, debugging tools, Hermes profiling, React DevTools, common crash patterns |
| `references/platform-features.md` | Push notifications (expo-notifications, FCM/APNs), deep linking, universal links, biometric auth, camera/media, file system, splash screen, app icons |
| `references/performance.md` | FlashList vs FlatList, Hermes engine, bundle optimization, image caching (expo-image), memory management, startup time, New Architecture performance gains |
