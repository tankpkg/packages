# Test Configuration

Sources: Playwright official documentation (playwright.dev, 2024-2026), Microsoft Playwright GitHub repository, Playwright test-configuration and test-parallel guides

Covers: playwright.config.ts structure, projects for multi-browser testing, parallelism and workers, retries, reporters, webServer, timeouts, expect options, and global setup/teardown.

## Configuration File Structure

The `playwright.config.ts` file controls all test execution behavior. Use `defineConfig` for type safety:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Test discovery
  testDir: './tests',
  testMatch: '**/*.spec.ts',
  testIgnore: '**/helpers/**',

  // Execution
  fullyParallel: true,
  workers: process.env.CI ? 1 : undefined,
  retries: process.env.CI ? 2 : 0,
  forbidOnly: !!process.env.CI,
  timeout: 30000,

  // Reporting
  reporter: [
    ['html', { open: 'never' }],
    ['json', { outputFile: 'results.json' }],
  ],
  outputDir: 'test-results',

  // Shared settings for all projects
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  // Browser configurations
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  // Dev server
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

## Top-Level Options

These options are NOT inside the `use` block:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `testDir` | string | `.` | Directory to scan for test files |
| `testMatch` | string/RegExp | `**/*.@(spec|test).?(m)[jt]s?(x)` | Pattern for test files |
| `testIgnore` | string/RegExp | `**/node_modules/**` | Pattern to exclude |
| `timeout` | number | 30000 | Test timeout in ms (includes fixtures, hooks) |
| `fullyParallel` | boolean | false | Run all tests in parallel |
| `workers` | number/string | 50% of CPUs | Max parallel workers |
| `retries` | number | 0 | Retry failed tests N times |
| `forbidOnly` | boolean | false | Fail if `test.only` exists (for CI) |
| `reporter` | string/array | `list` | Reporter configuration |
| `outputDir` | string | `test-results` | Artifact output directory |
| `globalSetup` | string | - | Path to global setup script |
| `globalTeardown` | string | - | Path to global teardown script |
| `maxFailures` | number | 0 | Stop after N test failures (0 = unlimited) |
| `repeatEach` | number | 1 | Run each test N times (stress testing) |

## Projects

Projects run the same tests with different configurations. Common patterns:

### Multi-Browser

```typescript
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },
],
```

### Mobile Viewports

```typescript
projects: [
  { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },
],
```

### Setup Dependencies

Run a setup project before other projects:

```typescript
projects: [
  {
    name: 'setup',
    testMatch: /global\.setup\.ts/,
  },
  {
    name: 'chromium',
    use: {
      ...devices['Desktop Chrome'],
      storageState: '.auth/user.json',
    },
    dependencies: ['setup'],
  },
],
```

### Filtered by Directory

```typescript
projects: [
  { name: 'unit', testDir: './tests/unit' },
  { name: 'integration', testDir: './tests/integration' },
  { name: 'e2e', testDir: './tests/e2e' },
],
```

## Parallelism and Workers

### Configuration Levels

| Level | Setting | Effect |
|-------|---------|--------|
| Config | `fullyParallel: true` | All tests across all files run in parallel |
| Config | `workers: 4` | Maximum 4 worker processes |
| Config | `workers: '50%'` | Use 50% of logical CPU cores |
| File | `test.describe.configure({ mode: 'serial' })` | Tests in block run sequentially |
| File | `test.describe.configure({ mode: 'parallel' })` | Tests in block run in parallel |

### Worker Process Model

Each worker process runs test files independently. Workers share no state.

```
Worker 1: file-a.spec.ts → file-d.spec.ts
Worker 2: file-b.spec.ts → file-e.spec.ts
Worker 3: file-c.spec.ts → file-f.spec.ts
```

Within a file, tests run sequentially by default unless `fullyParallel` is enabled.

### Serial Mode

Force sequential execution for tests that depend on shared state:

```typescript
test.describe.configure({ mode: 'serial' });

test('step 1: create user', async ({ page }) => { /* ... */ });
test('step 2: verify user', async ({ page }) => { /* ... */ });
test('step 3: delete user', async ({ page }) => { /* ... */ });
// If step 1 fails, steps 2 and 3 are skipped
```

## Retries

```typescript
export default defineConfig({
  retries: 2,  // Retry failed tests up to 2 times
});
```

Detect retry in tests:

```typescript
test('may be flaky', async ({ page }, testInfo) => {
  if (testInfo.retry > 0) {
    // Clear state before retry
    await page.evaluate(() => localStorage.clear());
  }
  // ...
});
```

### Retry Categories

| testInfo Property | Meaning |
|-------------------|---------|
| `testInfo.retry` | Current retry attempt (0 = first run) |
| `testInfo.status` | Test status: `passed`, `failed`, `timedOut`, `skipped`, `interrupted` |
| `testInfo.expectedStatus` | Expected status (usually `passed`, `skipped` for skip) |

## Reporters

### Built-in Reporters

| Reporter | Output | Use For |
|----------|--------|---------|
| `list` | Console list | Local development (default) |
| `line` | Compact console | CI with many tests |
| `dot` | Minimal dots | CI, quick summary |
| `html` | Interactive HTML report | Detailed investigation |
| `json` | JSON file | Parsing in other tools |
| `junit` | JUnit XML | CI systems (Jenkins, GitLab) |
| `blob` | Binary blob | Merge sharded results |
| `github` | GitHub annotations | GitHub Actions |

### Multiple Reporters

```typescript
reporter: [
  ['list'],
  ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ['junit', { outputFile: 'results.xml' }],
],
```

### Custom Reporter

```typescript
reporter: [
  ['./my-reporter.ts'],
],
```

## Use Options

Options inside `use` are shared with all test fixtures:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `baseURL` | string | - | Base URL for `page.goto('/')` |
| `headless` | boolean | true | Run browsers headless |
| `viewport` | object | 1280x720 | Browser viewport size |
| `ignoreHTTPSErrors` | boolean | false | Ignore SSL errors |
| `locale` | string | - | Browser locale |
| `timezoneId` | string | - | Timezone |
| `geolocation` | object | - | Geolocation override |
| `permissions` | string[] | - | Browser permissions to grant |
| `colorScheme` | string | - | `light`, `dark`, or `no-preference` |
| `userAgent` | string | - | Custom user agent |
| `storageState` | string/object | - | Auth state file path or object |
| `testIdAttribute` | string | `data-testid` | Custom test ID attribute |
| `actionTimeout` | number | 0 | Timeout for each action |
| `navigationTimeout` | number | 0 | Timeout for navigations |

### Artifact Options

| Option | Values | Description |
|--------|--------|-------------|
| `screenshot` | `off`, `on`, `only-on-failure` | When to capture screenshots |
| `video` | `off`, `on`, `retain-on-failure`, `on-first-retry` | When to record video |
| `trace` | `off`, `on`, `retain-on-failure`, `on-first-retry`, `on-all-retries` | When to record traces |

Recommended CI configuration:

```typescript
use: {
  trace: 'on-first-retry',
  screenshot: 'only-on-failure',
  video: 'retain-on-failure',
},
```

## webServer

Launch a dev server before tests:

```typescript
webServer: {
  command: 'npm run start',
  url: 'http://localhost:3000',
  reuseExistingServer: !process.env.CI,
  timeout: 120000,
  stdout: 'pipe',
  stderr: 'pipe',
  env: { PORT: '3000' },
},
```

Multiple servers:

```typescript
webServer: [
  { command: 'npm run start:api', url: 'http://localhost:4000' },
  { command: 'npm run start:web', url: 'http://localhost:3000' },
],
```

## Global Setup and Teardown

Run scripts before/after all tests:

```typescript
// playwright.config.ts
export default defineConfig({
  globalSetup: require.resolve('./global-setup'),
  globalTeardown: require.resolve('./global-teardown'),
});
```

```typescript
// global-setup.ts
import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:3000/login');
  await page.getByLabel('Email').fill('admin@test.com');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Login' }).click();
  await page.context().storageState({ path: '.auth/admin.json' });
  await browser.close();
}

export default globalSetup;
```

For authentication, prefer setup projects over globalSetup — they support retries and parallelism. See `references/authentication-state.md`.

## Expect Options

```typescript
export default defineConfig({
  expect: {
    timeout: 5000,
    toHaveScreenshot: {
      maxDiffPixels: 10,
      maxDiffPixelRatio: 0.01,
      threshold: 0.2,
      animations: 'disabled',
    },
    toMatchSnapshot: {
      maxDiffPixelRatio: 0.1,
    },
  },
});
```

## Per-File and Per-Test Overrides

```typescript
// Override for entire file
test.use({ viewport: { width: 375, height: 667 } });

// Override for a describe block
test.describe('mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('responsive layout', async ({ page }) => { /* ... */ });
});

// Override timeout for a single test
test('slow test', async ({ page }) => {
  test.setTimeout(120000);
  // ...
});
```

## Sharding

Split tests across multiple CI machines:

```bash
# Machine 1
npx playwright test --shard=1/4

# Machine 2
npx playwright test --shard=2/4

# Machine 3
npx playwright test --shard=3/4

# Machine 4
npx playwright test --shard=4/4
```

Merge results from shards:

```bash
npx playwright merge-reports --reporter html ./shard-results/
```

Use `blob` reporter on each shard, then merge for the final HTML report. See `references/ci-cd-integration.md` for full CI workflow.
