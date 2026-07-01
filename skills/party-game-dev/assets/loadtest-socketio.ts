// Load test harness for Socket.IO party game servers.
// Spawns N virtual players that join rooms, submit answers, and vote.
// Run: npx tsx loadtest-socketio.ts --url http://localhost:3001 --rooms 10 --players-per-room 8
//
// Measures: connection time, join latency, event round-trip, memory (server-side via /health).
// NOT a replacement for k6 or Artillery — use this for quick smoke tests during development.

import { io, Socket } from "socket.io-client";

interface LoadTestConfig {
  serverUrl: string;
  totalRooms: number;
  playersPerRoom: number;
  submitDelayMs: number;
  voteDelayMs: number;
}

interface LatencyBucket {
  event: string;
  startMs: number;
  endMs: number;
  durationMs: number;
}

const latencies: LatencyBucket[] = [];

function recordLatency(event: string, startMs: number): void {
  const endMs = Date.now();
  latencies.push({ event, startMs, endMs, durationMs: endMs - startMs });
}

function generateRoomCode(): string {
  const chars = "ABCDEFGHJKLM" + "NPQRSTUVWXYZ23456789";
  return Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join("");
}

async function connectPlayer(
  serverUrl: string,
  roomCode: string,
  playerName: string
): Promise<Socket> {
  return new Promise((resolve, reject) => {
    const startMs = Date.now();
    const socket = io(serverUrl, { transports: ["websocket"], autoConnect: true });

    const timeout = setTimeout(() => {
      socket.disconnect();
      reject(new Error(`Connection timeout for ${playerName}`));
    }, 10_000);

    socket.on("connect", () => {
      recordLatency("connect", startMs);
      clearTimeout(timeout);

      const joinStart = Date.now();
      socket.emit("join-room", { roomCode, playerName });

      socket.once("room:joined", () => {
        recordLatency("join-room", joinStart);
        resolve(socket);
      });

      socket.once("error", (err: { message: string }) => {
        clearTimeout(timeout);
        reject(new Error(`Join error for ${playerName}: ${err.message}`));
      });
    });

    socket.on("connect_error", (err) => {
      clearTimeout(timeout);
      reject(err);
    });
  });
}

function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

async function simulateRoom(config: LoadTestConfig, roomIndex: number): Promise<void> {
  const roomCode = generateRoomCode();
  const sockets: Socket[] = [];

  try {
    for (let i = 0; i < config.playersPerRoom; i++) {
      const name = `Bot-${roomIndex}-${i}`;
      const socket = await connectPlayer(config.serverUrl, roomCode, name);
      sockets.push(socket);
    }

    console.log(`Room ${roomCode}: ${sockets.length} players connected`);

    // Wait for game to start (VIP starts it, or auto-start)
    await delay(1000);

    // Simulate submit phase
    for (const socket of sockets) {
      await delay(config.submitDelayMs * Math.random());
      const startMs = Date.now();
      socket.emit("submit-answer", { text: `Answer from ${socket.id}` });
      socket.once("ack", () => recordLatency("submit-answer", startMs));
    }

    // Simulate vote phase
    await delay(2000);
    for (const socket of sockets) {
      await delay(config.voteDelayMs * Math.random());
      const startMs = Date.now();
      socket.emit("cast-vote", { targetPlayerId: sockets[0].id });
      socket.once("ack", () => recordLatency("cast-vote", startMs));
    }

    await delay(3000);
  } finally {
    for (const s of sockets) s.disconnect();
  }
}

function printReport(): void {
  const grouped = new Map<string, number[]>();
  for (const bucket of latencies) {
    const arr = grouped.get(bucket.event) ?? [];
    arr.push(bucket.durationMs);
    grouped.set(bucket.event, arr);
  }

  console.log("\n--- Load Test Report ---");
  console.log(`Total events: ${latencies.length}`);

  for (const [event, durations] of grouped) {
    durations.sort((a, b) => a - b);
    const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
    const p50 = durations[Math.floor(durations.length * 0.5)];
    const p95 = durations[Math.floor(durations.length * 0.95)];
    const p99 = durations[Math.floor(durations.length * 0.99)];
    console.log(
      `  ${event}: count=${durations.length} avg=${avg.toFixed(0)}ms p50=${p50}ms p95=${p95}ms p99=${p99}ms`
    );
  }
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const getArg = (name: string, fallback: string): string => {
    const idx = args.indexOf(`--${name}`);
    return idx >= 0 && args[idx + 1] ? args[idx + 1] : fallback;
  };

  const config: LoadTestConfig = {
    serverUrl: getArg("url", "http://localhost:3001"),
    totalRooms: parseInt(getArg("rooms", "5"), 10),
    playersPerRoom: parseInt(getArg("players-per-room", "8"), 10),
    submitDelayMs: parseInt(getArg("submit-delay", "200"), 10),
    voteDelayMs: parseInt(getArg("vote-delay", "150"), 10),
  };

  console.log("Load test config:", config);
  console.log(`Spawning ${config.totalRooms * config.playersPerRoom} total connections...\n`);

  const roomPromises = Array.from({ length: config.totalRooms }, (_, i) =>
    simulateRoom(config, i).catch((err) => console.error(`Room ${i} failed:`, err.message))
  );

  await Promise.all(roomPromises);
  printReport();
}

main().catch(console.error);
