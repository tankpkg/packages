# Deployment and Operations
Sources: Socket.IO scaling documentation, WebSocket hosting best practices, production party game deployment patterns

Deploying a WebSocket-based party game requires specialized infrastructure that maintains persistent connections and supports stateful room management. Standard serverless platforms are unsuitable for the long-lived nature of game sessions.

## WebSocket Hosting Options

Select a hosting provider that supports persistent TCP connections and provides sticky session capability. Avoid serverless functions (Vercel, Netlify) for the WebSocket server as they terminate connections after short intervals.

| Provider | Recommendation | Pros | Cons |
|----------|----------------|------|------|
| Fly.io | Recommended | Native Anycast, built-in WebSocket support, easy scaling. | Complex networking for multi-region. |
| Railway | Good | Simple setup, persistent disks, affordable. | No native Anycast across regions. |
| Render | Good | Managed Redis, reliable WebSocket support. | Scaling costs can increase quickly. |
| AWS ECS/EKS | Advanced | Maximum control, global infrastructure. | High configuration overhead. |

### Why Fly.io for Party Games
Fly.io is particularly effective for party games because its Anycast routing automatically sends players to the nearest available server instance. This minimizes geographic latency, which is critical for real-time interaction. Furthermore, Fly's private networking allows server instances to communicate directly for state synchronization if needed.

### Hosting Requirements
- **Sticky Sessions**: Mandatory for Socket.IO when using multiple instances to ensure clients stay on the same server during the initial handshake.
- **WebSocket Support**: Verify the platform's load balancer does not prematurely close idle TCP connections. Set proxy timeouts to at least 60 seconds.
- **Region Locality**: Deploy as close to the target player base as possible. If targeting a global audience, use a provider that supports multi-region deployments with shared Redis.

## Docker Setup

Containerize the party game server to ensure environment parity between development and production. Use a multi-stage build to minimize the final image size and reduce the attack surface.

### Production Dockerfile Pattern
```dockerfile
# Stage 1: Build
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
# Install all dependencies including devDependencies for build
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Runtime
FROM node:20-slim
WORKDIR /app
ENV NODE_ENV=production
# Only install production dependencies
COPY --from=builder /app/package*.json ./
RUN npm ci --only=production
COPY --from=builder /app/dist ./dist

# Health check endpoint for container orchestrators
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD node dist/scripts/health-check.js || exit 1

EXPOSE 3000
# Run as non-privileged user for security
USER node
CMD ["node", "dist/index.js"]
```

### Local Development Environment
Use Docker Compose to simulate a production-like environment locally, including the game server and a Redis instance for scaling tests.

```yaml
version: '3.8'
services:
  server:
    build: 
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - PORT=3000
      - REDIS_URL=redis://redis:6379
      - NODE_ENV=development
    depends_on:
      - redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: ["redis-server", "--appendonly", "yes"]
```

## Redis Adapter for Scaling

When scaling beyond a single server instance, use a Redis adapter to synchronize events across the cluster. The adapter uses Redis Pub/Sub to broadcast messages to all connected instances.

### Scaling Implementation
Add Redis when the player count exceeds the capacity of a single instance (~5,000-10,000 concurrent players depending on game complexity and broadcast frequency).

```typescript
import { Server } from "socket.io";
import { createAdapter } from "@socket.io/redis-adapter";
import { createClient } from "redis";

async function setupScaling(io: Server) {
  const pubClient = createClient({ 
    url: process.env.REDIS_URL,
    socket: {
      tls: process.env.NODE_ENV === "production",
      rejectUnauthorized: false
    }
  });
  
  const subClient = pubClient.duplicate();

  pubClient.on("error", (err) => console.error("Redis Pub Error", err));
  subClient.on("error", (err) => console.error("Redis Sub Error", err));

  await Promise.all([pubClient.connect(), subClient.connect()]);

  io.adapter(createAdapter(pubClient, subClient));
}
```

**Warning**: Redis stores ephemeral Pub/Sub data for broadcasting. It does not automatically store your game state. You must implement a separate persistent storage strategy if game state needs to survive server restarts.

## Sticky Sessions

Socket.IO requires sticky sessions (session affinity) during the HTTP long-polling handshake phase before upgrading to WebSocket. Without sticky sessions, the client might send a handshake request to Server A and a subsequent connection request to Server B, causing a 400 "Session ID unknown" error.

### The Handshake Problem
1. Client sends HTTP GET to `/socket.io/?transport=polling`.
2. Load balancer routes to Server A. Server A generates a session ID.
3. Client sends HTTP POST to `/socket.io/?transport=polling&sid=XYZ`.
4. Load balancer (without sticky sessions) routes to Server B.
5. Server B does not recognize session XYZ and rejects the connection.

### Nginx Sticky Session Config
If managing your own load balancer, use IP hashing or a dedicated cookie to route traffic consistently.

```nginx
upstream game_servers {
    ip_hash; # Routing based on client IP
    server 127.0.0.1:3000;
    server 127.0.0.1:3001;
}

server {
    listen 80;
    location /socket.io/ {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_pass http://game_servers;
        
        # Essential for WebSocket upgrade
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Prevent proxy from closing idle connections
        proxy_read_timeout 86400;
    }
}
```

## Room Cleanup and Memory

Memory leaks in party games typically stem from abandoned rooms that remain in memory after players have disconnected. Implement an aggressive room cleanup strategy.

### Lifecycle Management Patterns
1. **Empty Room Removal**: Immediately delete a room object and its associated state when the last player leaves or disconnects.
2. **Inactivity Timeout**: Set a timer when a room becomes empty. If no players rejoin within a specific window (e.g., 5 minutes), purge the room.
3. **Stale Session Cleanup**: Regularly scan the room registry for games that have been active longer than a reasonable maximum (e.g., 4 hours) and force terminate them.

### Inactivity Tracker Example
```typescript
class RoomRegistry {
  private rooms = new Map<string, GameRoom>();
  private timeouts = new Map<string, NodeJS.Timeout>();

  removePlayer(roomId: string, playerId: string) {
    const room = this.rooms.get(roomId);
    if (!room) return;

    room.removePlayer(playerId);
    
    if (room.isEmpty()) {
      const timeout = setTimeout(() => {
        this.rooms.delete(roomId);
        this.timeouts.delete(roomId);
        console.log(`Room ${roomId} purged due to inactivity`);
      }, 300000); // 5 minutes
      this.timeouts.set(roomId, timeout);
    }
  }

  onPlayerJoin(roomId: string) {
    const timeout = this.timeouts.get(roomId);
    if (timeout) {
      clearTimeout(timeout);
      this.timeouts.delete(roomId);
    }
  }
}
```

## Environment Configuration

Use environment variables for all environment-specific settings. Validate these variables at server startup to prevent runtime failures.

| Variable | Description | Example |
|----------|-------------|---------|
| PORT | Port the server listens on. | 3000 |
| REDIS_URL | Connection string for scaling adapter. | redis://localhost:6379 |
| CORS_ORIGIN | Allowed frontend URL (comma separated). | https://game.com,http://localhost:5173 |
| NODE_ENV | Running environment. | production |
| ROOM_MAX_CAPACITY | Global limit for players per room. | 8 |
| LOG_LEVEL | Granularity of server logs. | info, debug, warn |
| SESSION_SECRET | Secret for signing session tokens. | long-random-string |

### Configuration Validation with Zod
```typescript
import { z } from "zod";

const envSchema = z.object({
  PORT: z.string().transform(Number).default("3000"),
  REDIS_URL: z.string().url(),
  CORS_ORIGIN: z.string().transform(s => s.split(",")),
  NODE_ENV: z.enum(["development", "production", "test"]),
  LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),
});

export const config = envSchema.parse(process.env);
```

## Health Checks and Monitoring

Implement health check endpoints that verify the internal state of the server and its dependencies.

### Health Check Endpoint Implementation
A healthy server must have a functional WebSocket engine and an active connection to the Redis adapter.

```typescript
app.get("/health", async (req, res) => {
  const isRedisConnected = redisClient.isOpen;
  const activeRooms = io.sockets.adapter.rooms.size;
  const memoryUsage = process.memoryUsage().heapUsed / 1024 / 1024;
  
  if (!isRedisConnected) {
    return res.status(503).json({ status: "unhealthy", reason: "redis_disconnected" });
  }

  res.status(200).json({
    status: "healthy",
    metrics: {
      rooms: activeRooms,
      players: io.engine.clientsCount,
      memoryMB: Math.round(memoryUsage),
      uptime: Math.round(process.uptime())
    }
  });
});
```

### Logging Strategy
Use a structured logger (like Pino or Winston) to record game events. Log these specific actions for easier debugging:
- **Room Creation**: Include room ID and host ID.
- **Join Failures**: Log why a player couldn't join (full, wrong state).
- **Abrupt Disconnects**: Log Socket.IO disconnect reasons (ping timeout, transport close).
- **Game State Transitions**: Log when games move from 'lobby' to 'playing'.

## Production Checklist

Ensure these items are addressed before launching to production.

| Category | Action Item | Priority |
|----------|-------------|----------|
| Security | Configure strict CORS origins for the Socket.IO server. | High |
| Security | Implement rate limiting for room creation and join events. | High |
| Operations | Configure graceful shutdown to notify players before restart. | Medium |
| Operations | Setup centralized logging (Loki, Datadog) for game events. | Medium |
| Logic | Handle room code collisions with a robust generation algorithm. | High |
| Logic | Implement automatic reconnection logic in the game client. | High |
| Performance | Enable gzip/deflate compression for WebSocket packets. | Medium |
| Monitoring | Setup alerts for high memory usage or Redis disconnection. | High |
| Scaling | Test the Redis adapter under load with simulated players. | Medium |

### Graceful Shutdown Implementation
Notify all connected clients and wait for existing game loops to finish before exiting the process.

```typescript
process.on("SIGTERM", async () => {
  console.log("SIGTERM received, shutting down gracefully");
  
  // 1. Stop accepting new connections
  io.engine.close();
  
  // 2. Notify existing players
  io.emit("server_shutdown", { message: "Server is restarting" });
  
  // 3. Close the server after a short delay
  setTimeout(() => {
    io.close(() => {
      console.log("WebSocket server closed");
      process.exit(0);
    });
  }, 5000);
});
```

## Troubleshooting Operations

### Common Production Issues
- **Zombie Rooms**: Rooms that remain active despite having no players. Usually caused by a failure in the `disconnect` handler. Use a periodic cleanup task to prune these.
- **Latency Spikes**: Often caused by large state broadcasts. Optimize by sending deltas instead of full state objects.
- **Connection Drops**: If players drop simultaneously, check the load balancer timeouts or Redis stability.
- **CORS Errors**: Verify that the `CORS_ORIGIN` environment variable exactly matches the frontend URL including the protocol and port.
