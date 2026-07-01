# Animations and Gestures

Sources: React Native Reanimated documentation (Software Mansion, 2025-2026), React Native Gesture Handler v2 docs, React Native performance documentation

Covers: Reanimated 3 worklets and shared values, animated styles, layout animations, entering/exiting transitions, Gesture Handler v2 composition, spring and timing configurations, gesture-driven animations, and performance patterns.

## Reanimated 3 Core Concepts

Reanimated runs animations on the native UI thread via worklets. JavaScript thread congestion does not affect animation frame rate.

### Shared Values

Shared values are the bridge between JS and UI threads:

```typescript
import { useSharedValue, useAnimatedStyle, withSpring } from 'react-native-reanimated';
import Animated from 'react-native-reanimated';

function AnimatedBox() {
  const offset = useSharedValue(0);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: offset.value }],
  }));

  return (
    <Animated.View style={[styles.box, animatedStyle]}>
      <Button onPress={() => { offset.value = withSpring(200); }} title="Move" />
    </Animated.View>
  );
}
```

| Concept | Description |
|---------|-------------|
| `useSharedValue` | Creates a value accessible from both JS and UI threads |
| `useAnimatedStyle` | Returns animated style that reads shared values on UI thread |
| `useDerivedValue` | Computes derived value from other shared values on UI thread |
| `useAnimatedProps` | Animated props for non-style properties (e.g., SVG) |

### Worklets

Worklets are JavaScript functions that execute on the UI thread. Mark with `'worklet'` directive:

```typescript
import { runOnUI, runOnJS } from 'react-native-reanimated';

function myWorklet() {
  'worklet';
  // Runs on UI thread
  const result = Math.sin(Date.now());
  // Call back to JS thread if needed
  runOnJS(handleResult)(result);
}

// Trigger from JS thread
runOnUI(myWorklet)();
```

Worklets cannot access JS thread closures directly. Pass data through shared values or `runOnJS` callbacks.

### Animation Functions

| Function | Behavior | Use Case |
|----------|----------|----------|
| `withSpring(target, config?)` | Spring physics (bouncy) | Natural-feeling movements |
| `withTiming(target, config?)` | Duration-based easing | Precise timed transitions |
| `withDecay(config)` | Velocity-based deceleration | Fling gestures, momentum |
| `withDelay(ms, animation)` | Delays animation start | Staggered sequences |
| `withSequence(...anims)` | Runs animations in order | Multi-step transitions |
| `withRepeat(anim, count, reverse?)` | Loops animation | Pulsing, loading indicators |

### Spring Configuration

```typescript
import { withSpring, WithSpringConfig } from 'react-native-reanimated';

// Responsive, snappy (buttons, toggles)
const snappy: WithSpringConfig = {
  damping: 15,
  stiffness: 150,
  mass: 0.5,
};

// Gentle, smooth (page transitions)
const gentle: WithSpringConfig = {
  damping: 20,
  stiffness: 80,
  mass: 1,
};

// Bouncy (playful elements)
const bouncy: WithSpringConfig = {
  damping: 8,
  stiffness: 100,
  mass: 0.8,
};

offset.value = withSpring(100, snappy);
```

### Timing Configuration

```typescript
import { withTiming, Easing } from 'react-native-reanimated';

// Standard ease-in-out
offset.value = withTiming(100, {
  duration: 300,
  easing: Easing.bezier(0.25, 0.1, 0.25, 1),
});

// Common easing presets
Easing.linear          // Constant speed
Easing.ease            // Subtle ease
Easing.bezier(a,b,c,d) // Custom cubic bezier
Easing.in(Easing.quad)  // Accelerate
Easing.out(Easing.quad)  // Decelerate
Easing.inOut(Easing.quad) // Both
```

## Layout Animations

Animate components when they enter, exit, or change layout position:

```typescript
import Animated, { FadeIn, FadeOut, Layout } from 'react-native-reanimated';

function AnimatedList({ items }) {
  return (
    <View>
      {items.map((item) => (
        <Animated.View
          key={item.id}
          entering={FadeIn.duration(300)}
          exiting={FadeOut.duration(200)}
          layout={Layout.springify()}
        >
          <ListItem item={item} />
        </Animated.View>
      ))}
    </View>
  );
}
```

### Built-in Entering Animations

| Animation | Effect |
|-----------|--------|
| `FadeIn` | Opacity 0 to 1 |
| `SlideInRight` | Slide from right edge |
| `SlideInLeft` | Slide from left edge |
| `SlideInUp` | Slide from bottom |
| `SlideInDown` | Slide from top |
| `ZoomIn` | Scale from 0 to 1 |
| `BounceIn` | Bounce entrance |
| `FlipInXUp` | 3D flip on X axis |
| `StretchInX` | Stretch horizontally |
| `LightSpeedInRight` | Speed entrance from right |

Each has a corresponding exiting variant (`FadeOut`, `SlideOutRight`, etc.).

### Chaining Modifiers

```typescript
FadeIn
  .delay(200)           // Wait 200ms before starting
  .duration(400)        // Animation takes 400ms
  .springify()          // Use spring physics instead of timing
  .damping(15)          // Spring damping
  .withInitialValues({ opacity: 0.5 })  // Start from custom value
  .withCallback((finished) => {
    'worklet';
    if (finished) console.log('Animation done');
  });
```

### Custom Entering/Exiting

```typescript
import { EntryAnimationsValues, withTiming } from 'react-native-reanimated';

function customEntering(values: EntryAnimationsValues) {
  'worklet';
  const animations = {
    opacity: withTiming(1, { duration: 300 }),
    transform: [
      { translateY: withTiming(0, { duration: 400 }) },
      { scale: withTiming(1, { duration: 300 }) },
    ],
  };
  const initialValues = {
    opacity: 0,
    transform: [{ translateY: -50 }, { scale: 0.9 }],
  };
  return { initialValues, animations };
}

<Animated.View entering={customEntering} />
```

## Gesture Handler v2

React Native Gesture Handler v2 provides a declarative gesture system that composes naturally with Reanimated.

### Basic Gesture

```typescript
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from 'react-native-reanimated';

function DraggableBox() {
  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);
  const savedX = useSharedValue(0);
  const savedY = useSharedValue(0);

  const pan = Gesture.Pan()
    .onStart(() => {
      savedX.value = translateX.value;
      savedY.value = translateY.value;
    })
    .onUpdate((event) => {
      translateX.value = savedX.value + event.translationX;
      translateY.value = savedY.value + event.translationY;
    })
    .onEnd(() => {
      translateX.value = withSpring(0);
      translateY.value = withSpring(0);
    });

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: translateX.value },
      { translateY: translateY.value },
    ],
  }));

  return (
    <GestureDetector gesture={pan}>
      <Animated.View style={[styles.box, animatedStyle]} />
    </GestureDetector>
  );
}
```

### Gesture Types

| Gesture | Use Case | Key Events |
|---------|----------|-----------|
| `Gesture.Pan()` | Drag, swipe, scroll | onUpdate (translationX/Y, velocityX/Y) |
| `Gesture.Tap()` | Single/double tap | onEnd |
| `Gesture.LongPress()` | Press and hold | onStart, onEnd |
| `Gesture.Pinch()` | Zoom in/out | onUpdate (scale, focalX/Y) |
| `Gesture.Rotation()` | Rotate element | onUpdate (rotation) |
| `Gesture.Fling()` | Quick swipe | onEnd (direction) |

### Gesture Composition

Combine gestures to create complex interactions:

```typescript
// Simultaneous: pinch + rotation at the same time
const pinch = Gesture.Pinch().onUpdate((e) => {
  scale.value = savedScale.value * e.scale;
});

const rotation = Gesture.Rotation().onUpdate((e) => {
  rotationVal.value = savedRotation.value + e.rotation;
});

const composed = Gesture.Simultaneous(pinch, rotation);

// Exclusive: tap OR long press (first recognized wins)
const tap = Gesture.Tap().onEnd(() => { /* handle tap */ });
const longPress = Gesture.LongPress().onStart(() => { /* handle long press */ });
const exclusive = Gesture.Exclusive(longPress, tap);

// Race: first gesture to activate wins, others cancelled
const race = Gesture.Race(pan, fling);
```

### Gesture + Animation Patterns

#### Swipe-to-Delete

```typescript
const translateX = useSharedValue(0);
const THRESHOLD = -100;

const pan = Gesture.Pan()
  .activeOffsetX([-10, 10])
  .onUpdate((e) => {
    translateX.value = Math.min(0, e.translationX);
  })
  .onEnd((e) => {
    if (translateX.value < THRESHOLD) {
      translateX.value = withTiming(-200, {}, () => {
        runOnJS(onDelete)(item.id);
      });
    } else {
      translateX.value = withSpring(0);
    }
  });
```

#### Pull-to-Refresh

```typescript
const translateY = useSharedValue(0);
const REFRESH_THRESHOLD = 80;

const pan = Gesture.Pan()
  .onUpdate((e) => {
    if (e.translationY > 0) {
      translateY.value = e.translationY * 0.5; // Resistance factor
    }
  })
  .onEnd(() => {
    if (translateY.value > REFRESH_THRESHOLD) {
      translateY.value = withTiming(REFRESH_THRESHOLD);
      runOnJS(onRefresh)();
    } else {
      translateY.value = withSpring(0);
    }
  });
```

## Performance Patterns

### Rules for 60fps Animations

1. **All animation logic in worklets** — Never update shared values from JS callbacks
2. **Avoid `runOnJS` in animation loops** — Use only for final callbacks (onEnd)
3. **Use `useAnimatedStyle` not inline styles** — Inline reanimated styles recompute every frame
4. **Prefer spring over timing** — Springs handle interruption naturally
5. **Cancel previous animations** — `cancelAnimation(sharedValue)` before starting new ones

### Common Performance Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Animating with `setState` | Janky, 10-20fps | Use `useSharedValue` + `useAnimatedStyle` |
| Heavy JS during animation | Dropped frames | Move computation to worklets |
| Animating `width`/`height` | Layout recalculation | Animate `transform: scale` instead |
| Too many animated views | Memory pressure | Limit to visible items, use FlatList |
| Missing `GestureHandlerRootView` | Gestures silently fail | Wrap root component |

### Setup

Install both libraries together:

```bash
npx expo install react-native-reanimated react-native-gesture-handler
```

Add Reanimated Babel plugin:

```javascript
// babel.config.js
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: ['react-native-reanimated/plugin'], // Must be last
  };
};
```

Wrap app root with `GestureHandlerRootView`:

```typescript
import { GestureHandlerRootView } from 'react-native-gesture-handler';

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <Stack />
    </GestureHandlerRootView>
  );
}
```
