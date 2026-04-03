---
name: "@tank/playwright-mastery"
description: |
  End-to-end testing mastery with Playwright Test for any web application.
  Covers locators and selectors (getByRole, getByText, getByTestId, filtering,
  chaining), auto-waiting and web-first assertions, Page Object Model with
  fixture injection, test configuration (multi-browser projects, parallelism,
  retries, reporters), authentication state reuse (storageState, globalSetup),
  network interception and API mocking (page.route, HAR replay), visual
  regression testing (toHaveScreenshot, snapshot comparison), API testing
  (request fixture, APIRequestContext), CI/CD integration (GitHub Actions,
  Docker, sharding, artifacts), debugging (Trace Viewer, UI mode, codegen),
  and accessibility testing (@axe-core/playwright).

  Synthesizes Playwright official documentation (2024-2026), Microsoft
  Playwright GitHub repository, and production testing patterns.

  Trigger phrases: "playwright", "playwright test", "playwright tutorial",
  "playwright best practices", "playwright locator", "playwright fixture",
  "playwright page object", "playwright authentication", "playwright CI",
  "playwright docker", "playwright visual testing", "playwright api testing",
  "playwright codegen", "playwright trace viewer", "playwright network mock",
  "playwright parallel", "playwright sharding", "playwright accessibility",
  "e2e test", "end-to-end test", "playwright selector", "playwright assertion",
  "playwright storageState", "playwright screenshot", "playwright component test"
---

# Playwright Mastery

## Core Philosophy

1. **User-facing locators first** — Locate elements as users and assistive technology perceive them. Prefer getByRole, getByLabel, getByText over CSS selectors or XPath. Resilient locators survive refactors.
2. **Auto-waiting eliminates flakiness** — Every Playwright action waits for actionability (visible, enabled, stable) before executing. Never add manual sleep() calls. Trust the built-in retry mechanism.
3. **Test isolation is non-negotiable** — Each test gets a fresh BrowserContext. Tests must not share state, leak cookies, or depend on execution order. Fixtures enforce this automatically.
4. **Fixtures over hooks** — Replace beforeEach/afterEach with custom fixtures. Fixtures are composable, reusable across files, on-demand, and encapsulate setup + teardown together.
5. **Assert, never check** — Use web-first assertions (expect(locator).toBeVisible()) that auto-retry until timeout. Never use if/else with isVisible() for assertions — that creates race conditions.

## Quick-Start: Common Problems

### "Tests are flaky and timing out"

1. Replace manual waitForTimeout() calls with proper assertions or locator auto-waiting
2. Use web-first assertions: `await expect(locator).toBeVisible()` — retries automatically
3. Check if locators are too broad (matching multiple elements triggers strict mode)
4. Inspect failures with Trace Viewer: set `trace: 'on-first-retry'` in config
-> See `references/locators-selectors.md` and `references/ci-cd-integration.md`

### "How do I structure tests with Page Object Model?"

1. Create page classes with Locator fields in the constructor
2. Wrap them in custom fixtures via `test.extend<{ myPage: MyPage }>()`
3. Request the fixture by name in test functions — setup/teardown is automatic
4. Compose multiple page objects into a single test via multiple fixture parameters
-> See `references/fixtures-page-objects.md`

### "Tests need authentication but login is slow"

1. Create a globalSetup script that logs in and saves `storageState` to a JSON file
2. Configure the project to reuse that storage state for all tests
3. For multi-role tests, create separate storage state files per role
-> See `references/authentication-state.md`

### "I need to mock API responses"

1. Use `page.route('**/api/**', route => route.fulfill({ json: data }))` for inline mocks
2. Record HAR files with `page.routeFromHAR()` for complex API surfaces
3. Combine UI tests with real API calls using the `request` fixture
-> See `references/network-api-testing.md`

### "CI is slow and screenshots differ across environments"

1. Shard tests with `--shard=1/4` for parallel CI jobs
2. Use the official Docker image `mcr.microsoft.com/playwright` for consistent visual baselines
3. Upload traces and reports as CI artifacts for debugging
-> See `references/ci-cd-integration.md`

## Decision Trees

### Locator Selection

| Element Type | Recommended Locator |
|-------------|-------------------|
| Button, link, checkbox | `getByRole('button', { name: '...' })` |
| Form input with label | `getByLabel('Email')` |
| Non-interactive text | `getByText('Welcome')` |
| Image | `getByAltText('Logo')` |
| No accessible name available | `getByTestId('submit-btn')` |
| Complex dynamic element | `locator('css=...').filter({ hasText: '...' })` |

### Test Organization

| Signal | Approach |
|--------|---------|
| Shared setup across files | Custom fixture in shared test file |
| Tests need different browsers | Projects in playwright.config.ts |
| Tests need auth state | storageState via globalSetup or setup project |
| Tests must run sequentially | `test.describe.serial()` |
| Slow test suite in CI | Shard across multiple CI jobs |

### Assertion Type

| Need | Assertion |
|------|----------|
| Element visible/hidden | `expect(locator).toBeVisible()` / `.toBeHidden()` |
| Text content | `expect(locator).toHaveText('...')` / `.toContainText()` |
| URL after navigation | `expect(page).toHaveURL(/dashboard/)` |
| Input value | `expect(locator).toHaveValue('...')` |
| Element count | `expect(locator).toHaveCount(3)` |
| Visual appearance | `expect(page).toHaveScreenshot()` |
| Non-retrying check | `expect(await locator.textContent()).toBe('...')` |

## Reference Index

| File | Contents |
|------|----------|
| `references/locators-selectors.md` | Locator hierarchy, getByRole/getByText/getByTestId, filtering, chaining, Shadow DOM, strictness, auto-waiting |
| `references/assertions-waiting.md` | Web-first assertions, expect() API, soft assertions, polling, custom matchers, timeout configuration, actionability |
| `references/fixtures-page-objects.md` | Custom fixtures, test.extend(), worker-scoped fixtures, Page Object Model, fixture composition, automatic fixtures |
| `references/test-configuration.md` | playwright.config.ts, projects, parallelism, retries, reporters, webServer, timeouts, expect options |
| `references/authentication-state.md` | storageState, globalSetup login, setup projects, multi-role auth, session reuse, per-test auth override |
| `references/network-api-testing.md` | page.route(), route.fulfill/continue/abort, HAR recording, API testing with request fixture, response validation |
| `references/ci-cd-integration.md` | GitHub Actions, Docker images, sharding, artifacts, visual regression in CI, Trace Viewer, codegen, accessibility testing |
