"""Claude Dash - TUI dashboard for Claude Code setup.

Designed to run in a narrow iTerm split pane (~30-40 chars wide).
"""

import os
import subprocess
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.widgets import Footer, Label, Static, Rule
from textual.binding import Binding
from textual.reactive import reactive

from .config import load_config, ClaudeConfig


class CompactView(Static):
    """Compact view showing icons and counts."""
    
    def __init__(self, config: ClaudeConfig, **kwargs):
        super().__init__(**kwargs)
        self.config = config
    
    def compose(self) -> ComposeResult:
        yield Static("⚡ [bold]Claude[/]", classes="header")
        yield Rule()
        
        # CLAUDE.md status
        if self.config.claude_md_exists:
            yield Static(f"📄 [green]✓[/] CLAUDE.md")
            # Show path relative to home if possible
            try:
                rel = self.config.claude_md_path.relative_to(Path.home())
                yield Static(f"   [dim]~/{rel}[/]", classes="subtext")
            except ValueError:
                yield Static(f"   [dim]{self.config.claude_md_path}[/]", classes="subtext")
        else:
            yield Static(f"📄 [red]✗[/] CLAUDE.md")
        
        yield Static("")
        
        # MCP servers
        yield Static(f"🔌 [bold]{len(self.config.mcp_servers)}[/] MCP servers")
        for server in self.config.mcp_servers[:5]:
            status = "[green]●[/]" if server.status == "configured" else "[yellow]○[/]"
            yield Static(f"   {status} {server.name}", classes="item")
        if len(self.config.mcp_servers) > 5:
            yield Static(f"   [dim]+{len(self.config.mcp_servers) - 5} more[/]", classes="subtext")
        
        yield Static("")
        
        # Skills
        yield Static(f"📚 [bold]{len(self.config.skills)}[/] skills")
        for skill in self.config.skills[:5]:
            yield Static(f"   • {skill.name}", classes="item")
        if len(self.config.skills) > 5:
            yield Static(f"   [dim]+{len(self.config.skills) - 5} more[/]", classes="subtext")


class ExpandedView(Static):
    """Expanded view showing full details."""
    
    def __init__(self, config: ClaudeConfig, **kwargs):
        super().__init__(**kwargs)
        self.config = config
    
    def compose(self) -> ComposeResult:
        yield Static("⚡ [bold]Claude Dash[/]", classes="header")
        yield Static(f"[dim]{self.config.workspace}[/]", classes="subtext")
        yield Rule()
        
        # CLAUDE.md section
        yield Static("[bold]CLAUDE.md[/]")
        if self.config.claude_md_exists:
            yield Static(f"[green]✓[/] {self.config.claude_md_path}")
            yield Static("")
            # Show first 20 lines
            lines = self.config.claude_md_content.split('\n')[:20]
            for line in lines:
                display_line = line[:60] + "..." if len(line) > 60 else line
                yield Static(f"[dim]{display_line}[/]")
            if len(self.config.claude_md_content.split('\n')) > 20:
                yield Static("[dim]...[/]")
        else:
            yield Static("[red]✗[/] Not found")
        
        yield Rule()
        
        # MCP servers section
        yield Static(f"[bold]MCP Servers ({len(self.config.mcp_servers)})[/]")
        if self.config.mcp_config_path:
            yield Static(f"[dim]{self.config.mcp_config_path}[/]", classes="subtext")
        yield Static("")
        for server in self.config.mcp_servers:
            status = "[green]●[/]" if server.status == "configured" else "[yellow]○[/]"
            yield Static(f"{status} [bold]{server.name}[/]")
            if server.command:
                cmd = server.command[:50] + "..." if len(server.command) > 50 else server.command
                yield Static(f"  [dim]{cmd}[/]")
        if not self.config.mcp_servers:
            yield Static("[dim]None configured[/]")
        
        yield Rule()
        
        # Skills section
        yield Static(f"[bold]Skills ({len(self.config.skills)})[/]")
        yield Static("")
        for skill in self.config.skills:
            yield Static(f"• [bold]{skill.name}[/]")
            if skill.description:
                desc = skill.description[:50] + "..." if len(skill.description) > 50 else skill.description
                yield Static(f"  [dim]{desc}[/]")
        if not self.config.skills:
            yield Static("[dim]None found[/]")


class ClaudeDash(App):
    """Narrow side-panel dashboard for Claude Code setup."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .header {
        text-align: center;
        padding: 1 0;
    }
    
    .subtext {
        color: $text-muted;
    }
    
    .item {
        padding: 0;
    }
    
    #main {
        padding: 1;
        height: 100%;
    }
    
    #scroll {
        height: 100%;
    }
    
    Rule {
        margin: 1 0;
        color: $primary-darken-2;
    }
    
    Footer {
        background: $surface-darken-1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        Binding("space", "toggle_view", "Expand"),
        Binding("e", "edit", "Edit"),
        Binding("r", "refresh", "Refresh"),
    ]
    
    expanded: reactive[bool] = reactive(False)
    
    def __init__(self, workspace: Path | None = None):
        super().__init__()
        self.workspace = workspace or Path.cwd()
        self.config = load_config(self.workspace)
    
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="scroll"):
            with Container(id="main"):
                if self.expanded:
                    yield ExpandedView(self.config, id="view")
                else:
                    yield CompactView(self.config, id="view")
        yield Footer()
    
    def watch_expanded(self, expanded: bool) -> None:
        """Rebuild view when expanded state changes."""
        try:
            container = self.query_one("#main", Container)
            container.remove_children()
            if expanded:
                container.mount(ExpandedView(self.config, id="view"))
            else:
                container.mount(CompactView(self.config, id="view"))
        except Exception:
            pass
    
    def action_toggle_view(self) -> None:
        """Toggle between compact and expanded view."""
        self.expanded = not self.expanded
    
    def action_edit(self) -> None:
        """Open CLAUDE.md in editor."""
        if self.config.claude_md_path:
            editor = os.environ.get("EDITOR", "vim")
            self.exit()
            subprocess.run([editor, str(self.config.claude_md_path)])
    
    def action_refresh(self) -> None:
        """Reload configuration."""
        self.config = load_config(self.workspace)
        self.expanded = self.expanded  # Trigger rebuild
        self.notify("Refreshed")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Claude Code setup dashboard (designed for narrow side pane)"
    )
    parser.add_argument(
        "workspace",
        nargs="?",
        default=None,
        help="Workspace directory (default: current directory)"
    )
    parser.add_argument(
        "-e", "--expanded",
        action="store_true",
        help="Start in expanded mode"
    )
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace) if args.workspace else None
    app = ClaudeDash(workspace=workspace)
    if args.expanded:
        app.expanded = True
    app.run()


if __name__ == "__main__":
    main()
