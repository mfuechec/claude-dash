"""Claude Dash - TUI dashboard for Claude Code setup."""

import os
import subprocess
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Collapsible,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    Markdown,
    Static,
    Tree,
)
from textual.binding import Binding
from textual.reactive import reactive

from .config import load_config, ClaudeConfig, MCPServer, Skill


class StatusIndicator(Static):
    """A small status indicator."""
    
    def __init__(self, status: str = "ok", label: str = "", **kwargs):
        super().__init__(**kwargs)
        self.status = status
        self.label_text = label
    
    def compose(self) -> ComposeResult:
        icon = "●" if self.status == "ok" else "○" if self.status == "unknown" else "✗"
        color = "green" if self.status == "ok" else "yellow" if self.status == "unknown" else "red"
        yield Static(f"[{color}]{icon}[/] {self.label_text}")


class CompactPanel(Static):
    """Compact view shown when sidebar is collapsed."""
    
    def __init__(self, config: ClaudeConfig, **kwargs):
        super().__init__(**kwargs)
        self.config = config
    
    def compose(self) -> ComposeResult:
        yield Static("⚡", classes="compact-icon")
        yield Static(f"[dim]M:[/]{len(self.config.mcp_servers)}", classes="compact-stat")
        yield Static(f"[dim]S:[/]{len(self.config.skills)}", classes="compact-stat")


class MCPServerItem(Static):
    """Display for a single MCP server."""
    
    def __init__(self, server: MCPServer, **kwargs):
        super().__init__(**kwargs)
        self.server = server
    
    def compose(self) -> ComposeResult:
        status_icon = "●" if self.server.status == "configured" else "○"
        status_color = "green" if self.server.status == "configured" else "yellow"
        yield Static(
            f"[{status_color}]{status_icon}[/] [bold]{self.server.name}[/]"
        )
        if self.server.command:
            cmd_display = self.server.command[:50] + "..." if len(self.server.command) > 50 else self.server.command
            yield Static(f"  [dim]{cmd_display}[/]")


class SkillItem(Static):
    """Display for a single skill."""
    
    def __init__(self, skill: Skill, **kwargs):
        super().__init__(**kwargs)
        self.skill = skill
    
    def compose(self) -> ComposeResult:
        yield Static(f"📚 [bold]{self.skill.name}[/]")
        if self.skill.description:
            desc = self.skill.description[:60] + "..." if len(self.skill.description) > 60 else self.skill.description
            yield Static(f"  [dim]{desc}[/]")


class DetailPanel(Static):
    """Main detail panel showing selected item."""
    
    content: reactive[str] = reactive("")
    
    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Markdown(self.content, id="detail-content"),
            id="detail-scroll"
        )
    
    def watch_content(self, new_content: str) -> None:
        try:
            md = self.query_one("#detail-content", Markdown)
            md.update(new_content)
        except Exception:
            pass


class SidePanel(Static):
    """Collapsible side panel with config overview."""
    
    expanded: reactive[bool] = reactive(True)
    
    def __init__(self, config: ClaudeConfig, **kwargs):
        super().__init__(**kwargs)
        self.config = config
    
    def compose(self) -> ComposeResult:
        with Vertical(id="side-content"):
            # Header
            yield Static("⚡ [bold]Claude Dash[/]", id="side-header")
            yield Static(f"[dim]{self.config.workspace.name}[/]", id="workspace-name")
            yield Static("─" * 20, classes="separator")
            
            # CLAUDE.md section
            with Collapsible(title="CLAUDE.md", collapsed=False):
                if self.config.claude_md_exists:
                    yield Button("📄 View CLAUDE.md", id="btn-claude-md", variant="default")
                else:
                    yield Static("[dim]Not found[/]")
            
            # MCP Servers section
            with Collapsible(title=f"MCP Servers ({len(self.config.mcp_servers)})", collapsed=False):
                if self.config.mcp_servers:
                    for server in self.config.mcp_servers:
                        yield MCPServerItem(server, classes="mcp-item")
                else:
                    yield Static("[dim]None configured[/]")
            
            # Skills section
            with Collapsible(title=f"Skills ({len(self.config.skills)})", collapsed=True):
                if self.config.skills:
                    for skill in self.config.skills[:10]:  # Limit display
                        yield SkillItem(skill, classes="skill-item")
                    if len(self.config.skills) > 10:
                        yield Static(f"[dim]... and {len(self.config.skills) - 10} more[/]")
                else:
                    yield Static("[dim]None found[/]")


class ClaudeDash(App):
    """Main Claude Dash application."""
    
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    #side-panel {
        width: 35;
        min-width: 20;
        max-width: 50;
        height: 100%;
        background: $surface;
        border-right: solid $primary;
        padding: 1;
    }
    
    #side-panel.collapsed {
        width: 6;
        min-width: 6;
    }
    
    #side-header {
        text-align: center;
        padding-bottom: 1;
    }
    
    #workspace-name {
        text-align: center;
        padding-bottom: 1;
    }
    
    .separator {
        color: $primary-darken-2;
        text-align: center;
    }
    
    #main-panel {
        width: 1fr;
        height: 100%;
        padding: 1;
    }
    
    #detail-scroll {
        height: 100%;
        border: solid $primary-darken-2;
        padding: 1;
    }
    
    .mcp-item {
        padding: 0 0 1 0;
    }
    
    .skill-item {
        padding: 0 0 1 0;
    }
    
    Collapsible {
        padding: 0;
        margin: 0 0 1 0;
    }
    
    CollapsibleTitle {
        padding: 0;
    }
    
    Button {
        width: 100%;
        margin: 0;
    }
    
    #compact-panel {
        width: 4;
        padding: 1 0;
    }
    
    .compact-icon {
        text-align: center;
        padding-bottom: 1;
    }
    
    .compact-stat {
        text-align: center;
    }
    
    Footer {
        background: $surface;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        Binding("tab", "toggle_sidebar", "Toggle Sidebar"),
        Binding("e", "edit_claude_md", "Edit CLAUDE.md"),
        Binding("r", "refresh", "Refresh"),
        Binding("?", "help", "Help"),
    ]
    
    sidebar_visible: reactive[bool] = reactive(True)
    
    def __init__(self, workspace: Path | None = None):
        super().__init__()
        self.workspace = workspace or Path.cwd()
        self.config = load_config(self.workspace)
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal():
            yield SidePanel(self.config, id="side-panel")
            yield DetailPanel(id="main-panel")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Show CLAUDE.md content on start if it exists."""
        if self.config.claude_md_exists:
            self.show_claude_md()
        else:
            self.show_welcome()
    
    def show_claude_md(self) -> None:
        """Display CLAUDE.md content in detail panel."""
        detail = self.query_one("#main-panel", DetailPanel)
        detail.content = self.config.claude_md_content
    
    def show_welcome(self) -> None:
        """Show welcome/help message."""
        detail = self.query_one("#main-panel", DetailPanel)
        detail.content = f"""# Claude Dash

Welcome to your Claude Code setup dashboard.

## Workspace
`{self.config.workspace}`

## Status
- **CLAUDE.md**: {"✅ Found" if self.config.claude_md_exists else "❌ Not found"}
- **MCP Servers**: {len(self.config.mcp_servers)} configured
- **Skills**: {len(self.config.skills)} available

## Keyboard Shortcuts
- `Tab` - Toggle sidebar
- `e` - Edit CLAUDE.md in $EDITOR
- `r` - Refresh configuration
- `q` or `Esc` - Quit
"""
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-claude-md":
            self.show_claude_md()
    
    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar width."""
        panel = self.query_one("#side-panel")
        panel.toggle_class("collapsed")
    
    def action_edit_claude_md(self) -> None:
        """Open CLAUDE.md in editor."""
        if self.config.claude_md_path:
            editor = os.environ.get("EDITOR", "vim")
            self.exit()
            subprocess.run([editor, str(self.config.claude_md_path)])
    
    def action_refresh(self) -> None:
        """Reload configuration."""
        self.config = load_config(self.workspace)
        self.notify("Configuration refreshed")
        # Refresh display
        if self.config.claude_md_exists:
            self.show_claude_md()
        else:
            self.show_welcome()
    
    def action_help(self) -> None:
        """Show help."""
        self.show_welcome()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Code setup dashboard")
    parser.add_argument(
        "workspace",
        nargs="?",
        default=None,
        help="Workspace directory (default: current directory)"
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Start in compact mode"
    )
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace) if args.workspace else None
    app = ClaudeDash(workspace=workspace)
    app.run()


if __name__ == "__main__":
    main()
