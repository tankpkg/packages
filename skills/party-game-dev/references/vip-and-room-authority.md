# VIP and Room Authority

Sources: Jackbox Games official documentation, Rocketcrab OSS (tannerkrewson/rocketcrab), Drawphone (tannerkrewson/drawphone), anime-character-guessr VIP transfer patterns

Covers: VIP concept and distinction from host, VIP assignment and transfer, room settings, kick/ban system, bot replacement on disconnect, implementation patterns with Socket.IO.

## 1. The VIP Concept

In Jackbox-style party games, three distinct roles exist. The existing codebase often conflates "Host" and "VIP" — this section clarifies the correct model.

| Role | What It Is | Where It Lives | Capabilities |
|------|-----------|----------------|--------------|
| **Host** | The TV/computer running the game | Physical device (console, PC, projector) | Displays game to all players, plays audio, shows animations |
| **VIP** | The first player to join the room | Phone/tablet at the game URL | Starts rounds, censors content, kicks players, controls flow, manages settings |
| **Player** | Any non-VIP participant | Phone/tablet at the game URL | Submits answers, votes, views personal prompts |

The Host is **not a player**. It is a display device. The VIP is a **player with host-level capabilities**. In Jackbox's own words: "The VIP is the first person to get in the game and the raw, unmitigated responsibility that comes with it is staggering."

### Why the Distinction Matters

- The Host screen has no input — it cannot start the game or kick players
- The VIP controls the game flow from their phone
- If the TV disconnects, the game cannot continue (no display)
- If the VIP disconnects, their privileges transfer to the next player
- Streaming setups require the streamer to be VIP so they control pacing

### Data Model

Update the shared `Player` interface to include VIP status:

```typescript
// packages/shared/src/types.ts
export interface Player {
  id: string;
  socketId: string;
  name: string;
  score: number;
  isVIP: boolean;       // Elevated privileges (start, kick, censor)
  isConnected: boolean;
  avatar?: string;
}

export interface GameRoom {
  code: string;
  state: GamePhase;
  players: Player[];
  idealVipId: string;   // Preferred VIP (survives reconnects)
  settings: RoomSettings;
  createdAt: number;
  lastActive: number;
}
```

Do **not** use `isHost` on the Player to mean VIP. Reserve `isHost` for the display connection if tracking it at all.

## 2. VIP Assignment

The first player to join a room automatically becomes VIP. Store the `idealVipId` at room level so VIP survives reconnection cycles.

```typescript
class Room {
  public players: Map<string, Player> = new Map();
  public idealVipId: string | null = null;

  addPlayer(id: string, name: string, socketId: string): Player {
    const player: Player = {
      id,
      socketId,
      name,
      score: 0,
      isVIP: false,
      isConnected: true,
    };
    this.players.set(id, player);

    // First player becomes the preferred VIP
    if (this.players.size === 1) {
      this.idealVipId = id;
    }

    this.assignVIP();
    return player;
  }

  private assignVIP(): void {
    // Clear all VIP flags
    for (const player of this.players.values()) {
      player.isVIP = false;
    }

    // Try ideal VIP first
    const ideal = this.players.get(this.idealVipId ?? '');
    if (ideal && ideal.isConnected) {
      ideal.isVIP = true;
      return;
    }

    // Fallback: connected player who joined earliest (lowest numeric order)
    const connected = Array.from(this.players.values())
      .filter(p => p.isConnected);
    if (connected.length > 0) {
      connected[0].isVIP = true;
    }
  }
}
```

This pattern is adapted from Rocketcrab's `idealHostId` + `setHost()` approach, where the party stores a preferred host ID and reassigns on every join/leave event.

## 3. VIP Responsibilities

### Actions Only the VIP Can Perform

| Action | When | Implementation Pattern |
|--------|------|----------------------|
| **Start game** | Lobby phase, min players met | `socket.on('game:start')` → check `isVIP` |
| **Skip content** | During reveal or voting | `socket.on('content:skip')` → advance phase |
| **Censor content** | During reveal | `socket.on('content:censor')` → hide from display |
| **Kick player** | Any phase | `socket.on('player:kick')` → remove + optional ban |
| **Change settings** | Lobby phase only | `socket.on('settings:update')` → validate + broadcast |
| **End game early** | Playing phase | `socket.on('game:end')` → transition to GAME_OVER |
| **Next round** | Between rounds | `socket.on('round:next')` → start next round |

### Server-Side Validation (Mandatory)

Never trust the client. Every VIP action must be validated server-side:

```typescript
const requireVIP = (socket: Socket, room: Room): boolean => {
  const player = room.getPlayerBySocketId(socket.id);
  if (!player?.isVIP) {
    socket.emit('error', { code: 'NOT_VIP', message: 'Only the VIP can do that' });
    return false;
  }
  return true;
};

// Usage in event handlers
socket.on('game:start', () => {
  const room = roomManager.getRoomBySocket(socket.id);
  if (!room || !requireVIP(socket, room)) return;
  if (room.players.size < room.settings.minPlayers) {
    socket.emit('error', { code: 'MIN_PLAYERS', message: 'Not enough players' });
    return;
  }
  room.startGame();
  io.to(room.code).emit('game:started');
});

socket.on('player:kick', ({ targetId }: { targetId: string }) => {
  const room = roomManager.getRoomBySocket(socket.id);
  if (!room || !requireVIP(socket, room)) return;
  room.kickPlayer(targetId);
});
```

## 4. VIP Transfer

Jackbox does not support VIP transfer. However, OSS games commonly implement it. Allow the current VIP to hand off privileges to another player.

```typescript
socket.on('vip:transfer', ({ newVipId }: { newVipId: string }) => {
  const room = roomManager.getRoomBySocket(socket.id);
  if (!room || !requireVIP(socket, room)) return;

  const newVIP = room.players.get(newVipId);
  if (!newVIP || !newVIP.isConnected) {
    socket.emit('error', { code: 'INVALID_TARGET', message: 'Player not found' });
    return;
  }

  const oldVIP = room.getVIP();
  room.idealVipId = newVipId;
  room.assignVIP();

  io.to(room.code).emit('vip:transferred', {
    oldVipName: oldVIP?.name,
    newVipName: newVIP.name,
  });
});
```

### VIP Transfer Event Protocol

| Event | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `vip:transfer` | Client → Server | `{ newVipId: string }` | Current VIP requests transfer |
| `vip:transferred` | Server → All | `{ oldVipName, newVipName }` | Broadcast new VIP identity |
| `vip:assigned` | Server → All | `{ playerId, playerName }` | Auto-assignment notification |

## 5. VIP Disconnect Handling

When the VIP disconnects, automatically reassign to the next available player. Use the `assignVIP()` method which falls back gracefully.

```typescript
const handleDisconnect = (socket: Socket): void => {
  const room = roomManager.getRoomBySocket(socket.id);
  if (!room) return;

  const player = room.getPlayerBySocketId(socket.id);
  if (!player) return;

  player.isConnected = false;
  room.lastActive = Date.now();

  const wasVIP = player.isVIP;

  // In lobby: remove immediately. In game: keep for reconnection
  if (room.state === 'LOBBY') {
    room.removePlayer(player.id);
  }

  // Reassign VIP if needed
  if (wasVIP) {
    room.assignVIP();
    const newVIP = room.getVIP();
    if (newVIP) {
      io.to(room.code).emit('vip:assigned', {
        playerId: newVIP.id,
        playerName: newVIP.name,
      });
    }
  }

  io.to(room.code).emit('player:disconnected', { playerId: player.id });
};
```

### Reconnection

When a player reconnects with a matching session ID, update their `socketId`, set `isConnected = true`, rejoin the Socket.IO room, then call `assignVIP()`. If this player is the `idealVipId`, they will be restored as VIP automatically. Emit `reconnected` with the full room state and the player's own data.

## 6. Kick and Ban System

VIP can kick (temporary) or ban (IP-based, permanent for session) players.

```typescript
interface KickResult {
  success: boolean;
  reason?: string;
}

class Room {
  private bannedIPs: Set<string> = new Set();

  kickPlayer(targetId: string, ban = false): KickResult {
    const target = this.players.get(targetId);
    if (!target) return { success: false, reason: 'Player not found' };
    if (target.isVIP) return { success: false, reason: 'Cannot kick VIP' };

    if (ban && target.socketId) {
      // Store IP for ban enforcement
      const ip = this.getPlayerIP(target.socketId);
      if (ip) this.bannedIPs.add(ip);
    }

    // Disconnect and remove
    const targetSocket = io.sockets.sockets.get(target.socketId);
    if (targetSocket) {
      targetSocket.emit('kicked', { reason: ban ? 'banned' : 'kicked' });
      targetSocket.leave(this.code);
      targetSocket.disconnect(true);
    }

    this.players.delete(targetId);
    this.assignVIP(); // In case order changed
    return { success: true };
  }

  isIPBanned(ip: string): boolean {
    return this.bannedIPs.has(ip);
  }
}
```

### Join Validation with Ban Check

```typescript
socket.on('room:join', ({ code, name }: { code: string; name: string }) => {
  const room = roomManager.getRoom(code);
  if (!room) return socket.emit('error', { code: 'ROOM_NOT_FOUND' });

  const ip = socket.handshake.address;
  if (room.isIPBanned(ip)) {
    return socket.emit('error', { code: 'BANNED', message: 'You are banned from this room' });
  }

  // ... normal join logic
});
```

## 7. Room Settings

The VIP configures game settings during the lobby phase. Settings are locked once the game starts.

```typescript
interface RoomSettings {
  maxPlayers: number;       // 2-16, default 8
  minPlayers: number;       // 2-8, default 3
  roundCount: number;       // 1-10, default 3
  submitDuration: number;   // seconds, default 60
  voteDuration: number;     // seconds, default 30
  contentFilter: 'off' | 'moderate' | 'strict';  // default 'moderate'
  familyFriendly: boolean;  // default false
  allowAudience: boolean;   // default true
  promptPack: string;       // pack ID, default 'standard'
}

const DEFAULT_SETTINGS: RoomSettings = {
  maxPlayers: 8,
  minPlayers: 3,
  roundCount: 3,
  submitDuration: 60,
  voteDuration: 30,
  contentFilter: 'moderate',
  familyFriendly: false,
  allowAudience: true,
  promptPack: 'standard',
};
```

### Settings Update Handler

```typescript
import { z } from 'zod';

const settingsSchema = z.object({
  maxPlayers: z.number().min(2).max(16).optional(),
  minPlayers: z.number().min(2).max(8).optional(),
  roundCount: z.number().min(1).max(10).optional(),
  submitDuration: z.number().min(15).max(300).optional(),
  voteDuration: z.number().min(10).max(120).optional(),
  contentFilter: z.enum(['off', 'moderate', 'strict']).optional(),
  familyFriendly: z.boolean().optional(),
  allowAudience: z.boolean().optional(),
  promptPack: z.string().optional(),
});

socket.on('settings:update', (data: unknown) => {
  const room = roomManager.getRoomBySocket(socket.id);
  if (!room || !requireVIP(socket, room)) return;
  if (room.state !== 'LOBBY') {
    return socket.emit('error', { code: 'GAME_IN_PROGRESS' });
  }

  const parsed = settingsSchema.safeParse(data);
  if (!parsed.success) {
    return socket.emit('error', { code: 'INVALID_SETTINGS' });
  }

  Object.assign(room.settings, parsed.data);
  io.to(room.code).emit('settings:updated', room.settings);
});
```

## 8. Bot Replacement

When a player disconnects mid-game, replace them with a bot to prevent the round from stalling. Pattern adapted from Drawphone.

```typescript
interface BotPlayer extends Player {
  isBot: true;
  originalPlayerId: string;  // ID of the player this bot replaced
}

const BOT_NAMES = [
  'RoboWriter', 'AutoVote', 'SillyBot', 'QuipMaster',
  'DrawBot', 'VoteBot', 'AnswerBot', 'JokeBot',
];

class Room {
  replaceWithBot(disconnectedId: string): BotPlayer | null {
    const player = this.players.get(disconnectedId);
    if (!player || this.state === 'LOBBY') return null;

    const bot: BotPlayer = {
      id: `bot-${disconnectedId}`,
      socketId: '',
      name: `${player.name} (Bot)`,
      score: player.score,
      isVIP: false,  // Bots never become VIP
      isConnected: true,
      isBot: true,
      originalPlayerId: disconnectedId,
    };

    this.players.delete(disconnectedId);
    this.players.set(bot.id, bot);
    return bot;
  }
}
```

When the timer expires, iterate over bot players and auto-submit `'(No answer)'` for any that haven't submitted. This prevents the game from stalling.

## 9. VIP UI Patterns

### Player List with VIP Badge

```tsx
const PlayerList = ({ players }: { players: Player[] }) => (
  <ul className="space-y-2">
    {players.map(player => (
      <li key={player.id} className="flex items-center gap-3 p-3 bg-white rounded-xl">
        <span className="text-lg font-bold">{player.name}</span>
        {player.isVIP && (
          <span className="bg-yellow-400 text-yellow-900 text-xs font-black px-2 py-0.5 rounded-full uppercase">
            VIP
          </span>
        )}
        {!player.isConnected && (
          <span className="text-red-400 text-sm">Disconnected</span>
        )}
      </li>
    ))}
  </ul>
);
```

### VIP Controls on Player Phone

Show a "VIP Controls" panel only to the VIP player. Include a start button and a collapsible kick list using `<details>`. Gate with `if (!isVIP) return null`. Style the panel with a distinct border color (e.g., `border-yellow-300 bg-yellow-50`) so the VIP knows they have special powers.

### Host Screen VIP Indicator

On the TV lobby screen, display who is VIP: `"{vip.name} is the VIP — they'll start the game"`. This tells the room who controls the game flow.

## 10. Checklist

Before shipping VIP functionality:

| Item | Requirement |
|------|-------------|
| VIP assignment | First player to join becomes VIP |
| Server validation | Every VIP action checked server-side |
| Disconnect handling | VIP auto-reassigns on disconnect |
| Reconnection | `idealVipId` restored on reconnect |
| Kick/ban | VIP can remove players; IP ban prevents rejoin |
| Settings | VIP controls room settings in lobby only |
| UI badge | VIP clearly marked on player list |
| Host display | TV shows who is VIP |
| Bot replacement | Mid-game disconnects replaced with bots |
| Transfer | Optional: VIP can hand off to another player |
