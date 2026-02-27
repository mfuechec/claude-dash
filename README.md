# Claude Dash ⚡

A TUI dashboard for Claude Code setup — see your CLAUDE.md, MCP servers, and skills at a glance.

![Claude Dash Screenshot](docs/screenshot.png)

## The Problem

Claude Code's configuration is invisible during use. You're flying blind:
- "What MCP tools do I even have right now?"
- "Is my MCP server actually connected?"
- "What did I put in CLAUDE.md?"
- "What skills are available?"

## The Solution

A collapsible side panel that shows your entire Claude Code setup at a glance.

## Installation

```bash
# With pipx (recommended)
pipx install claude-dash

# Or with pip
pip install claude-dash
```

## Usage

```bash
# Run in current directory
claude-dash

# Run in specific workspace
claude-dash /path/to/project
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Tab` | Toggle sidebar |
| `e` | Edit CLAUDE.md in $EDITOR |
| `r` | Refresh configuration |
| `q` / `Esc` | Quit |

## iTerm Integration

For a persistent side panel in iTerm, add this to your shell config:

```bash
# ~/.zshrc or ~/.bashrc

# Launch claude-dash in a side pane
claude-pane() {
    # Open claude-dash in a right split
    osascript -e 'tell application "iTerm2"
        tell current session of current window
            split vertically with default profile
            tell last session of current tab of current window
                write text "claude-dash '"${1:-$(pwd)}"'"
            end tell
        end tell
    end tell'
}
```

Then use `claude-pane` to open a dashboard alongside your terminal.

## What It Shows

- **CLAUDE.md** — View and edit your main instructions file
- **MCP Servers** — All configured servers with their commands
- **Skills** — Available skills and their descriptions

## Configuration Detection

Claude Dash automatically finds configuration in these locations:

### CLAUDE.md
- `./CLAUDE.md`
- `./.claude/CLAUDE.md`

### MCP Config
- `./.claude/mcp.json`
- `./mcp.json`
- `./config/mcp.json`
- `~/.config/claude/mcp.json`

### Skills
- `./skills/`
- `./.claude/skills/`
- `/opt/clawdbot/skills/` (Clawdbot)

## Development

```bash
# Clone the repo
git clone https://github.com/mfuechec/claude-dash
cd claude-dash

# Install in development mode
pip install -e .

# Run
claude-dash
```

## License

MIT
