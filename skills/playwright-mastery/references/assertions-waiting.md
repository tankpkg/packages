# Assertions and Auto-Waiting

Sources: Playwright official documentation (playwright.dev, 2024-2026), Microsoft Playwright GitHub repository, Playwright test-assertions API reference

Covers: web-first assertions, auto-waiting mechanism, actionability checks, expect() API, soft assertions, polling assertions, custom matchers, and timeout configuration.

## Auto-Waiting Mechanism

Every Playwright action automatically waits for the target element to be actionable before performing the operation. This eliminates the most common source of test flakiness.

### Actionability Checks

Before performing an action, Playwright verifies these conditions (varies by action type):

| Check | Description | Actions |
|-------|-------------|---------|
| Attached | Element exists in the DOM | All actions |
| Visible | Element has non-zero size and is not hidden | click, hover, fill, check |
| Stable | Element is not animating (bounding box unchanged across two animation frames) | click, hover |
| Enabled | Element is not disabled | click, fill, check, selectOption |
| Editable | Element is an editable input/textarea/contenteditable | fill, type |
| Receives events | Element is not obscured by another element at the action point | click |

### Action-Specific Checks

| Action | Attached | Visible | Stable | Enabled | Editable | Receives Events |
|--------|----------|---------|--------|---------|----------|----------------|
| `click()` | Yes | Yes | Yes | Yes | - | Yes |
| `fill()` | Yes | Yes | - | Yes | Yes | - |
| `check()` | Yes | Yes | Yes | Yes | - | Yes |
| `hover()` | Yes | Yes | Yes | - | - | Yes |
| `selectOption()` | Yes | Yes | - | Yes | - | - |
| `textContent()` | Yes | - | - | - | - | - |
| `isVisible()` | - | - | - | - | - | - |

### Timeouts

Configure the action timeout at multiple levels:

```typescript
// Global default (playwright.config.ts)
export default defineConfig({
  timeout: 30000,               // Test timeout (includes all actions)
  expect: { timeout: 5000 },    // Assertion timeout
  use: {
    actionTimeout: 10000,       // Per-action timeout
    navigationTimeout: 30000,   // Navigation timeout
  },
});

// Per-test override
test('slow page', async ({ page }) => {
  test.setTimeout(60000);
  // ...
});

// Per-action override
await page.getByRole('button').click({ timeout: 15000 });

// Per-assertion override
await expect(page.getByText('Done')).toBeVisible({ timeout: 10000 });
```

Timeout precedence: per-call > test.setTimeout > config timeout.

## Web-First Assertions

Web-first assertions auto-retry until the condition is met or the timeout expires. Always prefer them over manual checks.

### Page Assertions

```typescript
// URL
await expect(page).toHaveURL('https://example.com/dashboard');
await expect(page).toHaveURL(/\/dashboard/);

// Title
await expect(page).toHaveTitle('Dashboard - MyApp');
await expect(page).toHaveTitle(/Dashboard/);

// Visual comparison
await expect(page).toHaveScreenshot('dashboard.png');
await expect(page).toHaveScreenshot({ maxDiffPixelRatio: 0.01 });
```

### Locator Assertions

| Assertion | Description | Example |
|-----------|-------------|---------|
| `toBeVisible()` | Element is visible | `expect(dialog).toBeVisible()` |
| `toBeHidden()` | Element is hidden or detached | `expect(dialog).toBeHidden()` |
| `toBeEnabled()` | Element is enabled | `expect(button).toBeEnabled()` |
| `toBeDisabled()` | Element is disabled | `expect(button).toBeDisabled()` |
| `toBeChecked()` | Checkbox is checked | `expect(checkbox).toBeChecked()` |
| `toBeEditable()` | Input is editable | `expect(input).toBeEditable()` |
| `toBeEmpty()` | Element has no text | `expect(input).toBeEmpty()` |
| `toBeFocused()` | Element has focus | `expect(input).toBeFocused()` |
| `toBeAttached()` | Element exists in DOM | `expect(el).toBeAttached()` |
| `toBeInViewport()` | Element is in viewport | `expect(el).toBeInViewport()` |
| `toHaveText()` | Element text matches | `expect(el).toHaveText('Hello')` |
| `toContainText()` | Element text contains | `expect(el).toContainText('ello')` |
| `toHaveValue()` | Input value matches | `expect(input).toHaveValue('test')` |
| `toHaveValues()` | Multi-select values | `expect(select).toHaveValues(['a', 'b'])` |
| `toHaveAttribute()` | Has attribute with value | `expect(el).toHaveAttribute('href', '/home')` |
| `toHaveClass()` | Has CSS class | `expect(el).toHaveClass(/active/)` |
| `toHaveCSS()` | CSS property matches | `expect(el).toHaveCSS('color', 'rgb(0,0,0)')` |
| `toHaveCount()` | Number of matching elements | `expect(items).toHaveCount(5)` |
| `toHaveId()` | Element has ID | `expect(el).toHaveId('main')` |
| `toHaveScreenshot()` | Visual comparison | `expect(el).toHaveScreenshot()` |
| `toHaveAccessibleName()` | ARIA accessible name | `expect(btn).toHaveAccessibleName('Submit')` |
| `toHaveAccessibleDescription()` | ARIA description | `expect(btn).toHaveAccessibleDescription('...')` |
| `toHaveRole()` | ARIA role matches | `expect(el).toHaveRole('button')` |

### Text Matching Options

```typescript
// Substring match (default for toContainText)
await expect(locator).toContainText('welcome');

// Exact match
await expect(locator).toHaveText('Welcome, John!', { exact: true });

// Regex
await expect(locator).toHaveText(/welcome, \w+/i);

// Array of texts (for lists)
await expect(page.getByRole('listitem')).toHaveText([
  'First item',
  'Second item',
  'Third item',
]);

// Ignore case
await expect(locator).toHaveText('HELLO', { ignoreCase: true });
```

### Negation

Prefix any assertion with `.not` to negate:

```typescript
await expect(page.getByRole('dialog')).not.toBeVisible();
await expect(page.getByTestId('error')).not.toBeAttached();
await expect(page).not.toHaveURL(/login/);
```

## Soft Assertions

Soft assertions do not terminate the test on failure. Collect all failures and report at test end.

```typescript
await expect.soft(page.getByTestId('status')).toHaveText('Active');
await expect.soft(page.getByTestId('name')).toHaveText('John');
await expect.soft(page.getByTestId('email')).toHaveText('john@test.com');
// Test continues even if above assertions fail
// All failures reported at test end
```

Check if any soft assertion failed mid-test:

```typescript
await expect.soft(locator).toHaveText('Expected');
if (test.info().errors.length) {
  // Some soft assertion already failed — skip remaining steps
  return;
}
```

## Polling Assertions

For values not tied to locators, use `expect.poll()` to retry a callback:

```typescript
// Poll an API until condition is met
await expect.poll(async () => {
  const response = await page.request.get('/api/status');
  return response.json();
}, {
  message: 'API should return ready status',
  timeout: 30000,
  intervals: [1000, 2000, 5000],
}).toEqual({ status: 'ready' });
```

For a callback that must eventually succeed:

```typescript
await expect(async () => {
  const response = await page.request.get('/api/data');
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.items.length).toBeGreaterThan(0);
}).toPass({
  timeout: 30000,
  intervals: [1000, 2000, 5000],
});
```

## Custom Matchers

Extend the expect API with project-specific assertions:

```typescript
// custom-matchers.ts
import { expect as baseExpect } from '@playwright/test';
import type { Locator } from '@playwright/test';

export const expect = baseExpect.extend({
  async toHaveErrorState(locator: Locator) {
    const assertionName = 'toHaveErrorState';
    let pass: boolean;
    try {
      await baseExpect(locator).toHaveClass(/error|invalid/);
      pass = true;
    } catch {
      pass = false;
    }
    return {
      message: () => `expected element ${pass ? 'not ' : ''}to have error state`,
      pass,
      name: assertionName,
    };
  },
});

// Usage
await expect(page.getByLabel('Email')).toHaveErrorState();
await expect(page.getByLabel('Name')).not.toHaveErrorState();
```

## APIResponse Assertions

Assert on API responses from the `request` fixture:

```typescript
const response = await page.request.get('/api/users');
await expect(response).toBeOK();             // Status 200-299
await expect(response).not.toBeOK();          // Status outside 200-299
```

For deeper validation, use standard expect on parsed body:

```typescript
const body = await response.json();
expect(body.users).toHaveLength(3);
expect(body.users[0]).toMatchObject({ name: 'Alice' });
```

## Retrying vs Non-Retrying Assertions

| Pattern | Retrying | Use When |
|---------|----------|----------|
| `await expect(locator).toHaveText('...')` | Yes | Asserting on live page elements |
| `expect(await locator.textContent()).toBe('...')` | No | Value already resolved |
| `expect(response.status()).toBe(200)` | No | API response already received |
| `await expect.poll(() => getValue()).toBe(5)` | Yes | Non-locator values that change |

Always prefer retrying assertions for anything on the page. Non-retrying assertions create race conditions when the DOM is still updating.

## Common Assertion Mistakes

| Mistake | Problem | Correct |
|---------|---------|---------|
| `expect(await el.isVisible()).toBe(true)` | No auto-retry, snapshot of single moment | `await expect(el).toBeVisible()` |
| `expect(await el.textContent()).toBe('Hello')` | No retry if text hasn't updated yet | `await expect(el).toHaveText('Hello')` |
| `await page.waitForTimeout(3000)` | Arbitrary wait, still flaky | `await expect(el).toBeVisible()` |
| `if (await el.count() > 0)` | Race condition — count can change | `await expect(el).toHaveCount(n)` |
| `expect(el).toHaveText('...')` (missing await) | Assertion never executes | `await expect(el).toHaveText('...')` |
