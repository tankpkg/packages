---
name: "@tank/party-game-dev"
description: |
  Build real-time multiplayer party games (Jackbox-style) with full-stack TypeScript. Covers host-player architecture (TV + phones), VIP role (player with elevated control), Socket.IO networking, game state machines, room/lobby management, voting and scoring systems, content safety (profanity filtering, family mode, VIP censoring), and BDD testing with multiple browser contexts. Synthesizes patterns from Jackbox Games, Drawphone, Rocketcrab, Fishbowl, Socket.IO docs, and Playwright multi-context testing.

  Trigger phrases: "party game", "jackbox", "multiplayer game", "real-time game", "game room", "lobby system", "room code", "socket.io game", "websocket game", "game state machine", "voting game", "drawing game", "trivia game", "quiplash", "drawful", "host screen", "player controller", "VIP", "game VIP", "room owner", "kick player", "ban player", "multiplayer testing", "game server", "party game backend", "prompt and response game", "audience voting", "game lobby", "turn-based multiplayer", "phone controller game", "content moderation", "profanity filter", "family friendly", "test multiplayer", "BDD game testing"
---

# Party Game Development

Build Jackbox-style party games: one shared screen (TV/projector) runs the
host display, each player uses their phone as a controller. The first player
to join becomes the **VIP** — a player with elevated control (start game,
kick players, censor content). The VIP is NOT the host. The host is the TV.
All connected via WebSockets with server-authoritative state.

## Core Philosophy

1. **Server owns the truth** — All game state lives on the server. Clients
   send inputs, server validates, broadcasts results. No cheating possible.
2. **Rooms are ephemeral** — In-memory state, 4-character room codes, auto-cleanup.
   No database needed for the game itself.
3. **Phones are dumb controllers** — Player devices submit inputs and render
   state. Zero game logic on the client.
4. **VIP controls the game** — First player to join gets host-level capabilities
   (start, kick, censor, settings). Transfers automatically on disconnect.
5. **Test with real players** — BDD tests spawn multiple browser contexts.
   No mocks. Real WebSocket connections. Real game flow.
6. **Ship the simplest game first** — Prompt-response (Quiplash pattern) is
   the easiest to build. Start there, add complexity later.

## Quick-Start

### "I want to build a party game from scratch"

| Step | Action | Reference |
|------|--------|-----------|
| 1 | Choose game type (prompt-response recommended for first game) | `references/game-types-and-mechanics.md` |
| 2 | Scaffold project structure (monorepo: server + host + player) | `references/game-architecture.md` |
| 3 | Set up Socket.IO server with room management | `references/multiplayer-networking.md` |
| 4 | Implement VIP role, kick/ban, room settings | `references/vip-and-room-authority.md` |
| 5 | Implement game state machine (phases, rounds, timers) | `references/game-state-machines.md` |
| 6 | Add content safety (profanity filter, moderation) | `references/content-safety-and-moderation.md` |
| 7 | Build host screen (TV display) and player controller (phone) | `references/frontend-patterns.md` |
| 8 | Write BDD tests with multiple browser contexts | `references/bdd-multiplayer-testing.md` |
| 9 | Deploy with WebSocket support | `references/deployment-and-ops.md` |

### "I want to add a new game type to an existing project"

| Step | Action |
|------|--------|
| 1 | Pick game type blueprint from `references/game-types-and-mechanics.md` |
| 2 | Define data models (prompts, answers, votes, scores) |
| 3 | Implement round loop phases in game state machine |
| 4 | Build game-specific UI components for host and player screens |
| 5 | Write BDD feature files for the new game flow |

### "I need to test multiplayer interactions"

| Step | Action |
|------|--------|
| 1 | Set up playwright-bdd with `.bdd/` directory structure |
| 2 | Create multi-player fixtures (2-8 browser contexts) |
| 3 | Write Gherkin with persona-based steps (`Given Player "Alice"...`) |
| 4 | Implement page objects: `LobbyPage`, `GamePage`, `ResultsPage` |
| 5 | Use `Promise.all()` for cross-player assertions |
| 6 | Adapt `assets/test-multiplayer-example.ts` for quick Socket.IO smoke tests |

## Development Workflow

### Phase 1: Lobby + VIP
Build room creation, room codes, player joining, VIP assignment, player list.
Test: 3 players join, first player is VIP, VIP badge visible.

### Phase 2: Game Loop
Implement phase transitions: Lobby -> Round Start -> Input -> Reveal -> Score.
Test: VIP starts the game, a complete round flows from prompt to scoring.

### Phase 3: Player Interaction
Add answer submission, voting, timer countdown, content filtering.
Test: Players submit answers, vote, scores update correctly. Profanity filtered.

### Phase 4: Moderation + Edge Cases
VIP kick/ban, content censoring, disconnect/reconnect, VIP migration.
Test: VIP kicks player. Player disconnects and reconnects mid-game.

### Phase 5: Polish
Animations, sound effects, haptic feedback, accessibility, mobile UX hardening.

### Phase 6: Deploy
Docker + Fly.io (or Railway). Redis adapter if scaling beyond one server.

## Decision Trees

### Which Game Type to Build First?

| If you want... | Build | Complexity |
|----------------|-------|------------|
| Easiest to implement | Prompt-response (Quiplash) | Low |
| Visual/creative | Drawing game (Drawful) | Medium |
| Knowledge-based | Trivia/quiz | Medium |
| Social deduction | Word association / Wavelength | High |

### Tech Stack

| Component | Default Choice | Alternative |
|-----------|---------------|-------------|
| Server | Express + Socket.IO | Fastify + Socket.IO |
| Frontend | React + Vite | Svelte, Vue |
| Styling | Tailwind CSS | CSS Modules |
| Animation | Framer Motion | CSS transitions |
| State machine | Plain TypeScript | XState (complex games) |
| Testing | playwright-bdd | @cucumber/cucumber + Playwright |
| Hosting | Fly.io | Railway, Render |

### When to Add a Database?

| Scenario | Recommendation |
|----------|---------------|
| Game state during play | In-memory only |
| Player accounts / history | Add PostgreSQL |
| Leaderboards across sessions | Add PostgreSQL |
| Custom prompt packs | JSON files or PostgreSQL |
| Analytics / game stats | Add PostgreSQL |

### VIP vs Host — When to Use Which?

| Concept | Role | Who Controls It |
|---------|------|-----------------|
| **Host** | The TV/projector display | The physical device running the app |
| **VIP** | First player to join | A player on their phone with host-level capabilities |
| **Player** | Participants | Everyone else on their phone |

See `references/vip-and-room-authority.md` for full VIP implementation guide.

### Content Safety Level

| Audience | Filter Level | Moderation |
|----------|-------------|------------|
| Private friends | `off` | None |
| Mixed group / default | `moderate` | Profanity filter |
| Family / streaming / work | `strict` + `familyFriendly` | Human moderation queue |

See `references/content-safety-and-moderation.md` for implementation.

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Client-side game logic | Server-authoritative state | Prevents cheating |
| Polling for game state | WebSocket push | Real-time updates |
| Use `isHost` for VIP | Use `isVIP` for the controlling player | Host = TV, VIP = player |
| Trust client for VIP actions | Validate `isVIP` server-side on every action | Security |
| Bypass content filtering | Add profanity filter at `moderate` minimum | Public safety |
| Shared browser context in tests | Separate `BrowserContext` per player | Isolated sessions |
| Fixed delays in tests | `waitForSelector` / event-based waits | Reliable timing |
| Database for live game state | In-memory Map/Object | Speed, simplicity |
| Mocking WebSocket in tests | Real Socket.IO connections | Tests what ships |
| Complex room code schemes | 4-char alphanumeric (exclude 0/O/1/I) | Easy to read aloud |

## Assets (Examples)

| File | Purpose |
|------|---------|
| `assets/test-multiplayer-example.ts` | Spawn N Socket.IO clients, replay a game round. Adapt to your event names. |
| `assets/lobby.feature` | Gherkin feature for lobby creation and joining |
| `assets/game-round.feature` | Gherkin feature for a complete game round |
| `assets/edge-cases.feature` | Gherkin feature for disconnect/reconnect scenarios |
| `assets/protocol-envelope.ts` | Event envelope with dedup, version gating, and phase guarding |
| `assets/audio-unlock-howler.tsx` | iOS audio unlock + preloader React provider (Howler.js) |
| `assets/room-timeline.ts` | Structured room event log for post-game forensics and debugging |
| `assets/loadtest-socketio.ts` | Load test harness: spawn virtual players, measure p50/p95/p99 latency |
| `assets/prompt-pack.schema.ts` | Prompt pack schema, validator, loader, and CLI validation runner |

## Reference Files

| File | Contents |
|------|----------|
| `references/game-architecture.md` | Host-player model, project structure, tech stack, data flow, server setup |
| `references/multiplayer-networking.md` | Socket.IO setup, room management, event protocols, state sync, reconnection, scaling |
| `references/game-state-machines.md` | Game phases, round loops, timers, player state, game configuration, complete Game class |
| `references/game-types-and-mechanics.md` | Prompt-response, drawing, trivia, voting systems, scoring, data models per game type |
| `references/vip-and-room-authority.md` | VIP role (vs host), assignment, transfer, disconnect, kick/ban, room settings, bot replacement |
| `references/content-safety-and-moderation.md` | Profanity filtering, moderation queues, family mode, censoring, accessibility, mobile UX hardening |
| `references/frontend-patterns.md` | Host screen (TV), player controller (phone), React components, socket hooks, responsive design |
| `references/bdd-multiplayer-testing.md` | Multi-client Playwright fixtures, Gherkin multi-actor patterns, page objects, edge case testing |
| `references/deployment-and-ops.md` | WebSocket hosting, Docker, Redis scaling, sticky sessions, room cleanup, production checklist |
