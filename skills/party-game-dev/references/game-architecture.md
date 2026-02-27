# Game Architecture
Sources: Jackbox Games reverse engineering, Drawphone, Rocketcrab, Fishbowl OSS implementations

Modern party games (Jackbox-style) use a distributed architecture where game logic and high-fidelity rendering are separated from player input and personalized feedback. This architecture enables low-barrier entry where players join via a web browser on their mobile devices without downloading an app.

## 1. Host-Player Model
The fundamental pattern is the split between a "Host" (the TV/Screen) and "Players" (the Phones).

| Component | Responsibility | Environment |
|-----------|----------------|-------------|
| **Host** | Game engine, authoritative logic, high-res audio/video, leaderboard. | Unity, Browser (Chrome), Electron. |
| **Player** | Controller UI, input submission, private information (e.g., secret prompts). | Mobile Browser (Safari, Chrome). |
| **Server** | Room orchestration, message relay, state synchronization, validation. | Node.js, Socket.IO, WebSocket. |

### Single-Screen vs. Dual-Screen
- **Single-Screen (Shared):** All information is public. Use for simple quizzes or party games where everyone sees the same screen. This is rarely used in high-end party games because it lacks the "private information" mechanic that drives humor and strategy.
- **Dual-Screen (Asymmetric):** Essential for games with hidden roles, drawing prompts, or private answers. The host screen shows the "show," while player screens show the "remote."

Use a dual-screen model for all modern party game development to support diverse game mechanics. This allows for individual player feedback, such as "It's your turn to draw!" or "Wait for other players," which is critical for engagement.

## 2. Project Structure
Organize the project as a monorepo to share types and utility logic between the server, host client, and player client. This prevents "type drift" where the server expects one format but the client sends another.

```text
party-game-root/
├── apps/
│   ├── server/           # Node.js + Socket.IO server
│   │   ├── src/
│   │   │   ├── managers/ # Room and Game managers
│   │   │   ├── logic/    # Core game loop and rules
│   │   │   ├── socket/   # Socket event handlers and middleware
│   │   │   ├── utils/    # Room code generators and validators
│   │   │   └── index.ts  # Entry point and server config
│   ├── client-host/      # React/Next.js for the TV screen
│   │   ├── src/
│   │   │   ├── components/ # Large-scale game animations and views
│   │   │   ├── hooks/      # Socket listeners for game state
│   │   │   ├── store/      # Local state management (Zustand/Redux)
│   │   │   └── assets/     # High-res sprites, shaders, and audio
│   └── client-player/    # React for the phone controllers
│       ├── src/
│       │   ├── components/ # Specialized input (Canvas, Text, Sliders)
│       │   ├── hooks/      # Interaction handlers and local state
│       │   ├── styles/     # Mobile-optimized CSS (Tailwind)
│       │   └── assets/     # Lightweight icons and UI sprites
├── packages/
│   └── shared/           # Shared TypeScript types and constants
│       ├── src/
│       │   ├── types.ts  # State, Player, and Message interfaces
│       │   ├── events.ts # Socket event name constants
│       │   ├── constants.ts # Game-wide config (timers, player limits)
│       │   └── schemas/  # Zod validation schemas
└── package.json
```

### Shared Types Example
Defining shared interfaces ensures that `client-host` and `client-player` are always in sync with the `server`.

```typescript
// packages/shared/src/types.ts
export interface Player {
  id: string;
  name: string;
  score: number;
  role: 'PLAYER' | 'AUDIENCE';
  isHost: boolean;
  isConnected: boolean;
  avatar?: string;
  lastInput?: string;
}

export interface GameRoom {
  code: string;
  state: string;
  players: Player[];
  timer: number;
  maxPlayers: number;
  currentRound: number;
}
```

## 3. Tech Stack Recommendations
Choose the stack based on the complexity of the game state and persistence requirements.

| Stack Component | Recommended Choice | Reasoning |
|-----------------|--------------------|-----------|
| **Real-time** | Socket.IO | Handles reconnections, rooms, and namespaces out of the box. |
| **Backend** | Node.js + Express | Fast prototyping and unified JS/TS codebase. |
| **Frontend** | React + Tailwind | Component-based UI for complex player controllers. |
| **State** | In-Memory (Map/Object) | Party games are ephemeral; persistence is rarely needed. |
| **Language** | TypeScript | Mandatory for sharing types between clients and server. |
| **Validation** | Zod | Runtime type checking for all incoming socket data. |

### Essential Dependencies
Include these in the `apps/server/package.json`:
```json
{
  "dependencies": {
    "express": "^4.18.0",
    "socket.io": "^4.7.0",
    "zod": "^3.22.0",
    "nanoid": "^3.3.0",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "dotenv": "^16.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "ts-node-dev": "^2.0.0"
  }
}
```

Use `nanoid` for generating 4-character uppercase room codes (e.g., `ABCD`) to ensure accessibility and ease of typing on mobile. Avoid using similar-looking characters like `0` and `O` or `1` and `I` if using alphanumeric codes.

## 4. Data Flow Patterns
Data flows in a unidirectional loop to maintain consistency across all connected clients. The server acts as the single source of truth.

```text
[ Player Input (Phone) ]
       │ (Socket Event: 'input:submit')
       ▼
[ Server Middleware ]
       │ (Zod Validation, Auth Check, Rate Limit)
       ▼
[ Game Logic Handler ]
       │ (Calculate points, update logic, transition phases)
       ▼
[ Room State Update ]
       │ (Update in-memory Room object)
       ▼
[ Broadcast Update ]
       │ (Socket Event: 'room:update')
       ▼
[ UI Render (TV & Phone) ]
       │ (Host updates TV display with animations, Players update phone UI)
       └───────► (Repeat for next player or phase)
```

### Broadcast vs. Targeted Communication
Server communication follows three primary patterns:
1. **Broadcast (Host -> All):** Host pushes a "Next Round" event; everyone's UI transitions.
2. **Targeted (Server -> Specific Player):** Server pushes a secret prompt only to Player 3.
3. **Aggregated (Players -> Host):** Server collects all answers and pushes a "All Answers Received" event to the Host to trigger the reveal animation.

## 5. Server Architecture
The server manages multiple game rooms concurrently. Each room is an isolated instance of a game session.

### Room Class Implementation
A robust `Room` class manages its own lifecycle and player list.

```typescript
// apps/server/src/logic/Room.ts
export class Room {
  public code: string;
  public players: Map<string, Player> = new Map();
  public state: string = 'LOBBY';
  public timer: number = 0;
  public createdAt: number = Date.now();

  constructor(code: string) {
    this.code = code;
  }

  public addPlayer(id: string, name: string): Player {
    const player: Player = { 
      id, 
      name, 
      score: 0, 
      role: 'PLAYER',
      isConnected: true, 
      isHost: this.players.size === 0 
    };
    this.players.set(id, player);
    return player;
  }

  public serialize(role: 'HOST' | 'PLAYER', playerId?: string): any {
    const playersArray = Array.from(this.players.values()).map(p => ({
      id: p.id,
      name: p.name,
      score: p.score,
      isConnected: p.isConnected,
      isHost: p.isHost
    }));

    return {
      code: this.code,
      state: this.state,
      players: playersArray,
      timer: this.timer
    };
  }
}
```

### Access Control Lists (ACLs)
Implement ACLs to restrict which clients can view or modify specific state objects.
- **Host Only:** Scoring data, raw answers (before reveal), debug logs.
- **Player Only:** Their own secret prompt, their current draft answer.
- **Global:** Game state, room code, player list, scores (after reveal).

### Room Manager & Cleanup Logic
The `RoomManager` uses a `Map` for O(1) room lookup and handles the generation of unique codes.

```typescript
// apps/server/src/managers/RoomManager.ts
export class RoomManager {
  private rooms: Map<string, Room> = new Map();
  private readonly CODE_LENGTH = 4;
  private readonly ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ';

  public createRoom(): Room {
    const code = this.generateUniqueCode();
    const room = new Room(code);
    this.rooms.set(code, room);
    return room;
  }

  public getRoom(code: string): Room | undefined {
    return this.rooms.get(code.toUpperCase());
  }

  private generateUniqueCode(): string {
    let code = '';
    while (true) {
      for (let i = 0; i < this.CODE_LENGTH; i++) {
        code += this.ALPHABET[Math.floor(Math.random() * this.ALPHABET.length)];
      }
      if (!this.rooms.has(code) && !this.isOffensive(code)) break;
      code = '';
    }
    return code;
  }

  private isOffensive(code: string): boolean {
    const forbidden = ['FUCK', 'SHIT', 'PISS', 'HELL'];
    return forbidden.includes(code);
  }
}
```

## 6. Key Design Decisions

### Server-Authoritative Logic
The server must control all critical game elements.
- **Scoring:** Only the server calculates points based on validated player actions.
- **Phase Control:** The server decides when to move from prompting to voting based on timers or completion.

### In-Memory State Strategy
For party games, avoid persistent databases like PostgreSQL or MongoDB during active gameplay.
- **Speed:** In-memory access is the fastest possible way to handle 100ms response cycles.
- **Simplicity:** No need to handle database connections or complex schemas for transient data.
- **Cleanup:** Implement an aggressive cleanup policy. If a room has no active players for 5 minutes, delete it.

### Latency Compensation
While party games aren't competitive shooters, "input lag" on a phone can feel sluggish.
- **Optimistic UI:** When a player clicks "Submit," show a "Submitted!" state immediately on the phone before the server acknowledges.
- **Rollback:** If the server rejects the input (e.g., round ended just as they clicked), show an error and return to the input state.

### Disconnect Grace Periods
Mobile connections are unstable. Implement a grace period for player reconnections.
1. When a player disconnects, mark `player.isConnected = false`.
2. Do not remove them from the room for 60 seconds.
3. If they reconnect with the same `sessionID` (stored in `localStorage`), map them back to their existing `Player` object.
4. If the timer expires, remove them and re-assign the host role if the disconnected player was the host.

### Host Migration Logic
If the host (the TV screen) disconnects, the game cannot usually continue.
- **Detection:** Use the `disconnect` event.
- **Action:** If `player.isHost` is true, wait 15 seconds. If they don't reconnect, broadcast `game:ended` to all players.
- **Optional:** Allow any connected player to "Request Host" and take over the TV view.

### Audience Mode Implementation
Support "Audience" roles for games played on stream (Twitch/YouTube).
- **Threshold:** Set `maxPlayers` (e.g., 8). Any player joining after this is assigned `role: 'AUDIENCE'`.
- **Filtering:** Use `room.players.filter(p => p.role === 'PLAYER')` for game logic and `room.players.filter(p => p.role === 'AUDIENCE')` for crowd-sourced voting.

### Mobile UI Constraints
Player controllers must be designed for mobile constraints.
- **Viewport:** Use `100vh` carefully (or `-webkit-fill-available`) to handle mobile browser address bars.
- **Orientation:** Force portrait or landscape via CSS/JS if required, but portrait is preferred for one-handed play.
- **Keyboard:** Ensure inputs don't cover the "Submit" button when the virtual keyboard is open.

### Asymmetric Game Design
The core of the "Jackbox feel" is giving players unique information that the TV doesn't show.
- **Player Prompts:** Send a specific question to Player A that Player B doesn't see.
- **Secret Roles:** In social deduction games, only the player's phone knows their identity.
- **Private Feedback:** Use the phone to tell a player "You're the only one who got that right!" to create personal moments.

### Development Workflow Patterns
1. **Mock Players:** Write a script to spawn 5-8 headless socket clients that join a room and submit random answers.
2. **Local Networking:** Use `localhost` for development, but test on actual phones early using `ngrok` or your local network IP.
3. **Debug Logs:** Log room creation, player joins, and phase transitions to the console for easy tracing.

### Scaling and Infrastructure
While in-memory works for single servers, scaling to thousands of rooms requires architectural adjustments.
- **Sticky Sessions:** If using multiple server instances, ensure a client stays connected to the server hosting their specific room code.
- **Vertical Scaling:** Start with a single powerful server. Horizontal scaling adds significant complexity to in-memory state management (requires Redis or similar).

### Conclusion on Architecture
The architecture of a party game must prioritize **access** and **availability**. By using a server-authoritative, in-memory model with a split Host/Player frontend, you create a robust system that can handle the unique challenges of mobile-web gaming. The monorepo structure and shared TypeScript types ensure that the complex multi-client synchronization remains manageable as the game grows. Use the Host-Player model to create a "digital living room" where the technology disappears and the focus remains on the social interaction.
