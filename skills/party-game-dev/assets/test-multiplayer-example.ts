#!/usr/bin/env npx tsx
/**
 * Party Game Multiplayer Test Harness
 *
 * Spawns N Socket.IO clients to simulate a complete game round.
 * Usage: npx tsx scripts/test-multiplayer.ts [--players 4] [--url http://localhost:3000]
 *
 * What it tests:
 *   1. Room creation (first player becomes host)
 *   2. Player joining (remaining players join via room code)
 *   3. Game start (host triggers)
 *   4. Answer submission (each player submits)
 *   5. Voting (each player votes)
 *   6. Score verification (scores received by all)
 *
 * Requirements:
 *   npm install socket.io-client
 *   Game server running at the specified URL
 */

import { io, Socket } from "socket.io-client";

const args = process.argv.slice(2);
const PLAYER_COUNT = parseInt(
  args.find((_, i) => args[i - 1] === "--players") ?? "4",
  10
);
const SERVER_URL =
  args.find((_, i) => args[i - 1] === "--url") ?? "http://localhost:3000";
const TIMEOUT_MS = 15_000;

interface Player {
  name: string;
  socket: Socket;
  roomCode?: string;
  scores?: Record<string, number>;
}

function createPlayer(name: string): Player {
  const socket = io(SERVER_URL, {
    multiplex: false, // CRITICAL: each player gets an independent connection
    forceNew: true,
    transports: ["websocket"],
    autoConnect: false,
  });
  return { name, socket };
}

function waitForEvent<T = unknown>(
  socket: Socket,
  event: string,
  timeoutMs = TIMEOUT_MS
): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error(`Timeout waiting for '${event}' (${timeoutMs}ms)`)),
      timeoutMs
    );
    socket.once(event, (data: T) => {
      clearTimeout(timer);
      resolve(data);
    });
  });
}

function log(player: Player, msg: string): void {
  const ts = new Date().toISOString().slice(11, 23);
  console.log(`  [${ts}] ${player.name}: ${msg}`);
}

async function connectAll(players: Player[]): Promise<void> {
  console.log(`\n--- Connecting ${players.length} players to ${SERVER_URL} ---`);
  await Promise.all(
    players.map(
      (p) =>
        new Promise<void>((resolve, reject) => {
          p.socket.connect();
          p.socket.once("connect", () => {
            log(p, `Connected (id: ${p.socket.id})`);
            resolve();
          });
          p.socket.once("connect_error", (err) => {
            reject(new Error(`${p.name} connection failed: ${err.message}`));
          });
          setTimeout(() => reject(new Error(`${p.name} connection timeout`)), TIMEOUT_MS);
        })
    )
  );
}

async function createRoom(host: Player): Promise<string> {
  console.log("\n--- Creating Room ---");
  host.socket.emit("createRoom", { playerName: host.name });
  const data = await waitForEvent<{ roomCode: string }>(host.socket, "roomCreated");
  host.roomCode = data.roomCode;
  log(host, `Room created: ${data.roomCode}`);
  return data.roomCode;
}

async function joinRoom(players: Player[], roomCode: string): Promise<void> {
  console.log("\n--- Players Joining ---");
  for (const player of players) {
    player.socket.emit("joinRoom", { roomCode, playerName: player.name });
    await waitForEvent(player.socket, "joinedRoom");
    player.roomCode = roomCode;
    log(player, `Joined room ${roomCode}`);
  }
}

async function startGame(host: Player, allPlayers: Player[]): Promise<void> {
  console.log("\n--- Starting Game ---");
  const gameStartPromises = allPlayers.map((p) =>
    waitForEvent(p.socket, "gameStarted")
  );
  host.socket.emit("startGame", { roomCode: host.roomCode });
  await Promise.all(gameStartPromises);
  console.log("  All players received gameStarted");
}

async function submitAnswers(players: Player[]): Promise<void> {
  console.log("\n--- Submitting Answers ---");
  const answers = [
    "A rubber duck with a PhD",
    "My neighbor's WiFi password",
    "Three raccoons in a trenchcoat",
    "The meaning of life (it's 42)",
    "A strongly-worded letter",
    "Professional nap consultant",
    "Infinite breadsticks",
    "The last unicorn",
  ];

  await Promise.all(
    players.map(async (p, i) => {
      const answer = answers[i % answers.length];
      p.socket.emit("submitAnswer", {
        roomCode: p.roomCode,
        answer,
      });
      await waitForEvent(p.socket, "answerAccepted");
      log(p, `Submitted: "${answer}"`);
    })
  );
}

async function votePhase(players: Player[]): Promise<void> {
  console.log("\n--- Voting Phase ---");
  await Promise.all(
    players.map((p) => waitForEvent(p.socket, "votingStarted"))
  );
  console.log("  All players received votingStarted");

  await Promise.all(
    players.map(async (p, i) => {
      const voteForNextPlayer = (i + 1) % players.length;
      p.socket.emit("vote", {
        roomCode: p.roomCode,
        voteIndex: voteForNextPlayer,
      });
      await waitForEvent(p.socket, "voteAccepted");
      log(p, `Voted for answer #${voteForNextPlayer}`);
    })
  );
}

async function checkResults(players: Player[]): Promise<void> {
  console.log("\n--- Checking Results ---");
  const results = await Promise.all(
    players.map(async (p) => {
      const data = await waitForEvent<{ scores: Record<string, number> }>(
        p.socket,
        "roundResults"
      );
      p.scores = data.scores;
      return data;
    })
  );

  const firstScores = JSON.stringify(results[0].scores);
  const allMatch = results.every(
    (r) => JSON.stringify(r.scores) === firstScores
  );

  if (allMatch) {
    console.log("  All players received consistent scores");
    console.log("  Scores:", results[0].scores);
  } else {
    console.error("  ERROR: Score mismatch between players!");
    for (let i = 0; i < results.length; i++) {
      console.error(`    ${players[i].name}:`, results[i].scores);
    }
  }
}

function disconnectAll(players: Player[]): void {
  console.log("\n--- Disconnecting ---");
  players.forEach((p) => {
    p.socket.disconnect();
    log(p, "Disconnected");
  });
}

async function main(): Promise<void> {
  console.log(`\nParty Game Multiplayer Test`);
  console.log(`  Server: ${SERVER_URL}`);
  console.log(`  Players: ${PLAYER_COUNT}`);

  const players = Array.from({ length: PLAYER_COUNT }, (_, i) =>
    createPlayer(`Player${i + 1}`)
  );
  const [host, ...others] = players;

  try {
    await connectAll(players);
    const roomCode = await createRoom(host);
    await joinRoom(others, roomCode);
    await startGame(host, players);
    await submitAnswers(players);
    await votePhase(players);
    await checkResults(players);

    console.log("\n=== ALL TESTS PASSED ===\n");
  } catch (err) {
    console.error("\n=== TEST FAILED ===");
    console.error((err as Error).message);
    process.exitCode = 1;
  } finally {
    disconnectAll(players);
  }
}

main();
