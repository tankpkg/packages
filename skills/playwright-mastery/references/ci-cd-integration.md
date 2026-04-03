# CI/CD Integration, Debugging, and Tooling

Sources: Playwright official documentation (playwright.dev, 2024-2026), Microsoft Playwright GitHub repository, Playwright CI and Docker guides, axe-core/playwright documentation

Covers: GitHub Actions workflows, Docker images, sharding, artifacts, visual regression in CI, Trace Viewer, codegen, mobile emulation, component testing, and accessibility testing.

## GitHub Actions Workflow

### Basic Workflow

```yaml
name: Playwright Tests
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  test:
    timeout-minutes: 30
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 14
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: test-traces
          path: test-results/
          retention-days: 7
```

### Sharded Workflow

Split tests across multiple CI machines. Each shard runs a portion, then reports merge.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shardIndex: [1, 2, 3, 4]
        shardTotal: [4]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test --shard=${{ matrix.shardIndex }}/${{ matrix.shardTotal }}
      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with:
          name: blob-report-${{ matrix.shardIndex }}
          path: blob-report/
  merge-reports:
    needs: test
    if: ${{ !cancelled() }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - uses: actions/download-artifact@v4
        with:
          path: all-blob-reports
          pattern: blob-report-*
          merge-multiple: true
      - run: npx playwright merge-reports --reporter html ./all-blob-reports
      - uses: actions/upload-artifact@v4
        with:
          name: html-report
          path: playwright-report/
```

Configure blob reporter for sharding:

```typescript
// playwright.config.ts
reporter: process.env.CI
  ? [['blob'], ['github']]
  : [['html', { open: 'never' }]],
```

### Browser Caching

```yaml
- name: Cache Playwright browsers
  uses: actions/cache@v4
  id: playwright-cache
  with:
    path: ~/.cache/ms-playwright
    key: playwright-${{ hashFiles('package-lock.json') }}
- name: Install browsers
  if: steps.playwright-cache.outputs.cache-hit != 'true'
  run: npx playwright install --with-deps
- name: Install OS deps only
  if: steps.playwright-cache.outputs.cache-hit == 'true'
  run: npx playwright install-deps
```

## Docker

Use official images for consistent environments, especially for visual regression:

| Image | Base | Use |
|-------|------|-----|
| `mcr.microsoft.com/playwright:v1.52.0-jammy` | Ubuntu 22.04 | Standard CI |
| `mcr.microsoft.com/playwright:v1.52.0-noble` | Ubuntu 24.04 | Newer OS |

```dockerfile
FROM mcr.microsoft.com/playwright:v1.52.0-jammy
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
USER pwuser
CMD ["npx", "playwright", "test"]
```

CI configuration pattern:

```typescript
export default defineConfig({
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
});
```

## Visual Regression Testing

### Screenshot Comparison

```typescript
await expect(page).toHaveScreenshot('dashboard.png');
await expect(page.getByTestId('chart')).toHaveScreenshot('chart.png');
await expect(page).toHaveScreenshot('full.png', { fullPage: true });
```

First run creates baselines in `__snapshots__/`. Subsequent runs compare against them.

```bash
npx playwright test --update-snapshots           # Update all
npx playwright test --update-snapshots=changed    # Update only changed
```

### Comparison Options

| Option | Type | Description |
|--------|------|-------------|
| `maxDiffPixels` | number | Absolute pixel difference allowed |
| `maxDiffPixelRatio` | number | Ratio of different pixels (0-1) |
| `threshold` | number | Per-pixel color difference (0-1) |
| `animations` | `'allow'`/`'disabled'` | Disable CSS animations before capture |
| `mask` | Locator[] | Mask dynamic elements with colored boxes |
| `maskColor` | string | Color for masked elements |
| `fullPage` | boolean | Capture entire scrollable page |
| `stylePath` | string | CSS file to inject before screenshot |

### Masking Dynamic Content

```typescript
await expect(page).toHaveScreenshot('page.png', {
  mask: [
    page.getByTestId('timestamp'),
    page.getByTestId('random-avatar'),
  ],
});
```

### CI Considerations

| Problem | Solution |
|---------|----------|
| Screenshots differ across OS | Use Docker with fixed OS and fonts |
| Animations cause diffs | `animations: 'disabled'` (default) |
| Font rendering differs | Inject consistent fonts via `stylePath` |
| Dynamic content (dates, ads) | Use `mask` option |
| Flaky diffs | Increase `threshold` or `maxDiffPixelRatio` |

## Trace Viewer

### Recording Traces

| Config Value | When Recorded |
|-------------|---------------|
| `'off'` | Never |
| `'on'` | Always (large files) |
| `'retain-on-failure'` | Record always, keep only on failure |
| `'on-first-retry'` | Only on first retry (recommended for CI) |
| `'on-all-retries'` | On every retry attempt |

### Programmatic Tracing

```typescript
await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
// ... test steps ...
await context.tracing.stop({ path: 'trace.zip' });
```

### Viewing Traces

```bash
npx playwright show-trace trace.zip
# Or drag-and-drop to https://trace.playwright.dev/
```

Trace Viewer panels: Timeline (film strip), Actions (each step with timing), DOM Snapshot (interactive), Network (all requests), Console (browser output), Source (test code with current line).

### UI Mode

Interactive test runner with live browser and time-travel debugging:

```bash
npx playwright test --ui
```

## Codegen

Record browser interactions to generate test code:

```bash
npx playwright codegen https://example.com
npx playwright codegen --viewport-size=375,667 https://example.com
npx playwright codegen --target=python --output=tests/gen.spec.ts https://example.com
npx playwright codegen --load-storage=.auth/user.json https://example.com
```

Codegen produces a starting point. Refine by replacing brittle selectors with getByRole, extracting Page Objects, and adding assertions.

## Mobile Emulation

### Device Presets

```typescript
import { devices } from '@playwright/test';

projects: [
  { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },
  { name: 'tablet', use: { ...devices['iPad Pro 11'] } },
],
```

Presets include: viewport, userAgent, deviceScaleFactor, isMobile, hasTouch, defaultBrowserType.

### Custom Configuration

```typescript
test.use({
  viewport: { width: 375, height: 667 },
  isMobile: true,
  hasTouch: true,
  geolocation: { longitude: -73.935, latitude: 40.730 },
  permissions: ['geolocation'],
  locale: 'en-US',
  colorScheme: 'dark',
});
```

Note: `isMobile: true` is not supported in Firefox. Set viewport manually for Firefox mobile.

## Component Testing

Test components in isolation with `@playwright/experimental-ct-react` (or `-vue`, `-svelte`, `-solid`):

```typescript
import { test, expect } from '@playwright/experimental-ct-react';
import { Button } from './Button';

test('renders and clicks', async ({ mount }) => {
  let clicked = false;
  const component = await mount(
    <Button label="Click me" onClick={() => { clicked = true; }} />
  );
  await expect(component).toContainText('Click me');
  await component.click();
  expect(clicked).toBe(true);
});

test('updates props', async ({ mount }) => {
  const component = await mount(<Button label="Before" />);
  await component.update(<Button label="After" />);
  await expect(component).toContainText('After');
});
```

Limitations: no real router, no global app context (must wrap manually), components render in an iframe.

## Accessibility Testing

### Setup

```bash
npm install -D @axe-core/playwright
```

### Full Page and Scoped Scans

```typescript
import AxeBuilder from '@axe-core/playwright';

test('no accessibility violations', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});

test('WCAG 2.1 AA compliance', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .include('#main-content')
    .exclude('#third-party-widget')
    .analyze();
  expect(results.violations).toEqual([]);
});
```

### Keyboard Navigation Testing

```typescript
test('form is keyboard navigable', async ({ page }) => {
  await page.goto('/form');
  await page.keyboard.press('Tab');
  await expect(page.getByLabel('Name')).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(page.getByLabel('Email')).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'Submit' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByText('Form submitted')).toBeVisible();
});
```

Wait for dynamic content before scanning — axe-core scans the current DOM state:

```typescript
await page.goto('/dashboard');
await expect(page.getByRole('table')).toBeVisible();
const results = await new AxeBuilder({ page }).analyze();
```
