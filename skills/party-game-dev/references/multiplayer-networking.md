# Multiplayer Networking
Sources: Socket.IO documentation, Drawphone, Rocketcrab, production multiplayer game patterns

Multiplayer party games require a reliable, real-time bidirectional communication layer to synchronize game state across multiple devices. Socket.IO is the industry standard for these types of web-based experiences, providing automatic reconnection, room management, and fallback mechanisms essential for the varied network conditions of casual players.

## 1. Socket.IO Server Setup

A robust server initialization must handle cross-origin resource sharing (CORS) for separate frontend/backend deployments and configure transport settings for low-latency delivery.

```typescript
import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: process.env.CLIENT_URL || '*',
    methods: ['GET', 'POST'],
    credentials: true
  },
  pingInterval: 25000,
  pingTimeout: 60000,
  connectTimeout: 10000,
  maxHttpBufferSize: 1e6, // 1MB
  transports: ['websocket', 'polling']
});

io.on('connection', (socket) => {
  console.log(`Socket connected: ${socket.id}`);
  
  socket.on('disconnect', (reason) => {
    console.log(`Socket disconnected: ${socket.id} (Reason: ${reason})`);
  });
});

httpServer.listen(3000, () => {
  console.log('Socket.IO server running on port 3000');
});
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| pingInterval | 25000 | Frequency of heartbeat packets (ms) |
| pingTimeout | 50000 | Time without pong before disconnect (ms) |
| transports | ["polling", "websocket"] | Allowed connection methods (websocket preferred) |
| maxHttpBufferSize | 1e6 | Maximum payload size (1MB) before rejection |
| cookie | false | Whether to send a cookie with the handshake |

## 2. Room Management

Party games rely on a lobby system where players join via a short alphanumeric code. The `RoomManager` handles the lifecycle of these rooms, from generation to cleanup.

### Interfaces and State Definitions

```typescript
export interface Player {
  id: string;
  socketId: string;
  name: string;
  avatar?: string;
  score: number;
  isHost: boolean;
  isConnected: boolean;
}

export interface RoomState {
  code: string;
  status: 'LOBBY' | 'PLAYING' | 'REVEAL' | 'VOTING' | 'FINISHED';
  players: Player[];
  hostId: string;
  gameData: Record<string, any>;
  createdAt: number;
  lastActive: number;
}
```

### Room Code Generation

Codes should be 4-6 characters long and exclude visually ambiguous characters (0, O, I, 1, L) to improve usability for players entering codes on mobile devices.

```typescript
const generateRoomCode = (length: number = 4): string => {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let code = '';
  for (let i = 0; i < length; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
};
```

### RoomManager Implementation

```typescript
class RoomManager {
  private rooms: Map<string, RoomState> = new Map();

  createRoom(hostId: string, socketId: string, hostName: string): RoomState {
    let code = generateRoomCode();
    while (this.rooms.has(code)) {
      code = generateRoomCode();
    }
    
    const host: Player = {
      id: hostId,
      socketId,
      name: hostName,
      score: 0,
      isHost: true,
      isConnected: true
    };

    const room: RoomState = {
      code,
      hostId,
      players: [host],
      status: 'LOBBY',
      gameData: {},
      createdAt: Date.now(),
      lastActive: Date.now()
    };
    
    this.rooms.set(code, room);
    return room;
  }

  joinRoom(code: string, player: Player): RoomState {
    const room = this.rooms.get(code);
    if (!room) throw new Error('ROOM_NOT_FOUND');
    if (room.status !== 'LOBBY') throw new Error('GAME_IN_PROGRESS');
    if (room.players.length >= 8) throw new Error('ROOM_FULL');
    
    room.players.push(player);
    room.lastActive = Date.now();
    return room;
  }

  leaveRoom(code: string, playerId: string): void {
    const room = this.rooms.get(code);
    if (room) {
      room.players = room.players.filter(p => p.id !== playerId);
      if (room.players.length === 0) {
        this.rooms.delete(code);
      }
    }
  }
}
```

## 3. Event Protocol Design

Communication is defined by a strictly typed event protocol. Use camelCase verbs for event names and avoid generic 'data' events.

### Client-to-Server Event Protocol

| Event Name | Payload Type | Description |
|------------|--------------|-------------|
| createRoom | { name: string } | Create a new lobby with sender as host |
| joinRoom | { code: string, name: string } | Join an existing room by its code |
| startGame | void | Host starts the game transition |
| submitAnswer | { answer: string } | Submit data during a gameplay phase |
| vote | { targetId: string } | Cast a vote for a specific player or entry |
| leaveRoom | void | Explicitly leave the current room |

### Server-to-Client Event Protocol

| Event Name | Payload Type | Description |
|------------|--------------|-------------|
| roomJoined | { room: RoomState, you: Player } | Confirmation of successful join |
| playerJoined | { player: Player } | Broadcast to existing players in room |
| playerLeft | { playerId: string } | Broadcast when a player leaves or drops |
| stateUpdate | Partial<RoomState> | Delta or full update of room state |
| countdown | { seconds: number } | Synchronization for timed events |
| gameStarted | void | Notification that game logic has begun |
| error | { code: string, message: string } | Unified error reporting event |

### TypeScript Event Types

```typescript
export interface ServerToClientEvents {
  roomJoined: (data: { room: RoomState, you: Player }) => void;
  playerJoined: (player: Player) => void;
  playerLeft: (playerId: string) => void;
  stateUpdate: (state: Partial<RoomState>) => void;
  countdown: (data: { seconds: number }) => void;
  gameStarted: () => void;
  error: (err: { code: string, message: string }) => void;
}

export interface ClientToServerEvents {
  createRoom: (data: { name: string }) => void;
  joinRoom: (data: { code: string, name: string }) => void;
  submitAnswer: (data: { answer: string }) => void;
  startGame: () => void;
  vote: (data: { targetId: string }) => void;
}
```

## 4. State Synchronization

State in party games must be server-authoritative. The server maintains the master state and projects specific views to different players.

### Selective Broadcasting

Never broadcast sensitive information (like other players' hidden answers) to all clients. Use targeted emits for private data.

```typescript
// Broadcast to everyone in the room
io.to(roomCode).emit('gameState', publicState);

// Broadcast to everyone EXCEPT the sender
socket.to(roomCode).emit('playerAction', { id: socket.id, action: 'typed' });

// Send private data to a specific socket
socket.emit('privateData', { yourHiddenRole: 'Spy' });
```

### Delta Synchronization Pattern

Instead of sending the full state object on every change, send only the modified fields to minimize bandwidth and processing.

```typescript
const updatePlayerScore = (code: string, playerId: string, points: number) => {
  const room = roomManager.getRoom(code);
  const player = room.players.find(p => p.id === playerId);
  if (player) {
    player.score += points;
    // Broadcast only the updated scores
    io.to(code).emit('stateUpdate', {
      players: room.players.map(p => ({ id: p.id, score: p.score }))
    });
  }
};
```

### State Projection Pattern

```typescript
const projectStateForPlayer = (room: RoomState, playerId: string) => {
  return {
    players: room.players.map(p => ({
      id: p.id,
      name: p.name,
      score: p.score,
      isConnected: p.isConnected,
      hasSubmitted: !!room.gameData.submissions[p.id]
    })),
    status: room.status,
    // Only include submission if the player is the one who submitted it
    mySubmission: room.gameData.submissions[playerId] || null,
    // Other players' submissions are hidden until reveal phase
    revealCount: Object.keys(room.gameData.submissions).length,
    currentPrompt: room.gameData.currentPrompt
  };
};

// Sync the projected state to each player individually
const syncRoom = (code: string) => {
  const room = roomManager.getRoom(code);
  room.players.forEach(player => {
    const view = projectStateForPlayer(room, player.id);
    io.to(player.socketId).emit('stateUpdate', view);
  });
};
```

## 5. Connection Handling

Managing players joining, dropping, and reconnecting is critical for the "party" experience where players may switch apps or lose signal.

### Reconnection and Session Recovery

Store session identifiers (not just socket IDs) to allow players to reclaim their position in a room after a refresh.

```typescript
io.use((socket, next) => {
  const sessionID = socket.handshake.auth.sessionID;
  if (sessionID) {
    const session = sessionStore.findSession(sessionID);
    if (session) {
      socket.data.sessionID = sessionID;
      socket.data.userID = session.userID;
      socket.data.username = session.username;
      return next();
    }
  }
  socket.data.sessionID = crypto.randomUUID();
  socket.data.userID = crypto.randomUUID();
  next();
});
```

### Host Migration

When the host disconnects, the server must automatically designate a new host to prevent the room from becoming orphaned.

```typescript
const handleDisconnect = (socket: Socket) => {
  const room = roomManager.getRoomBySocket(socket.id);
  if (!room) return;

  roomManager.markPlayerDisconnected(room.code, socket.id);
  
  if (room.hostId === socket.id) {
    // Attempt to find the next active player to become host
    const nextHost = room.players.find(p => p.isConnected);
    if (nextHost) {
      room.hostId = nextHost.id;
      nextHost.isHost = true;
      io.to(room.code).emit('stateUpdate', { hostId: room.hostId });
    } else {
      // Room is empty or all disconnected, schedule for deletion after 5 minutes
      roomManager.scheduleCleanup(room.code, 300000);
    }
  }
};
```

## 6. Error Handling

Uncaught errors in event handlers can crash the entire Node.js process. Implement a safe event wrapper to catch exceptions and notify the offending client.

### Safe Event Wrapper Pattern

```typescript
const wrapHandler = (socket: Socket, handler: Function) => {
  return async (...args: any[]) => {
    try {
      await handler(...args);
    } catch (err: any) {
      console.error(`Socket Event Error [${socket.id}]:`, err);
      socket.emit('error', {
        code: err.code || 'INTERNAL_ERROR',
        message: err.message || 'An unexpected error occurred'
      });
    }
  };
};

// Application setup
io.on('connection', (socket) => {
  socket.on('submitAnswer', wrapHandler(socket, async (data: any) => {
    if (!data.answer || data.answer.length > 500) {
      throw new Error('INVALID_SUBMISSION');
    }
    await gameController.processAnswer(socket, data);
  }));
});
```

## 7. Scaling

As the player base grows, you must scale the server horizontally. This requires a shared message broker and sticky sessions at the load balancer level.

### Redis Adapter Setup

The Redis adapter allows multiple Socket.IO server instances to communicate. When a broadcast is emitted on Server A, it is published to Redis and picked up by Server B for delivery to its connected clients.

```typescript
import { createAdapter } from '@socket.io/redis-adapter';
import { createClient } from 'redis';

const setupScaling = async (io: Server) => {
  const pubClient = createClient({ url: process.env.REDIS_URL });
  const subClient = pubClient.duplicate();

  await Promise.all([pubClient.connect(), subClient.connect()]);
  
  io.adapter(createAdapter(pubClient, subClient));
  console.log('Redis adapter initialized for horizontal scaling');
};
```

### Infrastructure Configuration

Load balancers must be configured for "sticky sessions" because the Socket.IO handshake requires the client to talk to the same server instance throughout the upgrade process.

```nginx
# Nginx upstream config for sticky sessions
upstream game_servers {
    ip_hash; # Enables IP-based stickiness
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
    server 10.0.0.3:3000;
}

server {
    listen 80;
    location /socket.io/ {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_pass http://game_servers;
        
        # Required for WebSocket upgrades
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Increase timeouts for long-lived connections
        proxy_read_timeout 86400;
    }
}
```

### Performance Optimization

| Optimization | Strategy | Benefit |
|--------------|----------|---------|
| Binary Transmission | Send data as Buffer | Reduced CPU overhead, smaller payload |
| Message Batching | Group updates into 50ms windows | Lower packet count, reduced interrupt overhead |
| Volatile Emits | Use `volatile.emit()` | Prevents queue build-up on slow clients |
| Compression | `perMessageDeflate: true` | Significant bandwidth savings for large state |

### Summary Checklist

- Initialize server with appropriate CORS and transports.
- Use 4-character alphanumeric codes for room access, excluding ambiguous chars.
- Implement a centralized `RoomManager` for lifecycle management.
- Define a strictly typed event protocol for consistency and clarity.
- Enforce server-authoritative state with selective broadcasting of private data.
- Handle reconnections via persistent session identifiers stored in `socket.data`.
- Protect the server with async error-handling wrappers for all event listeners.
- Use a Redis adapter and sticky sessions when scaling horizontally.
