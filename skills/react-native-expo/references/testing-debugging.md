# Testing and Debugging

Sources: React Native Testing Library documentation (2025), Jest documentation, Detox documentation (Wix, 2025-2026), Maestro documentation, Expo DevTools documentation, Hermes profiling guide

Covers: unit and component testing with Jest and RNTL, E2E testing with Detox and Maestro, debugging tools and workflows, Hermes profiling, common crash patterns, and CI integration for mobile tests.

## Testing Strategy

| Layer | Tool | What to Test | Speed |
|-------|------|-------------|-------|
| Unit | Jest | Pure functions, hooks, utilities | Milliseconds |
| Component | Jest + RNTL | Render output, user interactions | Seconds |
| Integration | Jest + RNTL + MSW | Screens with mocked API | Seconds |
| E2E | Detox or Maestro | Full app flows on device/simulator | Minutes |

### Testing Pyramid for React Native

Invest in component tests as the primary layer. They catch most bugs with reasonable speed:

| Layer | Coverage Target | Rationale |
|-------|----------------|-----------|
| Unit tests | 20% of test suite | Logic-heavy utilities, complex hooks |
| Component tests | 60% of test suite | Primary value: catches render + interaction bugs |
| E2E tests | 20% of test suite | Critical user flows only (auth, purchase, onboarding) |

## Jest + React Native Testing Library

### Setup

```bash
npx expo install jest-expo @testing-library/react-native @testing-library/jest-native
```

```json
// package.json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  },
  "jest": {
    "preset": "jest-expo",
    "transformIgnorePatterns": [
      "node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@sentry/react-native|native-base|react-native-svg)"
    ],
    "setupFilesAfterSetup": ["@testing-library/jest-native/extend-expect"]
  }
}
```

### Component Test

```typescript
// components/__tests__/LoginForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { LoginForm } from '../LoginForm';

describe('LoginForm', () => {
  it('shows validation errors for empty fields', async () => {
    const onSubmit = jest.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    fireEvent.press(screen.getByText('Login'));

    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeTruthy();
      expect(screen.getByText('Password is required')).toBeTruthy();
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('submits with valid data', async () => {
    const onSubmit = jest.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    fireEvent.changeText(screen.getByPlaceholderText('Email'), 'user@test.com');
    fireEvent.changeText(screen.getByPlaceholderText('Password'), 'password123');
    fireEvent.press(screen.getByText('Login'));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        email: 'user@test.com',
        password: 'password123',
      });
    });
  });
});
```

### Testing Hooks

```typescript
import { renderHook, act } from '@testing-library/react-native';
import { useCounter } from '../useCounter';

test('increments counter', () => {
  const { result } = renderHook(() => useCounter());

  expect(result.current.count).toBe(0);

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});
```

### Mocking Navigation

```typescript
const mockPush = jest.fn();
const mockBack = jest.fn();

jest.mock('expo-router', () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
  useLocalSearchParams: () => ({ id: '123' }),
  Link: ({ children }: any) => children,
}));
```

### Mocking API with MSW

```typescript
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const server = setupServer(
  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({ id: params.id, name: 'Alice' });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### RNTL Query Priority

Use queries in this order for maintainable tests:

| Priority | Query | When |
|----------|-------|------|
| 1 | `getByRole` | Accessible elements (buttons, headings) |
| 2 | `getByText` | Visible text content |
| 3 | `getByPlaceholderText` | Input fields |
| 4 | `getByDisplayValue` | Filled inputs |
| 5 | `getByTestId` | Last resort, no semantic match |

## Detox (E2E Testing)

Native E2E testing framework by Wix. Tests run on real simulators/emulators with gray-box access.

### Setup

```bash
npm install --save-dev detox @types/detox
npx detox init
```

```json
// .detoxrc.js
module.exports = {
  testRunner: {
    args: { config: 'e2e/jest.config.js' },
    jest: { setupTimeout: 120000 },
  },
  apps: {
    'ios.debug': {
      type: 'ios.app',
      binaryPath: 'ios/build/Build/Products/Debug-iphonesimulator/MyApp.app',
      build: 'xcodebuild -workspace ios/MyApp.xcworkspace -scheme MyApp -configuration Debug -sdk iphonesimulator -derivedDataPath ios/build',
    },
    'android.debug': {
      type: 'android.apk',
      binaryPath: 'android/app/build/outputs/apk/debug/app-debug.apk',
      build: 'cd android && ./gradlew assembleDebug assembleAndroidTest -DtestBuildType=debug',
    },
  },
  devices: {
    simulator: { type: 'ios.simulator', device: { type: 'iPhone 16' } },
    emulator: { type: 'android.emulator', device: { avdName: 'Pixel_7_API_34' } },
  },
  configurations: {
    'ios.debug': { device: 'simulator', app: 'ios.debug' },
    'android.debug': { device: 'emulator', app: 'android.debug' },
  },
};
```

### Detox Test

```typescript
// e2e/login.test.ts
describe('Login Flow', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
  });

  it('should login with valid credentials', async () => {
    await element(by.id('email-input')).typeText('user@test.com');
    await element(by.id('password-input')).typeText('password123');
    await element(by.id('login-button')).tap();

    await waitFor(element(by.text('Welcome back')))
      .toBeVisible()
      .withTimeout(5000);
  });

  it('should show error for invalid credentials', async () => {
    await element(by.id('email-input')).clearText();
    await element(by.id('email-input')).typeText('wrong@test.com');
    await element(by.id('password-input')).clearText();
    await element(by.id('password-input')).typeText('wrong');
    await element(by.id('login-button')).tap();

    await expect(element(by.text('Invalid credentials'))).toBeVisible();
  });
});
```

### Detox Commands

```bash
# Build for testing
npx detox build --configuration ios.debug

# Run tests
npx detox test --configuration ios.debug

# Run specific test file
npx detox test --configuration ios.debug e2e/login.test.ts
```

## Maestro (E2E Alternative)

Declarative E2E testing with YAML. Simpler setup than Detox, no native build step.

### Maestro Flow

```yaml
# e2e/login.yaml
appId: com.myapp
---
- launchApp
- tapOn: "Email"
- inputText: "user@test.com"
- tapOn: "Password"
- inputText: "password123"
- tapOn: "Login"
- assertVisible: "Welcome back"
```

### Maestro Commands

```bash
# Run a flow
maestro test e2e/login.yaml

# Run all flows in directory
maestro test e2e/

# Record a flow interactively
maestro record

# Run on CI (cloud)
maestro cloud --app-file app.apk e2e/
```

### Detox vs Maestro

| Dimension | Detox | Maestro |
|-----------|-------|---------|
| Language | TypeScript/JavaScript | YAML |
| Setup complexity | High (native build) | Low (install CLI) |
| Gray-box access | Yes (direct native APIs) | No (black-box) |
| Flakiness handling | Built-in sync, waitFor | Auto-wait, retry |
| CI integration | Custom setup | Maestro Cloud |
| Platform support | iOS + Android | iOS + Android + Web |
| Best for | Complex native interactions | Standard UI flows |

## Debugging Tools

### Expo DevTools (Recommended)

```bash
# Start with DevTools
npx expo start

# Press j for debugger
# Press r for reload
# Press m for dev menu
```

### React DevTools

```bash
# Install globally
npm install -g react-devtools

# Launch (connects automatically to running app)
react-devtools
```

Inspect component tree, props, state, and hooks. The Profiler tab shows render timing.

### Debugging Strategies by Problem Type

| Problem | Tool | Approach |
|---------|------|---------|
| Component not rendering | React DevTools | Inspect tree, check props/state |
| API data issues | Network inspector (DevTools) | Check request/response |
| Performance jank | React DevTools Profiler | Find unnecessary re-renders |
| Native crash | Xcode/Android Studio logs | Read native stack trace |
| JS error | LogBox + console | Read error boundary output |
| Layout issues | Dev menu > Inspector | Visual layout debugging |
| Memory leak | Hermes profiler | Heap snapshots |
| Animation jank | Perf Monitor (dev menu) | Check frame rate |

### Hermes Profiling

Hermes is the default JS engine. Profile with Chrome DevTools:

```bash
# Start Metro with Hermes debugging
npx expo start

# Open Chrome, navigate to:
# chrome://inspect
# Click "inspect" on the Hermes target
```

### LogBox Configuration

```typescript
import { LogBox } from 'react-native';

// Ignore specific warnings (use sparingly)
LogBox.ignoreLogs([
  'ViewPropTypes will be removed',
  'Sending `onAnimatedValueUpdate`',
]);

// Disable LogBox entirely in production
if (__DEV__) {
  // LogBox is only active in development
}
```

## Common Crash Patterns

| Crash | Cause | Fix |
|-------|-------|-----|
| "Text strings must be rendered within a Text" | Raw string outside `<Text>` | Wrap all text in `<Text>` |
| "VirtualizedLists should never be nested" | ScrollView wrapping FlatList | Use FlatList header/footer props |
| "Cannot update component from inside function" | setState during render | Move to useEffect or event handler |
| White screen (no error) | Unhandled promise rejection | Add error boundaries, catch async errors |
| "Invariant Violation: requireNativeComponent" | Missing native module | Run `npx expo prebuild --clean` |
| OOM crash on Android | Large image list without recycling | Use FlashList, resize images |

## CI Integration

### GitHub Actions for Tests

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npm test -- --coverage
      - uses: codecov/codecov-action@v4

  e2e-maestro:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: brew install maestro
      - run: npx expo prebuild --platform ios
      - run: maestro test e2e/
```
