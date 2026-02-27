# BDD Multiplayer Testing

Sources: Playwright multi-context patterns, Socket.IO testing, INQTR/poker-planning test suite, party game testing patterns

Testing multiplayer party games requires simulating multiple concurrent users, coordinating real-time state across independent browser contexts, and verifying that all participants see a consistent view of the game world. This reference provides the definitive patterns for building a robust BDD suite using `playwright-bdd`.

## Test Infrastructure Setup

Multiplayer tests are highly sensitive to timing and port availability. The configuration must prioritize stability and sequential execution to avoid race conditions and port conflicts between tests.

### Project Directory Structure

Following the `.bdd/` convention, organize party game tests by domain and layer:

```text
.bdd/
  features/              # Gherkin specs (lobby, rounds, voting)
    lobby/
      joining.feature
    game/
      round-flow.feature
  steps/                 # Step definitions (domain-specific)
    lobby.steps.ts
    game.steps.ts
    setup.steps.ts
  interactions/          # Page Objects (the "Interaction Layer")
    lobby.page.ts
    game.page.ts
    results.page.ts
  support/               # Fixtures and orchestration
    player-manager.ts    # Manages 2-8 browser contexts
    fixtures.ts          # Extends Playwright test with PlayerManager
    hooks.ts             # Global setup/teardown
  qa/                    # Audit trail
    findings/
    resolutions/
```

### Playwright-BDD Configuration

Use `workers: 1` and `fullyParallel: false` to ensure multiplayer tests do not interfere with each other's backend state.

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';
import { defineBddConfig } from 'playwright-bdd';

const testDir = defineBddConfig({
  features: '.bdd/features/**/*.feature',
  steps: '.bdd/steps/**/*.steps.ts',
});

export default defineConfig({
  testDir,
  fullyParallel: false,
  workers: 1,
  timeout: 60000, // Multi-player coordination takes longer
  expect: { timeout: 10000 },
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    video: 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

## Multi-Player Fixture Pattern

Each player in a party game must have a completely isolated session. Using multiple tabs in one context is insufficient as they share cookies and local storage. The `PlayerManager` creates truly independent `BrowserContext` instances.

### The PlayerManager Class

```typescript
// .bdd/support/player-manager.ts
import { Browser, BrowserContext, Page } from '@playwright/test';

export class PlayerManager {
  private contexts: Map<string, BrowserContext> = new Map();
  private pages: Map<string, Page> = new Map();

  constructor(private browser: Browser) {}

  async getPlayer(name: string): Promise<Page> {
    if (this.pages.has(name)) return this.pages.get(name)!;

    const context = await this.browser.newContext();
    const page = await context.newPage();
    
    this.contexts.set(name, context);
    this.pages.set(name, page);
    
    return page;
  }

  async getAllPages(): Promise<Page[]> {
    return Array.from(this.pages.values());
  }

  async cleanup() {
    await Promise.all(
      Array.from(this.contexts.values()).map(ctx => ctx.close())
    );
    this.contexts.clear();
    this.pages.clear();
  }
}
```

### Multiplayer Fixtures

```typescript
// .bdd/support/fixtures.ts
import { test as base } from 'playwright-bdd';
import { PlayerManager } from './player-manager';

type PartyFixtures = {
  playerManager: PlayerManager;
};

export const test = base.extend<PartyFixtures>({
  playerManager: async ({ browser }, use) => {
    const manager = new PlayerManager(browser);
    await use(manager);
    await manager.cleanup();
  },
});
```

## Gherkin for Multi-Actor Scenarios

Write Gherkin that explicitly identifies which player is acting. Use persona names (Alice, Bob) or indexed players (Player 1, Player 2) to maintain clarity.

### Lobby and Game Flow Examples

```gherkin
Feature: Game Session Orchestration

  Scenario: Room creation and multi-player join
    Given Player "Alice" is at the "Landing" page
    When Player "Alice" creates a new room
    Then Player "Alice" should see a unique room code
    
    When Player "Bob" joins room created by "Alice"
    And Player "Charlie" joins room created by "Alice"
    Then all players should see 3 participants in the lobby
    And all players should see names: "Alice", "Bob", "Charlie"

  Scenario: Synchronized round transition
    Given a game exists with players "Alice", "Bob", "Charlie"
    And "Alice" is the host
    When Player "Alice" starts the game
    Then all players should see the "Question" screen
    And all players should see the prompt "What is the best pizza topping?"

  Scenario: Voting and results propagation
    Given a round is active with prompt "Best animal?"
    And Player "Alice" submitted "Platypus"
    And Player "Bob" submitted "Capybara"
    When Player "Charlie" votes for "Capybara"
    Then all players should see "Capybara" has 1 vote
    And all players should see "Platypus" has 0 votes
```

## Step Definition Patterns

Step definitions must resolve player names to their respective browser pages using the `PlayerManager`.

```typescript
// .bdd/steps/lobby.steps.ts
import { createBdd } from 'playwright-bdd';
import { test } from '../support/fixtures';
import { LobbyPage } from '../interactions/lobby.page';
import { expect } from '@playwright/test';

const { Given, When, Then } = createBdd(test);

Given('Player {string} is at the {string} page', async ({ playerManager }, name: string, page: string) => {
  const p = await playerManager.getPlayer(name);
  await p.goto('/');
});

When('Player {string} creates a new room', async ({ playerManager }, name: string) => {
  const p = await playerManager.getPlayer(name);
  const lobby = new LobbyPage(p);
  this.roomCode = await lobby.createRoom();
});

When('Player {string} joins room created by {string}', async ({ playerManager }, joiner: string, creator: string) => {
  const p = await playerManager.getPlayer(joiner);
  const lobby = new LobbyPage(p);
  await lobby.joinRoom(this.roomCode);
});

Then('all players should see {int} participants in the lobby', async ({ playerManager }, count: number) => {
  const pages = await playerManager.getAllPages();
  await Promise.all(
    pages.map(p => expect(p.getByTestId('lobby-count')).toHaveText(count.toString()))
  );
});
```

## Page Objects for Party Games

Page objects should handle the synchronization logic, such as waiting for specific game phases to become active.

```typescript
// .bdd/interactions/game.page.ts
import { Page, expect } from '@playwright/test';

export class GamePage {
  constructor(private page: Page) {}

  async waitForQuestion(timeout = 15000) {
    await expect(this.page.getByTestId('question-text')).toBeVisible({ timeout });
  }

  async submitAnswer(text: string) {
    await this.page.getByTestId('answer-input').fill(text);
    await this.page.getByRole('button', { name: 'Submit' }).click();
    await expect(this.page.getByTestId('waiting-overlay')).toBeVisible();
  }

  async waitForVotingPhase() {
    await expect(this.page.getByTestId('voting-options')).toBeVisible({ timeout: 20000 });
  }

  async vote(optionText: string) {
    await this.page.getByRole('button', { name: optionText }).click();
  }

  async waitForResults(timeout = 15000) {
    await expect(this.page.getByTestId('results-screen')).toBeVisible({ timeout });
  }

  async getWinner() {
    return await this.page.getByTestId('winner-name').textContent();
  }
}

export class ResultsPage {
  constructor(private page: Page) {}

  async getScores(): Promise<Record<string, number>> {
    const scoreItems = await this.page.getByTestId('score-item').all();
    const scores: Record<string, number> = {};
    
    for (const item of scoreItems) {
      const name = await item.getByTestId('player-name').textContent();
      const score = await item.getByTestId('player-score').textContent();
      if (name && score) {
        scores[name] = parseInt(score);
      }
    }
    return scores;
  }

  async waitForNextRound(timeout = 20000) {
    await expect(this.page.getByTestId('next-round-indicator')).toBeVisible({ timeout });
  }
}
```

## Coordination Patterns

Multiplayer assertions often require checking state across all players simultaneously. Use `Promise.all` to avoid sequential waiting which can cause timeouts.

### Parallel Assertion Pattern

```typescript
// Verify score update across all clients
async function verifyScores(playerManager: PlayerManager, expectedScores: Record<string, number>) {
  const players = Object.keys(expectedScores);
  await Promise.all(players.map(async (name) => {
    const page = await playerManager.getPlayer(name);
    for (const [targetPlayer, score] of Object.entries(expectedScores)) {
      const scoreElement = page.getByTestId(`score-${targetPlayer}`);
      await expect(scoreElement).toHaveText(score.toString());
    }
  }));
}
```

### Waiting for Real-Time Propagation

Party games rely on WebSockets. If an action is taken by Player A, Player B might not see it instantly. Always use auto-retrying assertions (`expect(...).toHaveText(...)`) rather than static checks.

```typescript
// ❌ WRONG: Static check might fail due to network lag
const text = await player2.textContent('.status');
expect(text).toBe('Ready');

// ✅ CORRECT: Retrying assertion handles WebSocket delay
await expect(player2.getByTestId('status')).toHaveText('Ready');
```

## Socket.IO Direct Testing

For high-performance logic testing (e.g., scoring algorithms, timer logic), use `socket.io-client` to test without the browser overhead.

```typescript
// .bdd/support/socket-helper.ts
import { io, Socket } from 'socket.io-client';

export class SocketTester {
  private sockets: Socket[] = [];

  async createClient(url: string): Promise<Socket> {
    const socket = io(url, {
      multiplex: false, // CRITICAL: Force independent connections
      forceNew: true,
      transports: ['websocket'],
    });
    
    return new Promise((resolve, reject) => {
      socket.on('connect', () => {
        this.sockets.push(socket);
        resolve(socket);
      });
      socket.on('connect_error', reject);
    });
  }

  cleanup() {
    this.sockets.forEach(s => s.disconnect());
    this.sockets = [];
  }
}
```

## Edge Case Testing

Multiplayer robustness is defined by how it handles failures. BDD scenarios should explicitly cover these "unhappy paths."

### Host Migration Scenario

```gherkin
Scenario: Host migration on disconnect
  Given a game exists with players "Alice", "Bob", "Charlie"
  And "Alice" is the host
  When Player "Alice" disconnects
  Then Player "Bob" should be notified they are the new host
  And the game should continue from the current state
```

### Reconnection Implementation

```typescript
// .bdd/steps/reconnect.steps.ts
When('Player {string} reconnects', async ({ playerManager }, name: string) => {
  const page = await playerManager.getPlayer(name);
  
  // Save storage state to preserve session ID / JWT
  const state = await page.context().storageState();
  
  // Simulate browser close/reopen
  await page.close();
  const newPage = await playerManager.getPlayer(name);
  
  // Navigate back - app should resume session from cookies/localStorage
  await newPage.goto('/');
  await expect(newPage.getByTestId('game-active')).toBeVisible();
});
```

## Common Gotchas

### 1. Socket.IO Multiplexing
By default, Socket.IO reuses the same connection for the same URL. In a multi-player test environment, this will cause cross-talk between players.
**Fix:** Always set `multiplex: false` and `forceNew: true` in your client options.

### 2. ID Collisions
If your game uses `Math.random()` for room codes or player IDs, tests might occasionally collide.
**Fix:** Use a deterministic seeding strategy or mock the ID generator (only in the backend, never in the test) to ensure uniqueness in the test environment.

### 3. Port Conflicts
Running multiple workers in Playwright will start multiple instances of your web server if configured in `webServer`.
**Fix:** Set `workers: 1` or use a shared server instance that the tests connect to.

### 4. Memory Leaks
Creating many `BrowserContext` instances without closing them will quickly exhaust CI resources.
**Fix:** Ensure `PlayerManager.cleanup()` is called in the `After` hook of every scenario.

### 5. Animation Delays
Assertions might fire while a scoring animation is still playing.
**Fix:** Ensure your `data-testid` elements reflect the *final* state or wait for an "animation-complete" indicator.

```typescript
// Wait for animation to finish before checking score
await expect(page.getByTestId('score-update-indicator')).not.toBeVisible();
await expect(page.getByTestId('final-score')).toHaveText('100');
```
