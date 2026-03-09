# Project Setup and Structure

Sources: discordgo examples, YAGPDB architecture, CJ bot, ops-bot-iii patterns, production bot analysis (2026)

## Project Structure Patterns

### Simple Bot (single main.go + packages)

Use for bots with fewer than ~10 commands and no external services.

```
mybot/
├── main.go          # session setup, graceful shutdown
├── commands.go      # command definitions and handlers
├── handlers.go      # event handlers (Ready, GuildCreate, etc.)
├── config.go        # config struct and loader
├── go.mod
└── .env
```

All code lives in `package main`. `main.go` owns the session lifecycle. `commands.go` holds the command map and handler functions.

### Production Bot (cmd/internal layout)

Use when the bot has a database, multiple subsystems, or multiple developers.

```
mybot/
├── cmd/
│   └── bot/
│       └── main.go          # thin entry point: load config, wire deps, run
├── internal/
│   ├── bot/
│   │   └── bot.go           # Bot struct, Start/Stop, handler registration
│   ├── commands/
│   │   ├── general.go
│   │   ├── moderation.go
│   │   └── registry.go      # command map, bulk registration
│   ├── handlers/
│   │   └── events.go
│   ├── database/
│   │   └── db.go
│   └── config/
│       └── config.go
├── migrations/
├── go.mod
└── .env
```

`cmd/bot/main.go` is intentionally thin — load config, construct dependencies, call `bot.Start()`. The `internal/` boundary prevents external packages from importing bot internals.

### Plugin-Based Bot (YAGPDB-style)

Use for large bots where features must be independently toggled. Each plugin implements a `Plugin` interface and registers itself via `init()`. `main.go` imports plugin packages for side effects only.

```
mybot/
├── cmd/bot/main.go          # imports plugins to trigger init()
├── bot/bot.go               # core session, plugin registry
├── common/plugin.go         # Plugin interface: BotInitHandler, BotStopperHandler
└── plugins/
    ├── moderation/
    ├── music/
    └── logging/
```

Prefer `cmd/internal` until you have 5+ independent feature areas.

## main.go Bootstrapping

### Minimal Example (complete working bot in ~40 lines)

```go
package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/bwmarrin/discordgo"
)

func main() {
	token := os.Getenv("DISCORD_TOKEN")
	if token == "" {
		fmt.Fprintln(os.Stderr, "DISCORD_TOKEN not set")
		os.Exit(1)
	}

	s, err := discordgo.New("Bot " + token)
	if err != nil {
		fmt.Fprintf(os.Stderr, "creating session: %v\n", err)
		os.Exit(1)
	}

	s.Identify.Intents = discordgo.IntentsGuilds | discordgo.IntentsGuildMessages

	s.AddHandler(func(s *discordgo.Session, r *discordgo.Ready) {
		fmt.Printf("Logged in as %s\n", r.User.String())
	})

	s.AddHandler(func(s *discordgo.Session, i *discordgo.InteractionCreate) {
		if i.ApplicationCommandData().Name == "ping" {
			s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
				Type: discordgo.InteractionResponseChannelMessageWithSource,
				Data: &discordgo.InteractionResponseData{Content: "Pong!"},
			})
		}
	})

	if err = s.Open(); err != nil {
		fmt.Fprintf(os.Stderr, "opening connection: %v\n", err)
		os.Exit(1)
	}
	defer s.Close()

	s.ApplicationCommandCreate(s.State.User.ID, "", &discordgo.ApplicationCommand{
		Name: "ping", Description: "Responds with Pong!",
	})

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop
}
```

Note the `"Bot "` prefix on the token — discordgo requires it. Call `s.Open()` before registering commands so `s.State.User.ID` is populated.

### Production Example (with config, logging, graceful shutdown)

```go
package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/joho/godotenv"
	"mybot/internal/bot"
	"mybot/internal/config"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	slog.SetDefault(logger)

	if err := godotenv.Load(); err != nil {
		slog.Info("no .env file, using environment variables")
	}

	cfg, err := config.Load()
	if err != nil {
		slog.Error("loading config", "error", err)
		os.Exit(1)
	}

	b, err := bot.New(cfg, logger)
	if err != nil {
		slog.Error("creating bot", "error", err)
		os.Exit(1)
	}

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	if err := b.Start(ctx); err != nil {
		slog.Error("starting bot", "error", err)
		os.Exit(1)
	}

	<-ctx.Done()
	slog.Info("shutdown signal received")
	b.Stop()
}
```

`signal.NotifyContext` (Go 1.16+) is cleaner than the manual channel pattern. `b.Start(ctx)` opens the session and registers commands. `b.Stop()` deregisters guild commands and closes the session.

## go.mod Setup

```bash
go mod init github.com/yourname/mybot
go get github.com/bwmarrin/discordgo@latest
go get github.com/joho/godotenv@latest
```

```
module github.com/yourname/mybot

go 1.22

require (
    github.com/bwmarrin/discordgo v0.28.1
    github.com/joho/godotenv v1.5.1
    github.com/spf13/viper v1.19.0       // optional: YAML config + hot-reload
    github.com/caarlos0/env/v11 v11.2.2  // optional: struct tag env parsing
)
```

Pin discordgo to a specific version in production. The library does not follow strict semver and breaking changes occasionally appear in minor releases.

## Configuration Management

### Environment Variables (os.Getenv, caarlos0/env)

For structured config with validation, use `caarlos0/env`:

```go
type Config struct {
    Token       string `env:"DISCORD_TOKEN,required"`
    GuildID     string `env:"DISCORD_GUILD_ID"`           // empty = global commands
    DatabaseURL string `env:"DATABASE_URL,required"`
    LogLevel    string `env:"LOG_LEVEL"    envDefault:"info"`
}

func Load() (*Config, error) {
    cfg := &Config{}
    if err := env.Parse(cfg); err != nil {
        return nil, fmt.Errorf("parsing config: %w", err)
    }
    return cfg, nil
}
```

The `required` tag causes `env.Parse` to return an error if the variable is unset, surfacing misconfiguration at startup.

### Viper Config (YAML + hot-reload pattern from ops-bot-iii)

ops-bot-iii uses Viper with fsnotify to reload configuration without restarting the bot — useful for feature flags and rate limits.

```go
viper.SetConfigName("config")
viper.SetConfigType("yaml")
viper.AddConfigPath(".")
viper.AutomaticEnv() // env vars override YAML values
viper.ReadInConfig()

viper.OnConfigChange(func(e fsnotify.Event) {
    slog.Info("config reloaded", "file", e.Name)
})
viper.WatchConfig()
```

### Config Struct Pattern

Expose configuration as a typed struct regardless of the loading mechanism:

```go
type Config struct {
    Discord  DiscordConfig
    Database DatabaseConfig
    Features FeatureFlags
}

type DiscordConfig struct {
    Token   string
    GuildID string // empty = global command registration
    AppID   string // populated from session after Open()
}
```

Pass `*Config` into the `Bot` struct constructor. Avoid global config variables — they make testing difficult and obscure dependencies.

## .env Handling (godotenv)

```bash
# .env — never commit this file
DISCORD_TOKEN=Bot_your_token_here
DISCORD_GUILD_ID=123456789012345678
DATABASE_URL=postgres://localhost/mybot_dev?sslmode=disable
LOG_LEVEL=debug
```

`godotenv.Load()` does not overwrite variables already set in the environment, so production deployments that inject secrets via the environment work without modification.

Commit a `.env.example` with placeholder values to document required variables.

## .gitignore Template

```gitignore
.env
*.env
config.local.yaml
/mybot
/bin/
*.test
*.out
.idea/
.vscode/
.DS_Store
```

## Bot Struct Pattern (dependency injection)

The `Bot` struct is the central dependency container. Inject all external dependencies through the constructor.

```go
type Bot struct {
    session  *discordgo.Session
    db       *database.DB
    cfg      *config.Config
    logger   *slog.Logger
    commands []*discordgo.ApplicationCommand // track for cleanup
}

func New(cfg *config.Config, db *database.DB, logger *slog.Logger) (*Bot, error) {
    s, err := discordgo.New("Bot " + cfg.Discord.Token)
    if err != nil {
        return nil, fmt.Errorf("creating session: %w", err)
    }
    s.Identify.Intents = discordgo.IntentsGuilds |
        discordgo.IntentsGuildMessages |
        discordgo.IntentsGuildMembers

    b := &Bot{session: s, db: db, cfg: cfg, logger: logger}
    b.session.AddHandler(b.onReady)
    b.session.AddHandler(b.onInteractionCreate)
    return b, nil
}

func (b *Bot) onInteractionCreate(s *discordgo.Session, i *discordgo.InteractionCreate) {
    switch i.Type {
    case discordgo.InteractionApplicationCommand:
        b.handleCommand(s, i)
    case discordgo.InteractionMessageComponent:
        b.handleComponent(s, i)
    case discordgo.InteractionModalSubmit:
        b.handleModal(s, i)
    }
}
```

Handler methods on `Bot` access all injected dependencies without global state.

## Command Registration Strategies

### Guild Commands (instant, for development)

Guild commands appear immediately and are only visible in the specified guild. Use during development to avoid propagation delay.

```go
registered, err := b.session.ApplicationCommandCreate(
    b.cfg.Discord.AppID,
    b.cfg.Discord.GuildID, // dev server ID
    cmd,
)
```

Delete guild commands on shutdown to keep the command list clean:

```go
func (b *Bot) deregisterCommands() {
    for _, cmd := range b.commands {
        b.session.ApplicationCommandDelete(b.cfg.Discord.AppID, b.cfg.Discord.GuildID, cmd.ID)
    }
}
```

### Global Commands (up to 1hr propagation, for production)

Pass an empty string as the guild ID for global registration:

```go
registered, err := b.session.ApplicationCommandCreate(b.cfg.Discord.AppID, "", cmd)
```

Discord caches global commands for up to one hour. Do not delete and re-register global commands on every restart — this wastes API quota and causes commands to disappear temporarily. Register global commands once during deployment, not at runtime.

Switch between guild and global registration via config: set `GuildID` to your dev server in development, leave it empty in production.

### ApplicationCommandBulkOverwrite (atomic, recommended)

`ApplicationCommandBulkOverwrite` replaces all commands in a single API call. It is atomic — the old set is replaced by the new set with no intermediate state. CJ bot uses this pattern for reliable deployments.

```go
func (b *Bot) registerCommands() error {
    registered, err := b.session.ApplicationCommandBulkOverwrite(
        b.cfg.Discord.AppID,
        b.cfg.Discord.GuildID, // empty for global
        commandDefinitions,
    )
    if err != nil {
        return fmt.Errorf("bulk registering commands: %w", err)
    }
    b.commands = registered
    b.logger.Info("commands registered", "count", len(registered))
    return nil
}
```

Prefer `BulkOverwrite` over individual `ApplicationCommandCreate` calls in all cases. It handles additions, updates, and deletions in one round trip and avoids partial registration failures.

For global commands in production, run `BulkOverwrite` once during deployment via a separate `cmd/register/main.go` binary rather than on every bot startup:

```go
// cmd/register/main.go — run once during deployment, not on every start
func main() {
    godotenv.Load()
    s, _ := discordgo.New("Bot " + os.Getenv("DISCORD_TOKEN"))
    s.Open()
    defer s.Close()

    registered, err := s.ApplicationCommandBulkOverwrite(s.State.User.ID, "", commands.Definitions)
    if err != nil {
        fmt.Fprintf(os.Stderr, "registering commands: %v\n", err)
        os.Exit(1)
    }
    fmt.Printf("registered %d commands\n", len(registered))
}
```
