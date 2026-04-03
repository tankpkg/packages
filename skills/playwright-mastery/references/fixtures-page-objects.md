# Fixtures and Page Object Model

Sources: Playwright official documentation (playwright.dev, 2024-2026), Microsoft Playwright GitHub repository, Playwright POM guide

Covers: built-in fixtures, custom fixture creation with test.extend(), worker-scoped fixtures, automatic fixtures, fixture composition, Page Object Model patterns, and fixture-based test architecture.

## Built-in Fixtures

Playwright Test provides these fixtures out of the box:

| Fixture | Scope | Description |
|---------|-------|-------------|
| `page` | Test | Isolated Page instance for this test |
| `context` | Test | Isolated BrowserContext (page belongs to this context) |
| `browser` | Worker | Shared Browser instance across tests in a worker |
| `browserName` | Worker | Current browser: `chromium`, `firefox`, or `webkit` |
| `request` | Test | Isolated APIRequestContext for API calls |

Request a fixture by including it in the test function signature:

```typescript
import { test, expect } from '@playwright/test';

test('example', async ({ page, request }) => {
  // page and request are automatically set up
  await page.goto('/');
  const response = await request.get('/api/health');
  await expect(response).toBeOK();
});
```

Fixtures not requested by a test are never created — zero waste.

## Creating Custom Fixtures

Use `test.extend()` to define fixtures. Each fixture receives a `use` callback that provides the value to the test.

### Basic Pattern

```typescript
// my-test.ts
import { test as base } from '@playwright/test';
import { LoginPage } from './pages/login-page';
import { DashboardPage } from './pages/dashboard-page';

type MyFixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
};

export const test = base.extend<MyFixtures>({
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await use(loginPage);
  },
  dashboardPage: async ({ page }, use) => {
    const dashboardPage = new DashboardPage(page);
    await use(dashboardPage);
  },
});

export { expect } from '@playwright/test';
```

```typescript
// login.spec.ts
import { test, expect } from './my-test';

test('user can log in', async ({ loginPage, dashboardPage, page }) => {
  await loginPage.goto();
  await loginPage.login('admin', 'password');
  await expect(page).toHaveURL(/dashboard/);
  await expect(dashboardPage.welcomeMessage).toContainText('admin');
});
```

### Setup and Teardown in One Place

Code before `use()` is setup. Code after `use()` is teardown:

```typescript
todoPage: async ({ page }, use) => {
  // SETUP: create page, seed data
  const todoPage = new TodoPage(page);
  await todoPage.goto();
  await todoPage.addToDo('item1');
  await todoPage.addToDo('item2');

  // PROVIDE to test
  await use(todoPage);

  // TEARDOWN: clean up after test completes
  await todoPage.removeAll();
},
```

This replaces beforeEach/afterEach with a single, encapsulated unit.

## Worker-Scoped Fixtures

Worker-scoped fixtures are created once per worker process and shared across all tests in that worker. Use for expensive setup like creating accounts or starting services.

```typescript
type WorkerFixtures = {
  account: { username: string; password: string };
};

export const test = base.extend<{}, WorkerFixtures>({
  account: [async ({ browser }, use, workerInfo) => {
    // Create a unique account per worker
    const username = `user-${workerInfo.workerIndex}`;
    const password = 'secure-password';

    const page = await browser.newPage();
    await page.goto('/signup');
    await page.getByLabel('Username').fill(username);
    await page.getByLabel('Password').fill(password);
    await page.getByRole('button', { name: 'Sign up' }).click();
    await page.close();

    await use({ username, password });

    // Optional: cleanup account after all tests in worker
  }, { scope: 'worker' }],
});
```

Note the tuple syntax: `[async fn, { scope: 'worker' }]`.

### Worker vs Test Scope

| Aspect | Test-Scoped | Worker-Scoped |
|--------|-------------|---------------|
| Created | Once per test | Once per worker process |
| Isolation | Full (new for every test) | Shared within worker |
| Teardown | After each test | After worker shuts down |
| Use for | Page objects, test data | Accounts, servers, DB connections |
| Syntax | `fixture: async ({}, use) => {}` | `[async ({}, use) => {}, { scope: 'worker' }]` |
| Timeout | Part of test timeout | Separate timeout (default = test timeout) |

## Automatic Fixtures

Automatic fixtures run for every test, even when not requested by name. Use for global setup like logging or error collection.

```typescript
export const test = base.extend<{ saveLogs: void }>({
  saveLogs: [async ({}, use, testInfo) => {
    const logs: string[] = [];
    // Collect logs during test
    debug.log = (...args) => logs.push(args.join(' '));
    debug.enable('myapp');

    await use();

    // Attach logs only on failure
    if (testInfo.status !== testInfo.expectedStatus) {
      const logFile = testInfo.outputPath('logs.txt');
      await fs.promises.writeFile(logFile, logs.join('\n'));
      testInfo.attachments.push({
        name: 'logs',
        contentType: 'text/plain',
        path: logFile,
      });
    }
  }, { auto: true }],
});
```

Combine `auto: true` with `scope: 'worker'` for worker-level automatic fixtures.

## Fixture Composition and Dependencies

Fixtures can depend on other fixtures, forming a dependency graph:

```typescript
export const test = base.extend<{
  db: Database;
  apiClient: ApiClient;
  authenticatedPage: Page;
}>({
  db: async ({}, use) => {
    const db = await Database.connect();
    await use(db);
    await db.disconnect();
  },

  apiClient: async ({ db }, use) => {
    // Depends on db fixture
    const client = new ApiClient(db);
    await use(client);
  },

  authenticatedPage: async ({ page, apiClient }, use) => {
    // Depends on both page and apiClient
    const token = await apiClient.createSession('testuser');
    await page.goto('/');
    await page.evaluate(t => localStorage.setItem('token', t), token);
    await use(page);
  },
});
```

Playwright resolves the dependency graph automatically. Setup order follows dependencies; teardown runs in reverse.

## Merging Fixtures from Multiple Modules

Combine fixtures from different sources with `mergeTests`:

```typescript
import { mergeTests } from '@playwright/test';
import { test as dbTest } from './fixtures/database';
import { test as authTest } from './fixtures/auth';
import { test as a11yTest } from './fixtures/accessibility';

export const test = mergeTests(dbTest, authTest, a11yTest);
```

## Overriding Built-in Fixtures

Override any fixture, including built-in ones:

```typescript
export const test = base.extend({
  // Auto-navigate to baseURL on every test
  page: async ({ baseURL, page }, use) => {
    await page.goto(baseURL!);
    await use(page);
  },

  // Override storageState with custom auth
  storageState: async ({}, use) => {
    const cookie = await getAuthCookie();
    await use({ cookies: [cookie] });
  },
});
```

## Fixture Options

Create parameterized fixtures that can be configured per-project:

```typescript
type MyOptions = {
  locale: string;
};

export const test = base.extend<MyOptions>({
  locale: ['en-US', { option: true }],
});
```

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    { name: 'english', use: { locale: 'en-US' } },
    { name: 'french', use: { locale: 'fr-FR' } },
  ],
});
```

## Page Object Model

### Class Structure

```typescript
// pages/login-page.ts
import type { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(public readonly page: Page) {
    this.usernameInput = page.getByLabel('Username');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Sign in' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}
```

### POM Design Rules

| Rule | Rationale |
|------|-----------|
| Define locators in constructor as readonly fields | Locators are lazy — no DOM queries until action |
| Accept Page in constructor, not BrowserContext | Page is the correct scope for element interaction |
| Methods represent user actions, not implementation | `login()` not `fillUsernameField()` |
| No assertions inside page objects | Page objects describe capabilities, tests assert outcomes |
| Prefer composition over inheritance | `CheckoutFlow` uses `CartPage` + `PaymentPage`, not extends |
| Return page objects from navigation methods | `login()` returns `DashboardPage` for fluent chaining |

### Composition Pattern

```typescript
export class CheckoutFlow {
  readonly cart: CartPage;
  readonly payment: PaymentPage;
  readonly confirmation: ConfirmationPage;

  constructor(public readonly page: Page) {
    this.cart = new CartPage(page);
    this.payment = new PaymentPage(page);
    this.confirmation = new ConfirmationPage(page);
  }

  async completeOrder(item: string, card: string) {
    await this.cart.addItem(item);
    await this.cart.proceedToCheckout();
    await this.payment.enterCard(card);
    await this.payment.submit();
  }
}
```

### Navigation Return Pattern

```typescript
export class LoginPage {
  // ... locators

  async loginAsAdmin(): Promise<AdminDashboard> {
    await this.login('admin', 'password');
    return new AdminDashboard(this.page);
  }

  async loginAsUser(): Promise<UserDashboard> {
    await this.login('user', 'password');
    return new UserDashboard(this.page);
  }
}
```

## Fixture Execution Order

1. Worker-scoped automatic fixtures (setup)
2. Worker-scoped non-automatic fixtures (if needed)
3. `beforeAll` hooks
4. Per-test: automatic test fixtures (setup)
5. Per-test: `beforeEach` hooks
6. Per-test: requested test fixtures (setup, lazy)
7. Test function
8. `afterEach` hooks
9. Test-scoped fixtures (teardown, reverse order)
10. `afterAll` hooks (after all tests)
11. Worker-scoped fixtures (teardown, reverse order)

Unused fixtures are never set up. A fixture's teardown runs only after all tests using it complete.

## Box and Title Fixtures

Hide noisy utility fixtures from reports:

```typescript
helperFixture: [async ({}, use) => {
  // ... setup
  await use(value);
}, { box: true }],  // Hidden from trace/report

namedFixture: [async ({}, use) => {
  // ...
  await use(value);
}, { title: 'Database Connection' }],  // Custom display name
```
