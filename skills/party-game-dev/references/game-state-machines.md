# Game State Machines

Sources: XState documentation, Drawphone game logic, production party game state patterns

## Game Phases

Game phases define the high-level state of the game room. Use a central `GamePhase` enum to manage these transitions.

```typescript
enum GamePhase {
  LOBBY = 'LOBBY',
  PLAYING = 'PLAYING',
  ROUND_END = 'ROUND_END',
  GAME_OVER = 'GAME_OVER'
}
```

### Phase Transition Flow

The game starts in the Lobby and cycles through Playing and Round End before concluding.

```text
[ LOBBY ] --(START)--> [ PLAYING ] <----┐
   |                      |             |
(EXIT)                    |          (NEXT)
   |                   (FINISH)         |
   v                      v             |
[ CLOSED ]             [ ROUND_END ] ---┘
                          |
                       (DONE)
                          |
                          v
                     [ GAME_OVER ]
```

### Transition Table

| Current Phase | Event | Target Phase | Guard / Condition |
| --- | --- | --- | --- |
| LOBBY | START_GAME | PLAYING | Min players met |
| PLAYING | FINISH_ROUND | ROUND_END | Round timer expired or all submitted |
| ROUND_END | NEXT_ROUND | PLAYING | More rounds remaining |
| ROUND_END | SHOW_RESULTS | GAME_OVER | Final round complete |
| GAME_OVER | PLAY_AGAIN | LOBBY | Reset scores and state |

## Round Loop

The Round Loop is a sub-state machine within the `PLAYING` phase. For prompt-based games, implement these sequential phases:

```typescript
enum RoundPhase {
  PROMPTING = 'PROMPTING',   // Initial prompt display
  SUBMITTING = 'SUBMITTING', // Players writing/drawing
  REVEALING = 'REVEALING',   // Animation/presentation
  VOTING = 'VOTING',         // Players picking favorites
  SCORING = 'SCORING'        // Awarding points
}
```

### Implementing Round Logic

Use a simple class-based approach to manage the loop.

```typescript
class RoundLoop {
  private current: RoundPhase = RoundPhase.PROMPTING;
  private order = [
    RoundPhase.PROMPTING,
    RoundPhase.SUBMITTING,
    RoundPhase.REVEALING,
    RoundPhase.VOTING,
    RoundPhase.SCORING
  ];

  next(): RoundPhase | null {
    const currentIndex = this.order.indexOf(this.current);
    if (currentIndex < this.order.length - 1) {
      this.current = this.order[currentIndex + 1];
      return this.current;
    }
    return null; // Loop complete
  }

  getCurrent() { return this.current; }
}
```

## State Machine Implementation

### Approach A: Plain TypeScript (Switch/Case)

Recommended for 90% of party games. It is easy to read, debug, and maintain without external dependencies.

```typescript
class GameState {
  private phase: GamePhase = GamePhase.LOBBY;

  update(event: string) {
    switch (this.phase) {
      case GamePhase.LOBBY:
        if (event === 'START') this.transition(GamePhase.PLAYING);
        break;
      case GamePhase.PLAYING:
        if (event === 'ROUND_COMPLETE') this.transition(GamePhase.ROUND_END);
        break;
      // ... more phases
    }
  }

  private transition(next: GamePhase) {
    console.log(`Transition: ${this.phase} -> ${next}`);
    this.phase = next;
    // Emit event to clients via Socket.IO
  }
}
```

### Approach B: XState (Complex Logic)

Use XState only if your game has complex hierarchical states or concurrent phases (e.g., multiple tasks running at once).

```typescript
import { createMachine } from 'xstate';

const gameMachine = createMachine({
  id: 'partyGame',
  initial: 'lobby',
  states: {
    lobby: { on: { START: 'playing' } },
    playing: {
      initial: 'submitting',
      states: {
        submitting: { on: { ALL_DONE: 'voting' } },
        voting: { on: { VOTES_IN: 'results' } },
        results: { type: 'final' }
      },
      onDone: 'roundEnd'
    },
    roundEnd: { /* ... */ }
  }
});
```

### Decision Table

| Metric | Plain TypeScript | XState |
| --- | --- | --- |
| Complexity | Low | High |
| Learning Curve | Instant | Steep |
| Bundle Size | Zero | ~20kb |
| Visualization | Manual | Automatic |
| Use Case | Simple round loops | Branched/Parallel states |

## Timer Mechanics

Timers must run on the server to prevent cheating and ensure all players stay synced.

```typescript
class GameTimer {
  private timer: NodeJS.Timeout | null = null;
  private duration: number = 0;
  private elapsed: number = 0;
  private paused: boolean = false;
  private onComplete: () => void;

  constructor(onComplete: () => void) {
    this.onComplete = onComplete;
  }

  start(seconds: number) {
    this.stop();
    this.duration = seconds;
    this.elapsed = 0;
    this.paused = false;
    this.timer = setInterval(() => {
      if (!this.paused) {
        this.elapsed++;
        if (this.elapsed >= this.duration) {
          this.stop();
          this.onComplete();
        }
      }
    }, 1000);
  }

  pause() {
    this.paused = true;
  }

  resume() {
    this.paused = false;
  }

  extend(seconds: number) {
    this.duration += seconds;
  }

  stop() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  getRemaining() {
    return Math.max(0, this.duration - this.elapsed);
  }

  isPaused() {
    return this.paused;
  }
}
```

### Server-Client Sync

The server calculates the remaining time and broadcasts a `TIMER_UPDATE` with `remainingSeconds` every 1-2 seconds.

```typescript
// On Server
setInterval(() => {
  io.to(roomCode).emit('timerUpdate', {
    remaining: game.timer.getRemaining(),
    paused: game.timer.isPaused()
  });
}, 2000);
```

On the client, use the received sync to update the UI but maintain a local decrement to prevent jittery countdowns.

## Player State Management

Manage players in a central `PlayerManager` class to handle connections, readiness, and scoring.

```typescript
interface Player {
  id: string;
  name: string;
  score: number;
  isConnected: boolean;
  isReady: boolean;
  isHost: boolean;
  currentSubmission: any | null;
}

class PlayerManager {
  private players: Map<string, Player> = new Map();

  add(id: string, name: string) {
    const isFirst = this.players.size === 0;
    this.players.set(id, {
      id,
      name,
      score: 0,
      isConnected: true,
      isReady: false,
      isHost: isFirst,
      currentSubmission: null
    });
  }

  disconnect(id: string) {
    const player = this.players.get(id);
    if (player) player.isConnected = false;
  }

  reconnect(id: string) {
    const player = this.players.get(id);
    if (player) player.isConnected = true;
  }

  remove(id: string) {
    this.players.delete(id);
  }

  setReady(id: string, ready: boolean) {
    const player = this.players.get(id);
    if (player) player.isReady = ready;
  }

  allReady(): boolean {
    const active = this.getActive();
    return active.length > 0 && active.every(p => p.isReady);
  }

  getActive(): Player[] {
    return Array.from(this.players.values()).filter(p => p.isConnected);
  }

  getScores() {
    return Array.from(this.players.values()).map(p => ({
      name: p.name,
      score: p.score
    }));
  }

  addScore(id: string, points: number) {
    const player = this.players.get(id);
    if (player) player.score += points;
  }
}
```

## Game Configuration

Use a standardized config object to allow customization per room. Sensible defaults are crucial for a good user experience.

```typescript
interface GameConfig {
  maxPlayers: number;
  minPlayers: number;
  roundCount: number;
  submitDuration: number; // in seconds
  voteDuration: number;
  revealDuration: number;
}

const DEFAULT_CONFIG: GameConfig = {
  maxPlayers: 8,
  minPlayers: 3,
  roundCount: 3,
  submitDuration: 60,
  voteDuration: 30,
  revealDuration: 10
};

## Complete Game Class


The Game class acts as the orchestrator for all other components.

```typescript
class PartyGame {
  private players = new PlayerManager();
  private phase = GamePhase.LOBBY;
  private currentRound = 0;
  private timer: GameTimer;
  private config: GameConfig;

  constructor(config: GameConfig = DEFAULT_CONFIG) {
    this.config = config;
    this.timer = new GameTimer(() => this.onTimeUp());
  }

  start() {
    if (this.players.allReady()) {
      this.transitionTo(GamePhase.PLAYING);
      this.startRound();
    }
  }

  private startRound() {
    this.currentRound++;
    this.timer.start(this.config.submitDuration);
    // Notify clients about the round start
  }

  private onTimeUp() {
    switch (this.phase) {
      case GamePhase.PLAYING:
        this.transitionTo(GamePhase.ROUND_END);
        break;
      case GamePhase.ROUND_END:
        if (this.currentRound < this.config.roundCount) {
          this.transitionTo(GamePhase.PLAYING);
          this.startRound();
        } else {
          this.transitionTo(GamePhase.GAME_OVER);
        }
        break;
    }
  }

  private transitionTo(next: GamePhase) {
    console.log(`Entering phase: ${next}`);
    this.phase = next;
    // Emit notification to all clients via Socket.IO
  }

  // Socket event handlers
  handlePlayerJoin(id: string, name: string) {
    if (this.phase !== GamePhase.LOBBY) return;
    this.players.add(id, name);
  }

  handleSubmission(id: string, submission: any) {
    if (this.phase !== GamePhase.PLAYING) return;
    // Store submission, check if all are done
  }
}
```

### State Management Best Practices

1. **State Persistence**: Games are typically stored in a `Map<roomCode, PartyGame>`. Implement an auto-cleanup script for inactive rooms.
2. **Reconnection Support**: Use a unique `playerId` (not the socket ID) to track players. When a player reconnects, re-map their new socket to the existing player object.
3. **Data Stripping**: Before broadcasting state, strip private data (like others' answers during the submission phase).
4. **Validation**: Always validate events from the client. Don't allow a `START_GAME` event from a non-host player.

