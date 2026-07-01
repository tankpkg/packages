# Locators and Selectors

Sources: Playwright official documentation (playwright.dev, 2024-2026), Microsoft Playwright GitHub repository, W3C WAI-ARIA 1.2 specification

Covers: locator hierarchy and selection strategy, built-in locator methods, filtering and chaining, Shadow DOM traversal, strictness rules, and locator best practices.

## Locator Philosophy

Locators represent a way to find elements on the page at any moment. Unlike static selectors, a locator re-queries the DOM on every action. This means if the DOM changes between two calls on the same locator, each call finds the current element.

```typescript
const button = page.getByRole('button', { name: 'Submit' });
await button.hover();  // Finds element now
await button.click();  // Finds element again — may be a different DOM node
```

## Locator Hierarchy

Prefer locators in this order. Higher = more resilient to refactors.

| Priority | Locator | Use For | Example |
|----------|---------|---------|---------|
| 1 | `getByRole()` | Interactive elements | `getByRole('button', { name: 'Save' })` |
| 2 | `getByLabel()` | Form inputs with labels | `getByLabel('Email address')` |
| 3 | `getByPlaceholder()` | Inputs without labels | `getByPlaceholder('Search...')` |
| 4 | `getByText()` | Non-interactive text content | `getByText('Welcome back')` |
| 5 | `getByAltText()` | Images | `getByAltText('Company logo')` |
| 6 | `getByTitle()` | Elements with title attr | `getByTitle('Close dialog')` |
| 7 | `getByTestId()` | Explicit test contracts | `getByTestId('nav-menu')` |
| 8 | `locator()` | CSS/XPath as last resort | `locator('.custom-widget')` |

## Built-in Locator Methods

### getByRole

The primary locator. Maps to ARIA roles — how users and assistive technology perceive the page.

```typescript
// Button (explicit or implicit via <button>)
await page.getByRole('button', { name: 'Submit' }).click();

// Heading with level
await expect(page.getByRole('heading', { name: 'Settings', level: 2 })).toBeVisible();

// Checkbox
await page.getByRole('checkbox', { name: 'Accept terms' }).check();

// Link
await page.getByRole('link', { name: 'Documentation' }).click();

// Combobox (select dropdown)
await page.getByRole('combobox', { name: 'Country' }).selectOption('US');

// Navigation landmark
const nav = page.getByRole('navigation');

// Table with accessible name
const table = page.getByRole('table', { name: 'User list' });
```

Common ARIA roles: `alert`, `button`, `checkbox`, `combobox`, `dialog`, `heading`, `img`, `link`, `list`, `listitem`, `menuitem`, `navigation`, `progressbar`, `radio`, `region`, `row`, `slider`, `tab`, `tabpanel`, `textbox`, `tree`, `treeitem`.

Role options:

| Option | Type | Description |
|--------|------|-------------|
| `name` | string or RegExp | Accessible name (case-insensitive substring by default) |
| `exact` | boolean | Require exact name match |
| `checked` | boolean | Filter by checked state |
| `disabled` | boolean | Filter by disabled state |
| `expanded` | boolean | Filter by expanded state |
| `includeHidden` | boolean | Include hidden elements |
| `level` | number | Heading level (1-6) |
| `pressed` | boolean | Filter by pressed state |
| `selected` | boolean | Filter by selected state |

### getByLabel

Locate form controls by their associated label text. Works with `<label>` elements, `aria-label`, and `aria-labelledby`.

```typescript
await page.getByLabel('Username').fill('admin');
await page.getByLabel('Password').fill('secret');
await page.getByLabel(/remember me/i).check();
```

### getByText

Locate elements by text content. Use for non-interactive elements (div, span, p). For interactive elements, prefer getByRole.

```typescript
// Substring match (default)
await expect(page.getByText('Welcome')).toBeVisible();

// Exact match
await expect(page.getByText('Welcome, John', { exact: true })).toBeVisible();

// Regex match
await expect(page.getByText(/order #\d+/i)).toBeVisible();
```

Text matching normalizes whitespace — multiple spaces become one, line breaks become spaces, leading/trailing whitespace is ignored.

### getByTestId

Locate by `data-testid` attribute (configurable). Use when no accessible name or role exists, or when the test contract must be explicit.

```typescript
await page.getByTestId('submit-form').click();
await page.getByTestId('user-avatar').screenshot();
```

Configure the attribute name globally:

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    testIdAttribute: 'data-pw',
  },
});
```

### getByPlaceholder and getByAltText

```typescript
// Inputs without labels
await page.getByPlaceholder('name@example.com').fill('test@test.com');

// Images
await page.getByAltText('Product screenshot').click();
```

## Filtering Locators

When multiple elements match, narrow down with `.filter()`.

### Filter by Text

```typescript
// Find the list item containing "Product 2" and click its Add button
await page
  .getByRole('listitem')
  .filter({ hasText: 'Product 2' })
  .getByRole('button', { name: 'Add to cart' })
  .click();

// Exclude items
await expect(
  page.getByRole('listitem').filter({ hasNotText: 'Out of stock' })
).toHaveCount(5);
```

### Filter by Child/Descendant

```typescript
// Find row containing a specific heading
await page
  .getByRole('listitem')
  .filter({ has: page.getByRole('heading', { name: 'Product 2' }) })
  .getByRole('button', { name: 'Add to cart' })
  .click();

// Exclude rows with a specific child
await expect(
  page.getByRole('listitem')
    .filter({ hasNot: page.getByText('Sold out') })
).toHaveCount(3);
```

The child locator is relative to the filtered element, not the document root.

### Filter by Visibility

```typescript
// Only match visible buttons
await page.locator('button').filter({ visible: true }).click();
```

### Chaining Filters

Chain multiple `.filter()` calls for complex selection:

```typescript
const row = page.getByRole('listitem');
await row
  .filter({ hasText: 'John' })
  .filter({ has: page.getByRole('button', { name: 'Say goodbye' }) })
  .screenshot({ path: 'john-goodbye.png' });
```

## Locator Operators

### and() — Match Both Conditions

```typescript
const subscribedButton = page
  .getByRole('button')
  .and(page.getByTitle('Subscribe'));
```

### or() — Match Either Condition

Handle conditional UI (dialogs that may or may not appear):

```typescript
const newEmail = page.getByRole('button', { name: 'New' });
const dialog = page.getByText('Confirm security settings');
await expect(newEmail.or(dialog).first()).toBeVisible();
if (await dialog.isVisible()) {
  await page.getByRole('button', { name: 'Dismiss' }).click();
}
await newEmail.click();
```

### Chaining Locators

Narrow scope by chaining locator methods:

```typescript
// Find Save button inside a specific dialog
const dialog = page.getByTestId('settings-dialog');
await dialog.getByRole('button', { name: 'Save' }).click();

// Or using locator() to scope
const saveButton = page.getByRole('button', { name: 'Save' });
await dialog.locator(saveButton).click();
```

### nth(), first(), last()

Positional selection as a last resort:

```typescript
const items = page.getByRole('listitem');
await items.first().click();
await items.last().click();
await items.nth(2).click();  // 0-indexed
```

Avoid positional selectors — they break when DOM order changes. Prefer filtering by text or child content.

## Shadow DOM

All Playwright locators pierce Shadow DOM by default. No special syntax needed:

```typescript
// Works even if "Details" text is inside a shadow root
await page.getByText('Details').click();
```

Exceptions: XPath does not pierce shadow roots. Closed-mode shadow roots are not supported.

## Strictness

Locators are strict by default. An action on a locator that matches multiple elements throws an error:

```typescript
// Throws if multiple buttons exist
await page.getByRole('button').click();

// OK — multi-element operations work
await expect(page.getByRole('button')).toHaveCount(3);
const texts = await page.getByRole('listitem').allTextContents();
```

If strict mode throws, refine the locator instead of using `.first()`:

| Problem | Bad Fix | Good Fix |
|---------|---------|----------|
| Multiple buttons | `.first()` | Add `{ name: 'Submit' }` |
| Multiple inputs | `.nth(0)` | Use `getByLabel('Email')` |
| Multiple links | `.last()` | Filter by `{ hasText: 'Learn more' }` |

## FrameLocator

Interact with elements inside iframes:

```typescript
// Locate inside a frame
const frame = page.frameLocator('#payment-iframe');
await frame.getByRole('button', { name: 'Pay' }).click();

// Chain frame locators for nested iframes
const nested = page
  .frameLocator('#outer')
  .frameLocator('#inner')
  .getByText('Content');
```

## Iterating Over Elements

```typescript
// Get all matching elements
for (const item of await page.getByRole('listitem').all()) {
  console.log(await item.textContent());
}

// Evaluate in the browser for performance
const texts = await page.getByRole('listitem').evaluateAll(
  list => list.map(el => el.textContent)
);
```

## Locator Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `page.locator('#tsf > div:nth-child(2) > ...')` | Breaks on any DOM change | Use getByRole or getByTestId |
| `page.locator('xpath=//div[3]/button')` | Position-dependent, fragile | Use getByRole with name |
| `await page.waitForTimeout(2000)` | Arbitrary delay, still flaky | Use auto-waiting assertions |
| `if (await el.isVisible()) el.click()` | Race condition | Just `await el.click()` — auto-waits |
| `page.$('css=button')` | ElementHandle, no auto-waiting | Use `page.locator('button')` |
