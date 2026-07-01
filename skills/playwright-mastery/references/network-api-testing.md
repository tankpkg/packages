# Network Interception and API Testing

Sources: Playwright official documentation (playwright.dev, 2024-2026), Microsoft Playwright GitHub repository, Playwright network and API testing guides

Covers: request interception with page.route(), response mocking, request modification, HAR recording and replay, API testing with the request fixture, response validation, and combining UI and API tests.

## Network Interception Overview

Playwright can intercept, modify, and mock HTTP requests at the browser level. Three primary operations:

| Operation | Method | Use Case |
|-----------|--------|----------|
| Mock response | `route.fulfill()` | Return fake data without hitting the server |
| Modify request | `route.continue()` | Change headers, URL, or body before sending |
| Block request | `route.abort()` | Prevent requests (images, analytics, ads) |

## Mocking Responses with route.fulfill()

### Basic JSON Mock

```typescript
await page.route('**/api/users', async (route) => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    json: [
      { id: 1, name: 'Alice', email: 'alice@test.com' },
      { id: 2, name: 'Bob', email: 'bob@test.com' },
    ],
  });
});

await page.goto('/users');
await expect(page.getByText('Alice')).toBeVisible();
```

### Mock with Status Codes

```typescript
// Simulate server error
await page.route('**/api/users', async (route) => {
  await route.fulfill({
    status: 500,
    contentType: 'application/json',
    json: { error: 'Internal Server Error' },
  });
});

// Simulate not found
await page.route('**/api/users/999', async (route) => {
  await route.fulfill({ status: 404 });
});

// Simulate network delay
await page.route('**/api/slow', async (route) => {
  await new Promise(resolve => setTimeout(resolve, 3000));
  await route.fulfill({ json: { data: 'delayed' } });
});
```

### Mock from File

```typescript
await page.route('**/api/products', async (route) => {
  await route.fulfill({
    path: './tests/fixtures/products.json',
  });
});
```

### Conditional Mocking

Mock only specific HTTP methods or paths:

```typescript
await page.route('**/api/**', async (route) => {
  const request = route.request();

  // Only mock GET requests, let mutations through
  if (request.method() === 'GET') {
    const url = new URL(request.url());
    const mockFile = `./mocks${url.pathname}.json`;
    if (fs.existsSync(mockFile)) {
      await route.fulfill({ path: mockFile });
      return;
    }
  }

  // Pass through to real server
  await route.continue();
});
```

## Modifying Requests with route.continue()

Change outgoing requests before they reach the server:

```typescript
// Add custom headers
await page.route('**/api/**', async (route) => {
  await route.continue({
    headers: {
      ...route.request().headers(),
      'X-Test-Header': 'playwright',
      'Authorization': 'Bearer test-token',
    },
  });
});

// Redirect to different URL
await page.route('**/api/v1/**', async (route) => {
  const url = route.request().url().replace('/v1/', '/v2/');
  await route.continue({ url });
});

// Modify POST body
await page.route('**/api/submit', async (route) => {
  const postData = route.request().postDataJSON();
  postData.source = 'playwright-test';
  await route.continue({ postData: JSON.stringify(postData) });
});
```

## Modifying Responses (Fetch + Fulfill)

Fetch the real response, then modify it before returning to the browser:

```typescript
// Add a feature flag to the response
await page.route('**/api/config', async (route) => {
  const response = await route.fetch();
  const json = await response.json();
  json.featureFlags = { ...json.featureFlags, newDashboard: true };
  await route.fulfill({ response, json });
});

// Inject content into HTML
await page.route('**/dashboard', async (route) => {
  const response = await route.fetch();
  let body = await response.text();
  body = body.replace('</head>', '<script>window.__TEST__=true</script></head>');
  await route.fulfill({ response, body });
});
```

## Blocking Requests with route.abort()

```typescript
// Block images to speed up tests
await page.route('**/*.{png,jpg,jpeg,gif,svg,webp}', (route) => route.abort());

// Block analytics
await page.route('**/analytics/**', (route) => route.abort());
await page.route('**/google-analytics.com/**', (route) => route.abort());

// Block with specific error reason
await page.route('**/api/forbidden', (route) => route.abort('accessdenied'));
```

Abort reasons: `aborted`, `accessdenied`, `addressunreachable`, `blockedbyclient`, `blockedbyresponse`, `connectionaborted`, `connectionclosed`, `connectionfailed`, `connectionrefused`, `connectionreset`, `internetdisconnected`, `namenotresolved`, `timedout`, `failed`.

## URL Pattern Matching

| Pattern | Matches |
|---------|---------|
| `'**/api/users'` | Any URL ending with `/api/users` |
| `'**/api/**'` | Any URL containing `/api/` |
| `'**/*.css'` | Any CSS file |
| `'https://example.com/api/*'` | Exact domain, one path segment after `/api/` |
| `/\/api\/users\/\d+/` | Regex: `/api/users/` followed by digits |

## HAR Recording and Replay

Record real API responses to a HAR file, then replay for deterministic tests.

### Record HAR

```typescript
// Record during test
const context = await browser.newContext({
  recordHar: {
    path: './tests/fixtures/api.har',
    urlFilter: '**/api/**',
    mode: 'minimal',  // Only response bodies, not full headers
  },
});

const page = await context.newPage();
await page.goto('/app');
// ... perform actions that trigger API calls
await context.close();  // HAR saved on close
```

### Replay HAR

```typescript
// Replay recorded responses
await page.routeFromHAR('./tests/fixtures/api.har', {
  url: '**/api/**',
  notFound: 'fallback',  // Fall through to real server for unrecorded URLs
});

await page.goto('/app');
// API calls served from HAR file
```

### HAR Options

| Option | Values | Description |
|--------|--------|-------------|
| `notFound` | `'abort'`, `'fallback'` | What to do when URL not in HAR |
| `update` | boolean | Re-record HAR instead of replaying |
| `updateMode` | `'full'`, `'minimal'` | How much to record |
| `updateContent` | `'embed'`, `'attach'` | Where to store response bodies |

## Waiting for Network Events

```typescript
// Wait for a specific response
const responsePromise = page.waitForResponse('**/api/users');
await page.getByRole('button', { name: 'Load users' }).click();
const response = await responsePromise;
expect(response.status()).toBe(200);

// Wait for request to be sent
const requestPromise = page.waitForRequest('**/api/submit');
await page.getByRole('button', { name: 'Submit' }).click();
const request = await requestPromise;
expect(request.method()).toBe('POST');

// Wait with predicate
const response = await page.waitForResponse(
  (resp) => resp.url().includes('/api/') && resp.status() === 200
);
```

## Removing Routes

```typescript
// Remove a specific route
const handler = async (route: Route) => route.fulfill({ json: [] });
await page.route('**/api/users', handler);

// Later: remove this specific handler
await page.unroute('**/api/users', handler);

// Remove all routes for a URL
await page.unroute('**/api/users');

// One-time route (auto-removes after first match)
await page.route('**/api/init', async (route) => {
  await route.fulfill({ json: { initialized: true } });
}, { times: 1 });
```

## API Testing with request Fixture

The `request` fixture provides an `APIRequestContext` for making HTTP requests without a browser. Shares cookies with the browser context.

### Basic API Calls

```typescript
import { test, expect } from '@playwright/test';

test('API CRUD operations', async ({ request }) => {
  // POST — create
  const createResponse = await request.post('/api/users', {
    data: { name: 'Alice', email: 'alice@test.com' },
  });
  await expect(createResponse).toBeOK();
  const { id } = await createResponse.json();

  // GET — read
  const getResponse = await request.get(`/api/users/${id}`);
  await expect(getResponse).toBeOK();
  const user = await getResponse.json();
  expect(user.name).toBe('Alice');

  // PUT — update
  const updateResponse = await request.put(`/api/users/${id}`, {
    data: { name: 'Alice Updated' },
  });
  await expect(updateResponse).toBeOK();

  // DELETE — cleanup
  const deleteResponse = await request.delete(`/api/users/${id}`);
  expect(deleteResponse.status()).toBe(204);
});
```

### Request Options

```typescript
const response = await request.post('/api/data', {
  data: { key: 'value' },            // JSON body (auto Content-Type)
  form: { field: 'value' },           // Form URL-encoded
  multipart: {                         // Multipart form data
    file: fs.createReadStream('file.pdf'),
    name: 'document',
  },
  headers: { 'X-Custom': 'header' },  // Custom headers
  params: { page: '1', limit: '10' }, // Query parameters
  timeout: 10000,                      // Request timeout
  failOnStatusCode: true,              // Throw on 4xx/5xx
});
```

### Standalone API Context

For tests that only use API (no browser):

```typescript
import { test, expect } from '@playwright/test';

test('standalone API test', async ({ playwright }) => {
  const context = await playwright.request.newContext({
    baseURL: 'https://api.example.com',
    extraHTTPHeaders: {
      'Authorization': `Bearer ${process.env.API_TOKEN}`,
      'Accept': 'application/json',
    },
  });

  const response = await context.get('/health');
  await expect(response).toBeOK();

  await context.dispose();
});
```

## Combining UI and API Tests

### Pattern 1: API Setup, UI Verify

Create test data via API, verify it appears in the UI:

```typescript
test('created item appears in list', async ({ page, request }) => {
  // Setup via API (fast, reliable)
  await request.post('/api/items', {
    data: { title: 'Test Item', priority: 'high' },
  });

  // Verify via UI (tests what user sees)
  await page.goto('/items');
  await expect(page.getByText('Test Item')).toBeVisible();
  await expect(page.getByText('high')).toBeVisible();
});
```

### Pattern 2: UI Action, API Verify

Perform action in UI, verify the server state via API:

```typescript
test('form submission creates record', async ({ page, request }) => {
  // Act via UI
  await page.goto('/items/new');
  await page.getByLabel('Title').fill('New Item');
  await page.getByRole('button', { name: 'Create' }).click();

  // Verify via API
  const response = await request.get('/api/items');
  const items = await response.json();
  expect(items.some(i => i.title === 'New Item')).toBe(true);
});
```

### Pattern 3: API Cleanup in afterAll

```typescript
let createdIds: string[] = [];

test.afterAll(async ({ request }) => {
  for (const id of createdIds) {
    await request.delete(`/api/items/${id}`);
  }
});

test('create and track items', async ({ page, request }) => {
  const response = await request.post('/api/items', {
    data: { title: 'Temp Item' },
  });
  const { id } = await response.json();
  createdIds.push(id);

  // ... test using created item
});
```

## Response Validation Patterns

```typescript
const response = await request.get('/api/users');

// Status
expect(response.status()).toBe(200);
await expect(response).toBeOK();         // 200-299

// Headers
expect(response.headers()['content-type']).toContain('application/json');

// Body
const body = await response.json();
expect(body).toMatchObject({
  users: expect.arrayContaining([
    expect.objectContaining({ name: 'Alice' }),
  ]),
  total: expect.any(Number),
});

// Text body
const text = await response.text();
expect(text).toContain('success');
```
