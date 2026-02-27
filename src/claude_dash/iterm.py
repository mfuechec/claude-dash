"""iTerm integration for Claude Dash.

Automatically opens claude-dash in a narrow side pane.
"""

import subprocess
import sys
from pathlib import Path


APPLESCRIPT_SPLIT_RIGHT = '''
tell application "iTerm2"
    tell current session of current window
        set newSession to (split vertically with default profile)
        tell newSession
            write text "claude-dash {workspace}"
        end tell
    end tell
    
    -- Resize the new pane to be narrow (about 35 columns)
    tell current window
        tell current tab
            set width of current session to 100
        end tell
    end tell
end tell
'''

APPLESCRIPT_SPLIT_LEFT = '''
tell application "iTerm2"
    tell current session of current window
        set newSession to (split vertically with default profile)
    end tell
    
    -- The original session is now on the right, new on left
    -- Switch to new session and run claude-dash
    tell current session of current window
        write text "claude-dash {workspace}"
    end tell
end tell
'''


def open_side_pane(workspace: str = "", side: str = "right"):
    """Open claude-dash in a side pane in iTerm."""
    
    script = APPLESCRIPT_SPLIT_RIGHT if side == "right" else APPLESCRIPT_SPLIT_LEFT
    script = script.replace("{workspace}", workspace or "")
    
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True
        )
    except FileNotFoundError:
        print("Error: osascript not found. This feature only works on macOS with iTerm2.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to create iTerm split pane")
        print(f"  {e.stderr.decode() if e.stderr else 'Unknown error'}")
        print("\nMake sure iTerm2 is running and has 'Allow Python API' enabled in preferences.")
        sys.exit(1)


def main():
    """Entry point for claude-pane command."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Open claude-dash in a narrow iTerm side pane"
    )
    parser.add_argument(
        "workspace",
        nargs="?",
        default="",
        help="Workspace directory (default: current directory)"
    )
    parser.add_argument(
        "--left",
        action="store_true",
        help="Open pane on the left instead of right"
    )
    
    args = parser.parse_args()
    
    side = "left" if args.left else "right"
    open_side_pane(args.workspace, side)


if __name__ == "__main__":
    main()
