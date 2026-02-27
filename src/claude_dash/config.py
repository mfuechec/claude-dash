"""Configuration readers for Claude Code setup."""

import json
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MCPServer:
    """Represents an MCP server configuration."""
    name: str
    command: Optional[str] = None
    url: Optional[str] = None
    tools_count: Optional[int] = None
    status: str = "unknown"  # unknown, configured, error


@dataclass
class Skill:
    """Represents a skill."""
    name: str
    description: str = ""
    location: str = ""


@dataclass
class ClaudeConfig:
    """Complete Claude Code configuration."""
    workspace: Path
    claude_md_path: Optional[Path] = None
    claude_md_content: str = ""
    claude_md_exists: bool = False
    mcp_servers: list[MCPServer] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    mcp_config_path: Optional[Path] = None


def find_claude_md(workspace: Path) -> tuple[Optional[Path], str]:
    """Find and read CLAUDE.md in the workspace."""
    candidates = [
        workspace / "CLAUDE.md",
        workspace / ".claude" / "CLAUDE.md",
        workspace / "claude.md",
    ]
    
    for path in candidates:
        if path.exists():
            try:
                content = path.read_text()
                return path, content
            except Exception:
                return path, f"[Error reading {path}]"
    
    return None, ""


def find_mcp_config(workspace: Path) -> tuple[Optional[Path], list[MCPServer]]:
    """Find and parse MCP configuration."""
    candidates = [
        workspace / ".claude" / "mcp.json",
        workspace / "mcp.json",
        workspace / ".mcp.json",
        workspace / "config" / "mcp.json",
        workspace / "config" / "mcporter.json",
        Path.home() / ".config" / "claude" / "mcp.json",
        Path.home() / ".claude" / "mcp.json",
    ]
    
    servers = []
    config_path = None
    
    for path in candidates:
        if path.exists():
            config_path = path
            try:
                data = json.loads(path.read_text())
                # Handle different config formats
                mcp_servers = data.get("mcpServers", data.get("servers", {}))
                
                if isinstance(mcp_servers, dict):
                    for name, config in mcp_servers.items():
                        server = MCPServer(
                            name=name,
                            command=config.get("command"),
                            url=config.get("url"),
                            status="configured"
                        )
                        # Try to get args for display
                        if "args" in config:
                            server.command = f"{config.get('command', '')} {' '.join(config.get('args', []))}"
                        servers.append(server)
                break
            except Exception as e:
                servers.append(MCPServer(name=f"[Error: {e}]", status="error"))
                break
    
    return config_path, servers


def find_skills(workspace: Path) -> list[Skill]:
    """Find skills in common locations."""
    skills = []
    
    skill_dirs = [
        workspace / "skills",
        workspace / ".claude" / "skills",
        Path("/opt/clawdbot/skills"),  # Clawdbot skills
    ]
    
    for skill_dir in skill_dirs:
        if skill_dir.exists() and skill_dir.is_dir():
            for item in skill_dir.iterdir():
                if item.is_dir():
                    skill_md = item / "SKILL.md"
                    description = ""
                    if skill_md.exists():
                        try:
                            content = skill_md.read_text()
                            # Try to extract description from first paragraph
                            lines = content.split("\n")
                            for line in lines:
                                if line.strip() and not line.startswith("#"):
                                    description = line.strip()[:100]
                                    break
                        except Exception:
                            pass
                    
                    skills.append(Skill(
                        name=item.name,
                        description=description,
                        location=str(skill_md if skill_md.exists() else item)
                    ))
    
    return skills


def load_config(workspace: Optional[Path] = None) -> ClaudeConfig:
    """Load complete Claude Code configuration."""
    if workspace is None:
        workspace = Path.cwd()
    
    workspace = Path(workspace).resolve()
    
    claude_md_path, claude_md_content = find_claude_md(workspace)
    mcp_config_path, mcp_servers = find_mcp_config(workspace)
    skills = find_skills(workspace)
    
    return ClaudeConfig(
        workspace=workspace,
        claude_md_path=claude_md_path,
        claude_md_content=claude_md_content,
        claude_md_exists=claude_md_path is not None,
        mcp_servers=mcp_servers,
        skills=skills,
        mcp_config_path=mcp_config_path,
    )
