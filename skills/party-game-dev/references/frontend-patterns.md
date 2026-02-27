# Frontend Patterns
Sources: Jackbox Games UI analysis, Drawphone, Rocketcrab, Fishbowl frontend implementations

In party game development, the frontend is split into two distinct environments: the shared Host Screen (TV) and the private Player Controller (Mobile). This architecture requires strict synchronization and asymmetric UI design. Unlike traditional apps, party games prioritize low-latency interactions and high-impact visual feedback over complex information density.

## 1. Two-Screen Architecture

Party games utilize a distributed frontend model where the game state is shared across multiple devices with different roles. The central "Host" manages the authoritative visuals, while "Players" provide input through a browser-based controller.

### App Structure Patterns
There are two primary ways to implement this in React:

1. **Role-Based Routing (Single App)**: Use a single React application that branches based on the URL or a session role.
   - Host: `/host/:roomCode`
   - Player: `/play/:roomCode` or `/join`
   - Pros: Shared types, shared socket logic, easier deployment.
   - Cons: Larger bundle size for mobile players if host assets are heavy.

2. **Separate Applications (Recommended for Scale)**: Build two distinct applications.
   - `host-app`: Heavy on animations, high-res assets, no touch support.
   - `player-app`: Extremely lightweight, mobile-first, no heavy assets.

### Role-Based Routing Component Example
```typescript
const GameRouter = () => {
  const { role, roomCode } = useGameSession();

  if (!role) {
    return <LandingScreen />;
  }

  return (
    <Routes>
      <Route 
        path="/host/:roomCode" 
        element={role === 'host' ? <HostContainer /> : <Navigate to="/join" />} 
      />
      <Route 
        path="/play/:roomCode" 
        element={role === 'player' ? <PlayerContainer /> : <Navigate to="/join" />} 
      />
      <Route path="/join" element={<JoinScreen />} />
      <Route path="*" element={<Error404 />} />
    </Routes>
  );
};
```

## 2. Host Screen Design

The Host Screen acts as the central source of truth for all players. It must be designed for visibility from a distance (10-15 feet) and intended for passive viewing until a player interaction occurs.

### Key Design Principles
- **Prominent Room Code**: Display the 4-letter code in a high-contrast box in a corner at all times. Use a mono-spaced font (e.g., JetBrains Mono) to prevent character confusion.
- **Large Typography**: Use a minimum of 32px for body text and 96px+ for headers. Content must be readable even on low-resolution or small TVs.
- **Visual Feedback**: Every player action (joining, submitting) should trigger a visual indicator on the host screen. If a player submits an answer, their avatar on the Host Screen should pulse or change color.

### Host Component Responsibilities
| Component | Purpose | Key UI Elements |
|-----------|---------|-----------------|
| `<HostLobby>` | Initial gathering point | Room code, connected player list, "Start" button hint. |
| `<HostPrompt>` | Displays the current task | Large text question, player response status. |
| `<HostVoting>` | Displays options to vote on | Randomized list of player answers, anonymous labels. |
| `<HostResults>` | Shows the outcome of a round | Winning answer, author reveal, funny animations. |
| `<HostScoreboard>` | Displays current standings | Ranked player list, point delta animations. |
| `<HostAudio>` | Handles background music | Game phase themes, sound effects for votes/joins. |

### Host Layout Pattern
```tsx
const HostLayout = ({ children, roomCode }: { children: React.ReactNode, roomCode: string }) => (
  <div className="h-screen w-screen bg-slate-900 text-white overflow-hidden p-12 flex flex-col font-sans">
    <header className="flex justify-between items-start mb-8 z-10">
      <div className="flex flex-col">
        <h1 className="text-5xl font-black tracking-tighter italic">PARTY GAME</h1>
        <p className="text-slate-400 text-xl">Waiting for players...</p>
      </div>
      <div className="flex flex-col items-end">
        <span className="text-slate-500 text-sm mb-1">JOIN AT PARTY.GAME</span>
        <div className="bg-white text-slate-900 px-8 py-4 rounded-2xl shadow-2xl text-7xl font-mono font-black">
          {roomCode}
        </div>
      </div>
    </header>
    <main className="flex-1 flex flex-col items-center justify-center relative">
      {children}
    </main>
    <footer className="mt-8 flex justify-center gap-4">
      {/* Global connection status icons or audience count */}
    </footer>
  </div>
);
```

## 3. Player Controller Design

The Player Controller is a mobile-first interface optimized for speed and simplicity. It should be a "thin client" that only shows what is necessary for the current task.

### Controller Requirements
- **No Friction**: Players should reach the waiting room in under 10 seconds. Minimize inputs; use name + room code only.
- **Touch Optimization**: All interactive elements must be at least 48px tall. Use large, chunky buttons with feedback on touch (`:active` scale).
- **State Awareness**: The controller must always know the current game phase to show the correct inputs. It should show a "Look at the TV" message when no action is required.

### Player Component Responsibilities
| Component | Purpose | Key UI Elements |
|-----------|---------|-----------------|
| `<JoinScreen>` | Entry point | Room code input, name input, "Join" button. |
| `<WaitingRoom>` | Lobby state | "You're in!" message, player name display. |
| `<AnswerInput>` | Gameplay input | Textarea or drawing canvas, "Submit" button. |
| `<VotePicker>` | Decision phase | Vertical list of large buttons for each option. |
| `<PlayerResults>` | Feedback phase | Points earned, personal rank, "Play Again" button. |
| `<DisconnectedUI>`| Error handling | Auto-reconnect message, manual refresh button. |

### Mobile Input Pattern
```tsx
const AnswerInput = ({ prompt, onSubmit }: { prompt: string, onSubmit: (val: string) => void }) => {
  const [text, setText] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);

  if (isSubmitted) return <WaitingForOthers />;

  return (
    <div className="flex flex-col h-full p-6 gap-6 bg-slate-50">
      <div className="text-center">
        <p className="text-slate-500 uppercase text-xs font-bold tracking-widest">Question</p>
        <h2 className="text-2xl font-black text-slate-800 leading-tight">{prompt}</h2>
      </div>
      <textarea 
        autoFocus
        className="flex-1 p-4 text-xl border-4 border-slate-200 rounded-2xl focus:border-blue-500 outline-none"
        placeholder="Type your funny answer..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button 
        disabled={text.trim().length === 0}
        onClick={() => { setIsSubmitted(true); onSubmit(text); }}
        className="h-20 bg-blue-600 text-white rounded-3xl font-black text-2xl shadow-lg active:translate-y-1 transition-all disabled:bg-slate-300"
      >
        SEND
      </button>
    </div>
  );
};
```

## 4. Socket.IO React Integration

Effective real-time communication requires a centralized Socket context to prevent duplicate listeners and ensure state consistency across components.

### Socket Context Provider
Manage the socket instance at the top level of the app. Implement heartbeat monitoring to detect silent disconnects.

```typescript
const SocketContext = createContext<Socket | null>(null);

export const SocketProvider = ({ children }: { children: React.ReactNode }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const s = io(process.env.REACT_APP_SERVER_URL, {
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      timeout: 20000,
    });

    s.on('connect', () => setIsConnected(true));
    s.on('disconnect', () => setIsConnected(false));
    
    setSocket(s);
    return () => { s.close(); };
  }, []);

  return (
    <SocketContext.Provider value={socket}>
      {!isConnected && <ReconnectingOverlay />}
      {children}
    </SocketContext.Provider>
  );
};
```

### useSocket Hook Pattern
Encapsulate event handling to ensure clean removal of listeners. This prevents memory leaks and "state ghosting" where old callbacks are still active.

```typescript
export const useSocketEvent = <T>(event: string, callback: (data: T) => void) => {
  const socket = useContext(SocketContext);

  useEffect(() => {
    if (!socket) return;
    const wrappedCallback = (data: T) => callback(data);
    socket.on(event, wrappedCallback);
    return () => { socket.off(event, wrappedCallback); };
  }, [socket, event, callback]);
};
```

## 5. Game State Rendering

The frontend should be a pure function of the `gameState` emitted by the server. Avoid storing local game logic state.

### Phase-Based Rendering
Use a switch statement to toggle between game phases. Ensure each phase has its own layout to optimize use of screen real estate.

```tsx
const HostGameLoop = () => {
  const { phase, gameState, lastPhase } = useGameState();

  // Use AnimatePresence for smooth transitions between phases
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={phase}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        className="w-full h-full"
      >
        {(() => {
          switch (phase) {
            case "LOBBY": return <HostLobby players={gameState.players} />;
            case "PROMPT": return <HostPrompt question={gameState.currentQuestion} />;
            case "VOTING": return <HostVoting options={gameState.options} />;
            case "RESULTS": return <HostResults winner={gameState.winner} />;
            case "SCOREBOARD": return <HostScoreboard scores={gameState.scores} />;
            default: return <LoadingScreen />;
          }
        })()}
      </motion.div>
    </AnimatePresence>
  );
};
```

### Handling Phase Transitions
Transitions should never be instantaneous. When the server moves from `PROMPT` to `VOTING`, the client should:
1. Show a "Time's Up!" message for 2 seconds.
2. Animate the current content out.
3. Fetch any needed assets for the next phase.
4. Animate the next phase in.

## 6. Real-Time UI Updates

Animations and optimistic updates prevent the UI from feeling sluggish, which is critical when players are interacting with a shared screen.

### Optimistic Player Feedback
When a player submits an answer, the controller should immediately transition to a "Waiting" state, even before the server acknowledges. If the server rejects the input (e.g., profanity filter), the client should roll back to the input state and show an error.

### Server-Driven Animations
The server can emit "Visual Events" alongside state updates. For example, a `PLAYER_VOTED` event can trigger a "ding" sound and a bounce animation on the player's icon on the host screen without changing the actual game state logic.

### Synchronized Timers
Do not run independent timers on the client. The server should be the master clock. 
- **Pattern**: Server emits `timerStarted` event with `{ duration: 60, expiresAt: 1710000000 }`.
- **Client**: Calculates `Math.max(0, expiresAt - Date.now())` every 100ms.
- This ensures that even with network jitter, everyone sees the timer hit zero simultaneously.

```tsx
const SynchronizedTimer = ({ expiresAt }: { expiresAt: number }) => {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const tick = () => {
      const remaining = Math.ceil((expiresAt - Date.now()) / 1000);
      setSeconds(Math.max(0, remaining));
    };
    const interval = setInterval(tick, 200);
    tick();
    return () => clearInterval(interval);
  }, [expiresAt]);

  return (
    <div className={`text-6xl font-black ${seconds < 5 ? 'text-red-500 scale-110' : ''} transition-all`}>
      {seconds}
    </div>
  );
};
```

## 7. Responsive and Accessibility

### Screen Target Specifications
- **Host (1080p)**: Optimize for 1920x1080. Avoid relying on hover states. Ensure that interactive elements (like the "Start Game" button) are clearly marked and usable via a mouse or remote if necessary.
- **Player (Mobile)**: Target the smallest common screen (320px). Use fluid typography (`clamp()`) to ensure headers don't wrap awkwardly on small devices.

### Accessibility for TV Displays
- **Color Contrast**: Projects often wash out colors. Use a contrast ratio of at least 7:1 for text.
- **Motion Sensitivity**: Provide a way to disable heavy screen shakes or rapid flashes for players with vestibular disorders.
- **Subtitles**: If your game uses voice-over narration, include a persistent subtitle area on the host screen.

### Mobile UX Best Practices
- **Prevent Refresh**: Use `window.onbeforeunload` to warn players before they accidentally close the browser tab.
- **No Zoom**: Use meta tags to prevent accidental pinch-to-zoom which breaks layouts.
- **Keep Awake**: Use the Wake Lock API if available to prevent the phone from sleeping during long rounds.

## 8. Component Library Recommendations

### Styling Stack
- **Tailwind CSS**: Use utility classes for rapid layout iteration. Use the `container-queries` plugin to create components that look good on both the Host sidebars and Player fullscreens.
- **Design Tokens**: Standardize colors in `tailwind.config.js`. For example, `brand-primary`, `brand-secondary`, and a set of `player-colors` (e.g., `p1-blue`, `p2-red`).

### Motion Stack
- **Framer Motion**: Essential for the "Jackbox feel." Use `layoutId` to animate elements between components (e.g., a player's answer card moving from the prompt screen to the voting screen).

```tsx
<motion.div
  layoutId={`answer-${answer.id}`}
  className="bg-white p-6 rounded-xl shadow-lg text-slate-900"
>
  {answer.text}
</motion.div>
```

### Audio Stack
- **Howler.js**: Robust audio management for cross-browser support. Use it to handle spatial audio if the Host screen has a surround sound setup. Preload assets during the lobby phase to avoid lag during gameplay.
