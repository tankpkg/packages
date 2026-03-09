# Voice and Audio

Sources: discordgo v0.29.0 voice docs, dgvoice helper library, dca encoding tool, arikawa v3 voice package, Discord voice API reference (2026)

## Voice Support Overview

Discord voice uses a separate UDP connection alongside the WebSocket gateway. The bot joins a voice channel, negotiates an encryption key, and streams Opus-encoded audio frames over UDP.

### Library Voice Capabilities

| Feature | discordgo | arikawa | disgo |
|---|---|---|---|
| Voice protocol | v1 (XSalsa20) | v4 (AES-GCM) | v4 (AES-GCM) |
| Send audio | Yes | Yes | Yes |
| Receive audio | Yes (unofficial) | Yes (unofficial) | Limited |
| Helper libraries | dgvoice, dca | Built-in | Built-in |
| Context support | No | Yes | Yes |

discordgo uses the older v1 voice protocol (XSalsa20). arikawa and disgo implement v4 (AES-GCM). Both work with current Discord infrastructure; v4 is the forward-looking standard.

## discordgo Voice

### Required Intent

Register `IntentGuildVoiceStates` before opening the session. Without it, the gateway does not deliver `VoiceStateUpdate` events and voice channel joins fail silently. This intent is not included in `IntentsAllWithoutPrivileged`, so add it explicitly.

```go
s.Identify.Intents = discordgo.IntentsGuilds |
    discordgo.IntentGuildVoiceStates |
    discordgo.IntentsGuildMessages
```

### VoiceConnection Struct

`*discordgo.VoiceConnection` is the handle returned by `ChannelVoiceJoin`. The two key exported channels are `OpusSend chan []byte` (write Opus frames to play audio) and `OpusRecv chan *Packet` (read incoming Opus frames). `OpusSend` is buffered (capacity 2) — sending faster than real-time causes frames to drop. `OpusRecv` is nil when `deaf=true`.

### Joining a Voice Channel

```go
// mute=false, deaf=true disables receive; set deaf=false to receive audio
vc, err := s.ChannelVoiceJoin(guildID, channelID, false, true)
if err != nil {
    return fmt.Errorf("join voice: %w", err)
}
```

`ChannelVoiceJoin` blocks until the connection is ready. It stores the connection in `s.VoiceConnections[guildID]`, so only one voice connection per guild is possible.

### Leaving a Voice Channel

Call `vc.Disconnect()` to send the leave payload, close the UDP connection, and remove the entry from `s.VoiceConnections`. Defer it immediately after a successful join.

## Sending Audio

### Opus Frame Format

Discord requires Opus at 48,000 Hz, stereo, 20 ms per frame (960 samples per channel). Each value sent to `OpusSend` must be exactly one 20 ms Opus packet.

### Speaking State

Signal speaking state before sending frames and clear it after:

```go
vc.Speaking(true)
// ... send frames ...
vc.Speaking(false)
```

Omitting `Speaking(true)` makes audio inaudible. Omitting `Speaking(false)` leaves the voice indicator active in the Discord UI.

### Direct Opus Send

```go
for _, frame := range opusFrames {
    vc.OpusSend <- frame
}
```

Use this when you already have Opus-encoded data (e.g., from a `.dca` file).

### Using dgvoice Helper

`github.com/bwmarrin/dgvoice` wraps ffmpeg into a convenience function:

```go
stop := make(chan bool)
dgvoice.PlayAudioFile(vc, "audio.mp3", stop)
// send on stop to interrupt playback
```

dgvoice spawns ffmpeg, pipes PCM through an Opus encoder, writes frames to `OpusSend`, and handles `Speaking` state internally.

### Using dca

`github.com/jonas747/dca` provides Discord-optimized encoding and a streaming API. It also reads pre-encoded `.dca` files, skipping encoding and reducing CPU usage:

```go
opts := dca.StdEncodeOptions
opts.RawOutput = true
opts.Bitrate = 96
enc, err := dca.EncodeFile("audio.mp3", opts)
if err != nil { return err }
defer enc.Cleanup()
done := make(chan error)
dca.NewStream(enc, vc, done)
if err := <-done; err != nil && err != io.EOF {
    return fmt.Errorf("stream: %w", err)
}
```

### Playing Audio Files

Combine join, encode, and stream:

```go
func playFile(s *discordgo.Session, guildID, channelID, filePath string) error {
    vc, err := s.ChannelVoiceJoin(guildID, channelID, false, true)
    if err != nil { return fmt.Errorf("join: %w", err) }
    defer vc.Disconnect()
    enc, err := dca.EncodeFile(filePath, dca.StdEncodeOptions)
    if err != nil { return fmt.Errorf("encode: %w", err) }
    defer enc.Cleanup()
    done := make(chan error)
    dca.NewStream(enc, vc, done)
    if err := <-done; err != nil && err != io.EOF { return fmt.Errorf("stream: %w", err) }
    return nil
}
```

### Playing from URL/YouTube

Use yt-dlp to extract a stream URL, then pass it to dca:

```go
out, err := exec.Command("yt-dlp", "-f", "bestaudio", "-g", url).Output()
if err != nil {
    return fmt.Errorf("yt-dlp: %w", err)
}
enc, err := dca.EncodeFile(strings.TrimSpace(string(out)), dca.StdEncodeOptions)
// ... stream as above ...
```

yt-dlp must be installed on the host. The `-g` flag returns the direct stream URL without downloading. ffmpeg (called internally by dca) handles the HTTP stream.

## Receiving Audio

### OpusRecv Channel

When `deaf=false`, incoming audio arrives on `vc.OpusRecv` as `*discordgo.Packet` values. Each packet carries `SSRC` (speaker identifier), `Sequence` (ordering), `Timestamp` (RTP), and `Opus` (raw frame bytes).

```go
go func() {
    for p := range vc.OpusRecv {
        processPacket(p) // p.SSRC, p.Opus, p.Sequence
    }
}()
```

### Mapping SSRC to Users

Discord does not include user IDs in audio packets. Map SSRC values to users via `VoiceSpeakingUpdate` events:

```go
ssrcToUser := make(map[uint32]string)
var mu sync.RWMutex
s.AddHandler(func(vc *discordgo.VoiceConnection, vs *discordgo.VoiceSpeakingUpdate) {
    mu.Lock(); ssrcToUser[uint32(vs.SSRC)] = vs.UserID; mu.Unlock()
})
```

### Recording to File

Write length-prefixed Opus frames to disk:

```go
for p := range vc.OpusRecv {
    binary.Write(f, binary.LittleEndian, int16(len(p.Opus)))
    f.Write(p.Opus)
}
// Decode later: ffmpeg -f s16le -ar 48000 -ac 2 -i recorded.raw output.mp3
```

### Voice Receive Limitations

Voice receive is not officially supported by Discord or discordgo. Key constraints:

- Packets arrive mixed from all speakers; separation requires per-SSRC buffering.
- Silence packets (comfort noise) have `len(p.Opus) == 3`; filter them before decoding.
- Packet loss and reordering are common; use `p.Sequence` to detect gaps.
- Discord may change the voice protocol without notice, breaking receive.

## arikawa Voice

### voice.NewSession Setup

```go
s, _ := state.New("Bot " + token)
vs, err := voice.NewSession(s)
```

arikawa uses v4 voice protocol with AES-GCM encryption.

### JoinChannel with Context

```go
ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()
if err := vs.JoinChannel(ctx, guildID, channelID, false, true); err != nil {
    return fmt.Errorf("join: %w", err)
}
defer vs.Leave(context.Background())
```

Context propagation allows cancellation and timeout on the join handshake — an advantage over discordgo.

### UDP Dialer Configuration

Override the UDP dialer for custom network settings or timeouts:

```go
vs.SetUDPDialer(func(ctx context.Context, network, addr string) (net.Conn, error) {
    return (&net.Dialer{Timeout: 5 * time.Second}).DialContext(ctx, network, addr)
})
```

### Streaming via ffmpeg

```go
ffmpeg := exec.CommandContext(ctx, "ffmpeg", "-i", filePath,
    "-f", "s16le", "-ar", "48000", "-ac", "2", "pipe:1")
stdout, _ := ffmpeg.StdoutPipe()
ffmpeg.Start()

enc, _ := opus.NewEncoder(48000, 2, opus.AppAudio)
buf := make([]int16, 960*2)
for {
    if err := binary.Read(stdout, binary.LittleEndian, buf); err != nil { break }
    frame, _ := enc.Encode(buf, 960, 960*2*2)
    vs.WriteCtx(ctx, frame)
}
```

## Queue Management

### Simple Slice Queue

A mutex-protected slice works for simple bots:

```go
type Queue struct{ mu sync.Mutex; items []string }
func (q *Queue) Add(s string) { q.mu.Lock(); q.items = append(q.items, s); q.mu.Unlock() }
func (q *Queue) Next() (string, bool) {
    q.mu.Lock(); defer q.mu.Unlock()
    if len(q.items) == 0 { return "", false }
    s := q.items[0]; q.items = q.items[1:]; return s, true
}
```

### Channel-Based Queue

A channel-based queue decouples command handlers from the playback goroutine:

```go
type Player struct{ queue chan string; skip, stop chan struct{} }

func (p *Player) Run(vc *discordgo.VoiceConnection) {
    for {
        select {
        case url := <-p.queue: p.play(vc, url)
        case <-p.stop: return
        }
    }
}
```

### Skip, Stop, Pause, Resume

```go
func (p *Player) Skip() { select { case p.skip <- struct{}{}: default: } }
func (p *Player) Stop() { close(p.stop) }

var paused atomic.Bool // Pause/Resume: checked in the send loop

func sendLoop(vc *discordgo.VoiceConnection, frames [][]byte, skip <-chan struct{}) {
    for _, frame := range frames {
        for paused.Load() { time.Sleep(20 * time.Millisecond) }
        select {
        case vc.OpusSend <- frame:
        case <-skip: return
        }
    }
}
```

## Audio Encoding

### Opus Codec Requirements

| Parameter | Value |
|---|---|
| Sample rate | 48,000 Hz |
| Channels | 2 (stereo) |
| Frame size | 960 samples (20 ms) |
| Bitrate | 8–128 kbps (96 kbps recommended) |

### ffmpeg Pipeline (PCM → Opus)

Convert any audio format to raw PCM for Opus encoding: `ffmpeg -i input.mp3 -f s16le -ar 48000 -ac 2 pipe:1`. Flags: `-f s16le` (signed 16-bit PCM), `-ar 48000` (resample), `-ac 2` (stereo), `pipe:1` (stdout for piping).

### gopus for Direct Encoding

`github.com/hraban/opus` wraps libopus (requires `libopus-dev` or `brew install opus`):

```go
enc, _ := opus.NewEncoder(48000, 2, opus.AppAudio)
enc.SetBitrate(96000)
pcm := make([]int16, 960*2) // fill from ffmpeg stdout
buf := make([]byte, 1000)
n, _ := enc.Encode(pcm, buf)
vc.OpusSend <- buf[:n]
```

## Common Voice Bot Patterns

### Auto-Disconnect on Empty Channel

```go
s.AddHandler(func(s *discordgo.Session, vsu *discordgo.VoiceStateUpdate) {
    vc, ok := s.VoiceConnections[vsu.GuildID]
    if !ok { return }
    guild, _ := s.State.Guild(vsu.GuildID)
    count := 0
    for _, vs := range guild.VoiceStates {
        if vs.ChannelID == vc.ChannelID && vs.UserID != s.State.User.ID { count++ }
    }
    if count == 0 { vc.Disconnect() }
})
```

### Volume Control

Apply a gain multiplier to PCM samples before encoding. Clamp to int16 range to prevent overflow. `volume=1.0` is unity gain; `0.5` is half volume:

```go
func applyVolume(pcm []int16, volume float32) {
    for i, s := range pcm {
        v := float32(s) * volume
        if v > 32767 { v = 32767 } else if v < -32768 { v = -32768 }
        pcm[i] = int16(v)
    }
}
```

### Audio Mixing

Sum PCM streams and clamp. Divide by stream count to avoid clipping when mixing more than two sources:

```go
func mixPCM(streams [][]int16) []int16 {
    out := make([]int16, len(streams[0]))
    for i := range out {
        var sum int32
        for _, s := range streams { sum += int32(s[i]) }
        if sum > 32767 { sum = 32767 } else if sum < -32768 { sum = -32768 }
        out[i] = int16(sum)
    }
    return out
}
```

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Sending frames without `Speaking(true)` | Audio is inaudible; Discord drops frames | Call `vc.Speaking(true)` before the first frame |
| Not deferring `vc.Disconnect()` | Voice connection leaks; bot stays in channel | Defer `vc.Disconnect()` immediately after join |
| Sending frames faster than real-time | `OpusSend` buffer fills, frames drop | Pace sends at 20 ms intervals or use dca's stream |
| Ignoring `OpusSend` capacity | Goroutine blocks indefinitely on full channel | Use `select` with a `stop` channel |
| Decoding audio in the send goroutine | CPU spike causes frame timing jitter | Decode ahead or use a separate encoder goroutine |
| Reading `OpusRecv` with `deaf=true` | `OpusRecv` is nil; nil channel blocks forever | Set `deaf=false` when receive is needed |
