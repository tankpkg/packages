# Shell Integration and Features

Sources: ghostty.org/docs/features/shell-integration, ghostty.org/docs/config/reference

## Shell Integration Overview

Shell integration hooks into the shell's prompt system to give Ghostty semantic awareness
of the terminal session. It enables prompt jumping, smart cursor behavior, CWD tracking,
command output selection, and more.

Ghostty auto-injects shell integration for bash, zsh, fish, and elvish. No manual setup
needed for these shells in most configurations.

## Auto-Injection

Ghostty detects the shell from the binary basename. Works automatically for:
- `zsh` (including Homebrew installs)
- `bash` (not the macOS system bash at `/bin/bash` — see caveat below)
- `fish`
- `elvish`

Force a specific shell integration if the binary has a different name:
```ini
shell-integration = fish          # force fish integration regardless of binary name
shell-integration = none          # disable shell integration entirely
```

### macOS System Bash Caveat

`/bin/bash` on macOS is an old Bash version that does not support auto-injection. Options:
1. Install a modern bash via Homebrew and set it as your shell
2. Manually source the integration (see below)
3. Use zsh, fish, or elvish instead

## Manual Shell Integration Setup

Source the integration script at the top of your shell rc file.
`GHOSTTY_RESOURCES_DIR` is set automatically when running inside Ghostty.

**bash** (top of `~/.bashrc`):
```bash
if [ -n "${GHOSTTY_RESOURCES_DIR}" ]; then
    builtin source "${GHOSTTY_RESOURCES_DIR}/shell-integration/bash/ghostty.bash"
fi
```

**zsh** (top of `~/.zshrc`):
```zsh
if [[ -n "${GHOSTTY_RESOURCES_DIR}" ]]; then
    source "${GHOSTTY_RESOURCES_DIR}/shell-integration/zsh/ghostty-integration"
fi
```

**fish** (in `~/.config/fish/conf.d/`):
```fish
if set -q GHOSTTY_RESOURCES_DIR
    source "$GHOSTTY_RESOURCES_DIR/shell-integration/fish/vendor_conf.d/ghostty-shell-integration.fish"
end
```

**elvish** (in `~/.config/elvish/rc.elv`):
```elvish
if (not-eq $E:GHOSTTY_RESOURCES_DIR '') {
    use "$E:GHOSTTY_RESOURCES_DIR/shell-integration/elvish/lib/ghostty-integration"
}
```

## Shell Integration Features

| Feature | Required | Description |
|---|---|---|
| Prompt marks | OSC 133 | Enables jump_to_prompt and output selection |
| Cursor bar at prompt | Prompt marks | Shows bar cursor when editing, block when running |
| Alt+click to move cursor | Prompt marks | Click to position cursor in prompt |
| Smart close | Prompt marks | No confirmation when no process is running |
| New terminal in same CWD | Prompt marks + CWD reporting | New splits/windows start in current directory |
| Prompt resize/reflow | Shell integration | Prompts redraw correctly when terminal resizes |
| Command output selection | Prompt marks | Triple-click with Cmd (macOS) or Ctrl (Linux) |

### Enabling/Disabling Specific Features

```ini
shell-integration-features = cursor,title,sudo,ssh
shell-integration-features = no-cursor              # disable cursor bar, keep rest
shell-integration-features = no-sudo,no-ssh         # disable wrapping features
```

Available features: `cursor`, `title`, `sudo`, `ssh`

## SSH and sudo Wrapping

Shell integration can automatically handle two common sources of $TERM breakage.

### SSH Wrapping

```ini
shell-integration-features = ssh     # enable SSH wrapping
```

When enabled, SSH is wrapped to either:
1. Transmit the Ghostty terminfo to the remote host (when supported)
2. Set `TERM=xterm-256color` as a fallback

This prevents the "unknown terminal type" error on remote hosts that don't have
the `ghostty` terminfo installed.

Manual workaround without SSH wrapping:
```sh
# On local machine: copy terminfo to remote
infocmp -x | ssh remote-host -- tic -x -
# Or simpler:
TERM=xterm-256color ssh remote-host
```

### sudo Wrapping

```ini
shell-integration-features = sudo    # preserve terminfo across sudo
```

Without this, `sudo vim` can fail because root's env doesn't have the ghostty terminfo.

## Environment Variables

Ghostty sets these in all child processes:

| Variable | Value | Use |
|---|---|---|
| `GHOSTTY_RESOURCES_DIR` | Path to Ghostty resources | Manual shell integration sourcing |
| `GHOSTTY_BIN_DIR` | Directory of ghostty binary | Added to PATH since 1.2.1 |
| `TERM` | `ghostty` | Terminal type (unless overridden with `term =`) |
| `TERM_PROGRAM` | `ghostty` | Terminal identification |
| `COLORTERM` | `truecolor` | True color capability advertisement |

## $TERM and Terminfo

Ghostty uses `TERM=ghostty` by default. The `ghostty` terminfo entry declares full
capability support. If remote hosts or tools complain about an unknown terminal:

```ini
# Fallback to widely-supported value
term = xterm-256color
```

Or selectively for SSH sessions using SSH wrapping.

Verify Ghostty terminfo is available locally:
```sh
toe -a | grep ghostty        # should show ghostty terminfo
infocmp ghostty | head -5    # show ghostty capabilities
```

## Splits, Tabs, and Windows

Ghostty has native tabs, splits, and multiple windows. No tmux required for basic use.

### Tab Configuration

```ini
window-new-tab-position = end          # end | current+1
tab-title-template = "{{title}} [{{id}}]"
```

### Split Behavior

New splits inherit the CWD of the parent split (requires shell integration).

```ini
focus-follows-mouse = true      # auto-focus split under cursor
```

### Viewing Splits

The `inspector` action opens a built-in terminal inspector showing escape sequences,
rendering cells, and configuration. Useful for debugging display issues.

```ini
keybind = super+alt+i=inspector:toggle
```

## Scrollback Search (since 1.3.0)

In-buffer search with highlights and navigation:

```ini
# Default binds (can be customized)
# macOS: cmd+f = start search, cmd+g = next, shift+cmd+g = prev
# GTK:   ctrl+shift+f = start search, enter = next, shift+enter = prev
```

Searching runs in a background thread — stays responsive in large scrollbacks.

## Undo/Redo (macOS)

Ghostty supports undo/redo for terminal structure changes (not terminal content):

```ini
keybind = super+z=undo
keybind = super+shift+z=redo
undo-timeout = 10      # seconds before action expires (default varies)
```

Actions that can be undone: close/reopen window, close/reopen tab, close/reopen split.

## Verify Shell Integration Is Active

In a Ghostty terminal:
```sh
echo $GHOSTTY_RESOURCES_DIR    # should print a path
echo $TERM                      # should be "ghostty"
```

Check Ghostty logs on startup for:
```
info(io_exec): shell integration automatically injected shell=...fish
```

If you see this, shell integration is broken:
```
ghostty terminfo not found, using xterm-256color
shell could not be detected, no automatic shell integration will be injected
```

## Command Completion Notifications

```ini
notify-on-command-finish = 30    # notify when command takes > 30 seconds
notify-on-command-finish = 0     # disable (default)
```

Ghostty sends a system notification when a command running in the background finishes.
Requires shell integration (prompt marks). Only triggers when Ghostty is not focused.

Useful for: long builds, npm/pip installs, test runs, file transfers.

## OSC Sequences Used by Shell Integration

Shell integration uses standard OSC sequences. Relevant if debugging integration:

| Sequence | Purpose |
|---|---|
| OSC 133 A | Prompt start mark |
| OSC 133 B | Prompt end / command start mark |
| OSC 133 C | Command output start |
| OSC 133 D | Command finish (with exit code) |
| OSC 7 | CWD notification (`file://host/path`) |
| OSC 2 | Window title |
| OSC 9 | Desktop notification |

## Switching Shells Within Ghostty

Auto-injection only applies to the initially launched shell. If you run `bash` inside
a `zsh` session, bash loses integration. Fix by adding the manual source snippet to
`~/.bashrc` (and other shells you switch into).
