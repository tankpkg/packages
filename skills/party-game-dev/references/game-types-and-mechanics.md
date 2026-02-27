# Game Types and Mechanics
Sources: Jackbox Games (Quiplash, Drawful, Fibbage, You Don't Know Jack), Drawphone, Longwave, Fishbowl game analysis

This document outlines the core archetypes and mechanics used in modern party games. Each blueprint includes data models, phase flows, and scoring logic to enable implementation from a common design foundation.

## 1. Prompt-Response Games (Quiplash Blueprint)

Prompt-response games rely on subjective creativity where players receive prompts and submit text-based answers for others to judge.

### Data Model

```typescript
interface Prompt {
  id: string;
  text: string; // e.g., "The worst thing to find in your sandwich."
  category?: string;
  isNsfw: boolean;
}

interface Answer {
  id: string;
  promptId: string;
  playerId: string;
  text: string;
  timestamp: number;
}

interface Vote {
  voterId: string;
  targetAnswerId: string;
  timestamp: number;
}

interface PromptMatchup {
  promptId: string;
  answers: [Answer, Answer]; // Two players answer the same prompt
  votes: Vote[];
  winnerId?: string;
}

interface PromptRound {
  matchups: PromptMatchup[];
  currentMatchupIndex: number;
  totalMatchups: number;
}
```

### Phase Flow

1.  **Distribution Phase**: The host selects prompts from a pool. To ensure safety and anonymity, each prompt is sent to exactly two players. Each player typically receives two different prompts.
2.  **Submission Phase**: Players write their responses on their private devices. A timer (60s) enforces pressure.
3.  **Reveal Phase**: The host displays a prompt on the main screen alongside the two anonymous answers.
4.  **Voting Phase**: All players (except the two who answered) and the audience vote for their favorite answer on their devices.
5.  **Results Phase**: The authors of the answers are revealed, and points are awarded based on the vote percentage.

### Scoring Rules

-   **Percentage-Based**: Points are awarded relative to the percentage of the total vote received (e.g., 60% of votes = 600 points).
-   **Quiplash/Unanimous Bonus**: If a player receives 100% of the votes, they receive a "Quiplash" bonus (e.g., 2x points).
-   **Streak Multiplier**: Winning consecutive prompt matchups increases the base point value for the player.

---

## 2. Drawing Games (Drawful/Drawphone Blueprint)

Drawing games transition from text to visual media, often incorporating a "telephone" mechanic where prompts mutate through interpretations.

### Data Model

```typescript
interface Point {
  x: number;
  y: number;
}

interface Stroke {
  points: Point[];
  color: string;
  width: number;
}

interface Drawing {
  playerId: string;
  promptId: string;
  strokes: Stroke[]; // Canvas data format
  thumbnail?: string; // Base64 preview
}

interface ChainLink {
  type: 'word' | 'drawing';
  playerId: string;
  content: string | Stroke[];
}

interface DrawingChain {
  id: string;
  originalPlayerId: string;
  links: ChainLink[];
}
```

### Phase Flow (Telephone Chain)

1.  **Initial Word**: Every player is given or writes a secret starting word/phrase.
2.  **Drawing Link**: Player A passes their word to Player B. Player B must draw what they read.
3.  **Interpretation Link**: Player B passes their drawing to Player C. Player C must guess the original word based ONLY on the drawing.
4.  **Chain Continuation**: This continues until the chain returns to the start or a turn limit is reached.
5.  **Gallery Reveal**: The host shows the entire chain link-by-link, highlighting where the interpretation diverged.

### Performance Optimization: Stroke Batching

To avoid flooding the WebSocket with every mouse movement, batch stroke points and send them at a fixed interval (e.g., 100ms).

```typescript
interface StrokeUpdate {
  roomId: string;
  playerId: string;
  currentStroke: Stroke;
  isComplete: boolean;
}
```

---

## 3. Trivia and Quiz Games (YDKJ Blueprint)

Trivia games emphasize objective knowledge, speed, and deception.

### Data Model

```typescript
interface TriviaQuestion {
  id: string;
  text: string;
  type: 'multiple-choice' | 'free-text';
  options?: string[]; // For multiple choice
  correctAnswer: string;
  metadata: {
    value: number;
    difficulty: number;
  };
}

interface PlayerResponse {
  playerId: string;
  questionId: string;
  answer: string;
  timeElapsed: number; // For speed bonuses
  isCorrect: boolean;
}
```

### Speed Bonuses and Streak Multipliers

-   **Time-Sensitive Scoring**: `Score = BaseValue * (1 - (TimeTaken / TimeLimit))`. This encourages rapid answers.
-   **Streak Multipliers**: Maintain a `streakCount` in the player state.
    -   3 correct: 1.5x points.
    -   5 correct: 2.0x points.
-   **Lie-Detection (Fibbage Pattern)**: Players submit believable "lies" to fool others.
    -   Points for finding the truth.
    -   Bonus for every player who picks your lie.

---

## 4. Word and Association Games (Wavelength Blueprint)

These games focus on spectrums and relative accuracy within a team or group.

### Data Model

```typescript
interface SpectrumCard {
  left: string;  // e.g., "Useless"
  right: string; // e.g., "Useful"
}

interface SpectrumGuess {
  playerId: string;
  value: number; // 0.0 to 100.0 (left to right)
  targetValue: number; // The hidden "bullseye"
}
```

### Accuracy Scoring (Spectrum)

Scoring is based on proximity to the target value:
-   **Bullseye (Within 2 units)**: 4 points.
-   **Close (Within 5 units)**: 3 points.
-   **Neighborhood (Within 10 units)**: 2 points.
-   **Opposite Team Bonus**: The opposing team can earn 1 point by guessing if the actual target is to the left or right of the active team's guess.

---

## 5. Voting and Judging Systems

The selection of a winner can be handled through different social structures depending on the desired game "feel."

### Comparison Table

| System | Description | Best For | Pros | Cons |
| :--- | :--- | :--- | :--- | :--- |
| **Audience Voting** | Everyone (including non-players) votes on all options. | Quiplash, Trivia | High engagement, fair. | Can be slow if many options. |
| **Judge Rotation** | One player (the Judge) picks the winner from the group. | Cards Against Humanity | Personal bias adds humor. | Judge doesn't play that turn. |
| **Peer Scoring** | Every player rates every answer (e.g., 1-10 stars). | Talent Shows, Art | Granular feedback. | Highest time commitment. |

### Implementation Patterns

-   **Majority Winner**: The answer with `Math.max(...votes)` wins the round.
-   **Weighted Voting**: `(PlayerVotes * 1.0) + (AudienceVotes * 0.5)` allows the "crowd" to influence without dominating.
-   **Judge Picks**: A single player is assigned the `isJudge` flag for the round. The UI restricts voting to only that player.

---

## 6. Scoring Systems

Scoring must be calculated by the host (authoritative) to prevent client-side manipulation.

### Formula Patterns

1.  **Base Score**: `POINTS_PER_VOTE * VoteCount`
2.  **Speed Multiplier**: `BaseScore * (1 + (RemainingTime / TotalTime))`
3.  **Streak Multiplier**: `BaseScore * (1 + (ConsecutiveWins * 0.1))`
4.  **Audience Bonus**: `BaseScore + (AudienceVoteCount * AudienceMultiplier)`

### Leaderboard Data Model

```typescript
interface LeaderboardEntry {
  playerId: string;
  name: string;
  currentScore: number;
  lastIncrease: number;
  rank: number;
  isWinning: boolean;
}

interface GameLeaderboard {
  entries: LeaderboardEntry[];
  totalRounds: number;
  isFinal: boolean;
}
```

---

## 7. Content and Prompt Management

Party games live or die by the quality and variety of their content.

### Prompt Pools (JSON Format)

Prompts should be stored in structured JSON files separated by category or language.

```json
[
  {
    "id": "q-001",
    "text": "The worst thing to hear during a surgery.",
    "tags": ["standard", "surgery"],
    "minPlayers": 3
  },
  {
    "id": "q-002",
    "text": "What does the 'B' in 'FBI' actually stand for?",
    "tags": ["absurd"],
    "minPlayers": 3
  }
]
```

### User-Generated Content (UGC)

-   **Custom Packs**: Allow players to upload their own JSON files for private rooms.
-   **Content Safety**: Implement "Room Filters" (Family Friendly vs. Edgy) and allow the host to "Veto" or kick players/answers from the results screen.
-   **Randomization Logic**: Use a "Shuffle without Repeats" algorithm. Maintain a `usedPromptIds` set in the game session and re-seed the pool only when exhausted.

---

## 8. Asymmetric UI Patterns

In a host-player model, the TV and the Phone serve fundamentally different purposes.

### The TV (Host) UI
-   **Visual Spectacle**: High-quality animations, sounds, and global timers.
-   **Information Hub**: Displays common prompts, leaderboard, and voting results.
-   **Atmosphere**: Background music and voice-over (if applicable).

### The Phone (Player) UI
-   **Control Surface**: Minimalistic buttons, text inputs, and drawing pads.
-   **Personal Information**: Secret prompts, private vote buttons, and individual score updates.
-   **Engagement**: Haptic feedback on submission and low-latency response.

---

## 9. Audience and Spectator Mechanics

Modern party games support an unlimited number of audience members who can influence the game without occupying a player slot.

### Audience Data Model

```typescript
interface AudienceMember {
  id: string;
  joinedAt: number;
  lastVote?: string;
}

interface AudienceInfluence {
  totalVotes: number;
  voteDistribution: Record<string, number>; // answerId -> count
}
```

### Audience vs Player Roles

-   **Players (1-8)**: High-priority state sync. Full interactivity. Can win the game.
-   **Audience (Unlimited)**: Low-priority state sync. Limited interactivity (mostly voting). Cannot win the game but can influence scores.

---

## 10. Room and Session Management

Robust room management is critical for the "pick up and play" nature of party games.

### Room Code Generation

Codes should be short, alphanumeric, and uppercase for easy entry on mobile devices.

```typescript
function generateRoomCode(length: number = 4): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}
```

### Disconnect and Reconnection Logic

Players should be able to reconnect using a unique `userId` or `deviceId` stored in local storage.

1.  **Disconnect**: Mark the player as `isConnected: false` in the game state. Keep their score and submissions intact.
2.  **Reconnection**: When a player joins with a matching `userId`, re-map their socket and set `isConnected: true`.
3.  **Late Joining**: If the game has already started, a late-joiner should be added as an audience member until the next lobby phase.

---

## 11. Minimum Viable Game Checklist

Every party game, regardless of mechanic, requires these structural components to function:

1.  **Lobby**: Player joining, name entry, avatar selection, and "Ready Up" state.
2.  **Instruction Screen**: Brief explanation of the current round's rules.
3.  **Global Timer**: A synchronized countdown shown on both the host and player devices.
4.  **Submission Feedback**: Visual confirmation on the phone that the answer was received.
5.  **Reveal Transition**: Dramatic animations or sounds when showing results.
6.  **Leaderboard**: Intermediate score updates between rounds.
7.  **Results/Awards**: Final podium and highlight reel of the best moments.
8.  **Play Again Flow**: Option to restart with the same group or change game settings.

### Game State Interface

```typescript
interface GameState {
  roomCode: string;
  phase: 'LOBBY' | 'INSTRUCTIONS' | 'INPUT' | 'VOTING' | 'RESULTS' | 'FINAL';
  players: Player[];
  timer: {
    remaining: number;
    total: number;
  };
  roundData: any; // Context-specific data
}
```

By following these blueprints, developers can ensure that the core loops of their party games are robust, engaging, and technically sound while allowing for creative variation in theme and presentation.
