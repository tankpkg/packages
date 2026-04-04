# Authentication State

Sources: Playwright official documentation (playwright.dev, 2024-2026), Microsoft Playwright GitHub repository, hcengineering/platform and BearStudio/start-ui-web production patterns

Covers: storageState mechanism, global setup login, setup projects with dependencies, multi-role authentication, session reuse strategies, and per-test auth overrides.

## storageState Mechanism

Playwright can save and restore browser authentication state (cookies and localStorage) as a JSON file. This eliminates repeated login flows across tests.

```typescript
// Save state after login
await page.context().storageState({ path: '.auth/user.json' });

// Restore state in a new context
const context = await browser.newContext({
  storageState: '.auth/user.json',
});
```

The saved file contains:

```json
{
  "cookies": [
    {
      "name": "session_id",
      "value": "abc123",
      "domain": "example.com",
      "path": "/",
      "httpOnly": true,
      "secure": true,
      "sameSite": "Lax"
    }
  ],
  "origins": [
    {
      "origin": "https://example.com",
      "localStorage": [
        { "name": "token", "value": "eyJhb..." }
      ]
    }
  ]
}
```

## Setup Project Pattern (Recommended)

The modern approach uses a dedicated setup project that other projects depend on. This replaces globalSetup for authentication because setup projects support fixtures, retries, and parallelism.

### Step 1: Create Auth Setup File

```typescript
// tests/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const authFile = '.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Sign in' }).click();

  // Wait for auth to complete
  await expect(page).toHaveURL(/dashboard/);

  // Save signed-in state
  await page.context().storageState({ path: authFile });
});
```

### Step 2: Configure Projects with Dependencies

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  projects: [
    // Setup project — runs first
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },

    // Test projects — depend on setup
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/user.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        storageState: '.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],
});
```

### Step 3: Add Auth File to .gitignore

```gitignore
# Playwright auth state
.auth/
```

Create the directory:

```bash
mkdir -p .auth
echo '{}' > .auth/.gitkeep
```

## Multi-Role Authentication

For applications with multiple user roles, create separate storage state files per role.

### Setup File with Multiple Roles

```typescript
// tests/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const adminFile = '.auth/admin.json';
const userFile = '.auth/user.json';
const editorFile = '.auth/editor.json';

setup('authenticate as admin', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('admin@example.com');
  await page.getByLabel('Password').fill('admin-password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/admin/);
  await page.context().storageState({ path: adminFile });
});

setup('authenticate as user', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill('user-password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/dashboard/);
  await page.context().storageState({ path: userFile });
});

setup('authenticate as editor', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('editor@example.com');
  await page.getByLabel('Password').fill('editor-password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/dashboard/);
  await page.context().storageState({ path: editorFile });
});
```

### Per-Project Role Configuration

```typescript
// playwright.config.ts
projects: [
  { name: 'setup', testMatch: /.*\.setup\.ts/ },
  {
    name: 'admin-tests',
    testDir: './tests/admin',
    use: { storageState: '.auth/admin.json' },
    dependencies: ['setup'],
  },
  {
    name: 'user-tests',
    testDir: './tests/user',
    use: { storageState: '.auth/user.json' },
    dependencies: ['setup'],
  },
],
```

### Per-Test or Per-Describe Role Override

```typescript
import { test, expect } from '@playwright/test';

// Override for a describe block
test.describe('admin features', () => {
  test.use({ storageState: '.auth/admin.json' });

  test('can manage users', async ({ page }) => {
    await page.goto('/admin/users');
    await expect(page.getByRole('heading', { name: 'User Management' })).toBeVisible();
  });
});

// Another role in the same file
test.describe('editor features', () => {
  test.use({ storageState: '.auth/editor.json' });

  test('can edit content', async ({ page }) => {
    await page.goto('/content');
    await expect(page.getByRole('button', { name: 'Edit' })).toBeVisible();
  });
});
```

## Unauthenticated Tests

For tests that must run without auth (login page itself, public pages):

```typescript
test.describe('login page', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('shows login form', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByLabel('Email')).toBeVisible();
  });

  test('rejects invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('bad@email.com');
    await page.getByLabel('Password').fill('wrong');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('alert')).toContainText('Invalid');
  });
});
```

## Concurrent Multi-User Testing

Test collaboration features with multiple users in the same test:

```typescript
test('two users see each other typing', async ({ browser }) => {
  // Create two separate authenticated contexts
  const adminContext = await browser.newContext({
    storageState: '.auth/admin.json',
  });
  const userContext = await browser.newContext({
    storageState: '.auth/user.json',
  });

  const adminPage = await adminContext.newPage();
  const userPage = await userContext.newPage();

  // Both open the same document
  await adminPage.goto('/docs/shared-doc');
  await userPage.goto('/docs/shared-doc');

  // Admin types
  await adminPage.getByRole('textbox').fill('Hello from admin');

  // User sees the change
  await expect(userPage.getByText('Hello from admin')).toBeVisible();

  // Cleanup
  await adminContext.close();
  await userContext.close();
});
```

## Auth Fixture Pattern

For typed, reusable auth with Page Object Model:

```typescript
// fixtures.ts
import { test as base } from '@playwright/test';
import { LoginPage } from './pages/login-page';

type AuthFixtures = {
  adminPage: Page;
  userPage: Page;
};

export const test = base.extend<AuthFixtures>({
  adminPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: '.auth/admin.json',
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
  userPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: '.auth/user.json',
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});
```

```typescript
// collab.spec.ts
import { test, expect } from './fixtures';

test('admin and user collaborate', async ({ adminPage, userPage }) => {
  await adminPage.goto('/workspace');
  await userPage.goto('/workspace');
  // Both pages have separate auth contexts
});
```

## Worker-Scoped Auth with Unique Users

Create unique users per worker to avoid test interference:

```typescript
export const test = base.extend<{}, { workerAccount: Account }>({
  workerAccount: [async ({ browser }, use, workerInfo) => {
    const username = `test-user-${workerInfo.workerIndex}`;
    const password = 'test-password';

    // Create account via API (faster than UI)
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.request.post('/api/users', {
      data: { username, password },
    });

    // Login and save state
    await page.goto('/login');
    await page.getByLabel('Username').fill(username);
    await page.getByLabel('Password').fill(password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    const storageState = await page.context().storageState();
    await page.close();
    await context.close();

    await use({ username, password, storageState });
  }, { scope: 'worker' }],

  // Override page to use worker's auth
  page: async ({ browser, workerAccount }, use) => {
    const context = await browser.newContext({
      storageState: workerAccount.storageState,
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});
```

## Token-Based Authentication

For SPAs that use tokens instead of cookies:

```typescript
setup('get auth token', async ({ request }) => {
  const response = await request.post('/api/auth/login', {
    data: { email: 'user@test.com', password: 'password' },
  });
  const { token } = await response.json();

  // Save as storage state with localStorage
  const storageState = {
    cookies: [],
    origins: [
      {
        origin: 'http://localhost:3000',
        localStorage: [
          { name: 'auth_token', value: token },
        ],
      },
    ],
  };

  await fs.promises.writeFile(
    '.auth/token-user.json',
    JSON.stringify(storageState)
  );
});
```

## Auth Strategy Decision Tree

| Scenario | Strategy |
|----------|----------|
| Single role, all tests authenticated | Setup project + single storageState |
| Multiple roles | Setup project + separate storageState files per role |
| Mixed auth/unauth tests | storageState per role + `{ cookies: [], origins: [] }` for unauth |
| Collaboration features | Multiple BrowserContexts with different storageState |
| Parallel tests that mutate user data | Worker-scoped unique users via workerIndex |
| Token-based SPA | Save token in localStorage via storageState origins |
| Tests that require fresh login | Skip storageState, login in test directly |

## Common Auth Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Sharing state between parallel tests | Cookie/token expires mid-run | Worker-scoped accounts |
| Hardcoded credentials in test files | Security risk | Use env vars or `.env` files |
| Not waiting for auth redirect | storageState saved before login completes | Assert URL/element after login |
| storageState with expired tokens | Tests fail on CI with stale state | Always regenerate in setup project |
| Forgetting .gitignore for .auth/ | Credentials committed to repo | Add `.auth/` to .gitignore |

## Auth Strategy Review Questions

1. Should this suite share auth state, or does each test need fresh login/setup?
2. Are multiple roles isolated cleanly enough for parallel execution?
3. Is the saved state regenerated often enough to avoid hidden expiry drift?

## Auth-State Smells

| Smell | Why it matters |
|------|----------------|
| one shared account across mutating parallel tests | test interference |
| auth files created ad hoc without setup project | stale or inconsistent state |
| login flow assumed stable with no post-login assertion | false-success storage capture |
